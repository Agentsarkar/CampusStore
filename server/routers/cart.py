from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/cart", tags=["cart"])

# Pydantic Schemas
class AddToCartSchema(BaseModel):
    productId: str

class UpdateCartQtySchema(BaseModel):
    id: str
    qty: int

class DeleteCartItemSchema(BaseModel):
    id: str

# Helper to map Supabase cart item to React style
def map_cart_item(item: dict) -> dict:
    prod_data = None
    if item.get("products"):
        prod_data = {
            "_id": item["products"]["id"],
            "name": item["products"]["name"],
            "image": item["products"]["image"] or [],
            "price": float(item["products"]["price"]) if item["products"]["price"] is not None else 0.0,
            "discount": float(item["products"]["discount"]) if item["products"]["discount"] is not None else 0.0,
            "category_id": item["products"].get("category_id")
        }
    return {
        "_id": item["id"],
        "productId": prod_data,
        "quantity": item["quantity"]
    }

# Endpoints
@router.post("/create")
async def add_to_cart(data: AddToCartSchema, current_user_id: str = Depends(get_current_user_id)):
    # Check if product is already in cart
    existing = supabase.table("cart_items").select("*").eq("user_id", current_user_id).eq("product_id", data.productId).execute()
    if existing.data:
        # Increment quantity
        new_qty = existing.data[0]["quantity"] + 1
        update_res = supabase.table("cart_items").update({"quantity": new_qty}).eq("id", existing.data[0]["id"]).execute()
        if not update_res.data:
            raise HTTPException(status_code=500, detail="Failed to update cart quantity")
            
        return {
            "message": "Item added to cart",
            "error": False,
            "success": True,
            "data": map_cart_item(update_res.data[0])
        }
    
    # Insert new cart item
    insert_res = supabase.table("cart_items").insert({
        "user_id": current_user_id,
        "product_id": data.productId,
        "quantity": 1
    }).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to add item to cart")
        
    return {
        "message": "Item added to cart",
        "error": False,
        "success": True,
        "data": insert_res.data[0]
    }

@router.get("/get")
async def get_cart(current_user_id: str = Depends(get_current_user_id)):
    # Select cart items with populated products
    response = supabase.table("cart_items").select("*, products(*)").eq("user_id", current_user_id).execute()
    mapped_data = [map_cart_item(item) for item in response.data or [] if item.get("products") is not None]
    
    return {
        "message": "Cart items fetched successfully",
        "error": False,
        "success": True,
        "data": mapped_data
    }

@router.put("/update-qty")
async def update_cart_qty(data: UpdateCartQtySchema, current_user_id: str = Depends(get_current_user_id)):
    if data.qty <= 0:
        # Delete if quantity is 0 or less
        supabase.table("cart_items").delete().eq("id", data.id).eq("user_id", current_user_id).execute()
        return {
            "message": "Item removed from cart",
            "error": False,
            "success": True
        }
        
    response = supabase.table("cart_items").update({"quantity": data.qty}).eq("id", data.id).eq("user_id", current_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update cart quantity")
        
    return {
        "message": "Cart updated",
        "error": False,
        "success": True,
        "data": response.data[0]
    }

@router.delete("/delete-cart-item")
async def delete_cart_item(data: DeleteCartItemSchema, current_user_id: str = Depends(get_current_user_id)):
    supabase.table("cart_items").delete().eq("id", data.id).eq("user_id", current_user_id).execute()
        
    return {
        "message": "Item removed from cart",
        "error": False,
        "success": True
    }
