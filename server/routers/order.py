import uuid
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Any
from config import supabase
from utils.auth import get_current_user_id
from utils.razorpay_client import razorpay_client
import razorpay

router = APIRouter(prefix="/api/order", tags=["order"])

# Pydantic Schemas
class OrderProductDetails(BaseModel):
    name: str
    image: List[str]

class CartItemDetail(BaseModel):
    productId: Any  # Can be product object or dict
    quantity: int

class CreateOrderSchema(BaseModel):
    list_items: List[CartItemDetail]
    totalAmt: float
    addressId: str
    subTotalAmt: float
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

# Helper to map Supabase order to React style
def map_order(item: dict) -> dict:
    return {
        "_id": item.get("id"),
        "id": item.get("id"),
        "orderId": item.get("order_id"),
        "order_id": item.get("order_id"),
        "order_number": item.get("order_id"),
        "order_status": item.get("delivery_status", "PENDING"),
        "product_details": item.get("product_details", []),
        "totalAmt": float(item.get("total_amt", 0)),
        "payment_status": item.get("payment_status"),
        "delivery_address": item.get("delivery_address"),
        "store_name": item.get("store_name"),
        "store_address": item.get("store_address"),
        "createdAt": item.get("created_at")
    }

# Endpoints
@router.post("/cash-on-delivery")
@router.post("/checkout") # Fallback to support both checkout endpoints
async def create_order(data: CreateOrderSchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify Razorpay signature
    try:
        if not razorpay_client:
            raise Exception("Razorpay not configured")
            
        razorpay_client.utility.verify_payment_signature({
            'razorpay_order_id': data.razorpay_order_id,
            'razorpay_payment_id': data.razorpay_payment_id,
            'razorpay_signature': data.razorpay_signature
        })
    except razorpay.errors.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid payment signature")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Payment verification failed: {str(e)}")

    # 0. Check if any delivery partners are online
    riders_res = supabase.table("riders").select("id").eq("is_online", True).execute()
    if not riders_res.data or len(riders_res.data) == 0:
        raise HTTPException(status_code=400, detail="No delivery partners are currently available. Please try again later.")

    # 1. Fetch the delivery address
    addr_res = supabase.table("addresses").select("*").eq("id", data.addressId).execute()
    if not addr_res.data:
        raise HTTPException(status_code=400, detail="Delivery address not found")
        
    addr = addr_res.data[0]
    delivery_address_str = f"Room {addr['room_number']}, {addr['building_name']}, {addr['branch']}"
    
    # 2. Extract item details & Validate Stock
    formatted_details = []
    stock_updates = []
    store_name = ""
    store_address = ""
    
    for item in data.list_items:
        prod = item.productId
        prod_id = None
        # Handle case where productId is a dict or string ID
        if isinstance(prod, dict):
            name = prod.get("name", "Unknown Product")
            image = prod.get("image", [])
            price = prod.get("price", 0.0)
            if "_id" in prod:
                prod_id = prod["_id"]
        else:
            prod_id = str(prod)
            # Fallback query if product is just an ID string
            p_res = supabase.table("products").select("name", "image", "price").eq("id", prod_id).execute()
            if p_res.data:
                name = p_res.data[0]["name"]
                image = p_res.data[0]["image"]
                price = p_res.data[0]["price"]
            else:
                name = "Unknown Product"
                image = []
                price = 0.0
                
        # Validate stock
        if prod_id:
            stock_res = supabase.table("products").select("stock", "name", "category_id").eq("id", prod_id).execute()
            if stock_res.data:
                db_item = stock_res.data[0]
                stock = db_item["stock"]
                name = db_item["name"]
                
                # Capture outlet info from the first item
                if not store_name and db_item.get("category_id"):
                    cat_res = supabase.table("categories").select("name", "address").eq("id", db_item["category_id"]).execute()
                    if cat_res.data:
                        store_name = cat_res.data[0]["name"]
                        store_address = cat_res.data[0].get("address") or "Campus Outlet"

                if stock < item.quantity:
                    raise HTTPException(status_code=400, detail=f"Insufficient stock for {name}")
                
                stock_updates.append({"id": prod_id, "new_stock": stock - item.quantity})
                
        formatted_details.append({
            "name": name,
            "image": image,
            "quantity": item.quantity,
            "price": price
        })
        
    if not store_name:
        store_name = "Campus Canteen"
        store_address = "Campus Outlet"
        
    # Deduct stock after all validations pass
    for update in stock_updates:
        supabase.table("products").update({"stock": update["new_stock"]}).eq("id", update["id"]).execute()
        
    # 3. Create the order
    order_id_str = f"ORD-{str(uuid.uuid4())[:8].upper()}"
    import random
    otp = str(random.randint(100000, 999999))
    
    order_payload = {
        "order_id": order_id_str,
        "user_id": current_user_id,
        "product_details": formatted_details,
        "total_amt": data.totalAmt,
        "payment_status": "PAID",
        "delivery_address": delivery_address_str,
        "delivery_status": "PENDING",
        "store_name": store_name,
        "store_address": store_address,
        "delivery_otp": otp
    }
    
    order_res = supabase.table("orders").insert(order_payload).execute()
    if not order_res.data:
        raise HTTPException(status_code=500, detail="Failed to create order")
        
    # 4. Clear the cart
    supabase.table("cart_items").delete().eq("user_id", current_user_id).execute()
    
    return {
        "message": "Order placed successfully",
        "error": False,
        "success": True,
        "data": [map_order(order_res.data[0])]
    }

@router.get("/order-list")
async def get_orders(current_user_id: str = Depends(get_current_user_id)):
    response = supabase.table("orders").select("*").eq("user_id", current_user_id).order("created_at", desc=True).execute()
    mapped_data = [map_order(item) for item in response.data or []]
    
    return {
        "message": "order list",
        "data": mapped_data,
        "error": False,
        "success": True
    }

@router.get("/status/{order_id}")
async def get_order_status(order_id: str, current_user_id: str = Depends(get_current_user_id)):
    # 1. Search food orders table
    try:
        if len(order_id) > 20:
            response = supabase.table("orders").select("delivery_status, rider_id, store_name, delivery_otp").eq("id", order_id).eq("user_id", current_user_id).execute()
        else:
            response = supabase.table("orders").select("delivery_status, rider_id, store_name, delivery_otp").eq("order_id", order_id).eq("user_id", current_user_id).execute()
        
        if response.data and len(response.data) > 0:
            order_data = response.data[0]
            rider_info = None
            if order_data.get("rider_id"):
                rider_res = supabase.table("riders").select("name, phone").eq("id", order_data["rider_id"]).execute()
                if rider_res.data:
                    rider_info = {
                        "full_name": rider_res.data[0]["name"],
                        "phone_number": rider_res.data[0]["phone"]
                    }
            return {
                "success": True,
                "data": {
                    "status": order_data.get("delivery_status"),
                    "store_name": order_data.get("store_name", "Campus Canteen"),
                    "rider": rider_info,
                    "otp": order_data.get("delivery_otp")
                }
            }
    except Exception:
        pass

    # 2. Search Print Orders (memory cache first)
    try:
        from routers.print import IN_MEMORY_PRINT_ORDERS
        for print_item in IN_MEMORY_PRINT_ORDERS:
            if print_item.get("id") == order_id or print_item.get("order_id") == order_id:
                raw_status = print_item.get("delivery_status", "PENDING")
                return {
                    "success": True,
                    "data": {
                        "status": "PRINTING_IN_PROGRESS" if raw_status == "PENDING" else raw_status,
                        "store_name": "Campus Print Express",
                        "rider": None,
                        "otp": print_item.get("delivery_otp")
                    }
                }
    except Exception:
        pass

    # 3. Search Print Orders DB table
    try:
        if len(order_id) > 20:
            prt_res = supabase.table("print_orders").select("delivery_status, delivery_otp").eq("id", order_id).execute()
        else:
            prt_res = supabase.table("print_orders").select("delivery_status, delivery_otp").eq("order_id", order_id).execute()
        
        if prt_res.data and len(prt_res.data) > 0:
            raw_status = prt_res.data[0].get("delivery_status", "PENDING")
            return {
                "success": True,
                "data": {
                    "status": "PRINTING_IN_PROGRESS" if raw_status == "PENDING" else raw_status,
                    "store_name": "Campus Print Express",
                    "rider": None,
                    "otp": prt_res.data[0].get("delivery_otp")
                }
            }
    except Exception:
        pass

    raise HTTPException(status_code=404, detail="Order not found")
