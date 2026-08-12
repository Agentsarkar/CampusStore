from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Any
from config import supabase
from utils.auth import get_current_user_id
from utils.razorpay_client import razorpay_client
import razorpay

router = APIRouter(prefix="/api/canteen", tags=["canteen"])

# -------------------------------------------------------
# Pydantic Schemas
# -------------------------------------------------------
class CanteenCartAddSchema(BaseModel):
    product_id: str
    outlet_category_id: str
    quantity: Optional[int] = 1

class CanteenCartUpdateSchema(BaseModel):
    id: str
    qty: int

class CanteenCartDeleteSchema(BaseModel):
    id: str

class CanteenCheckoutSchema(BaseModel):
    outlet_category_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str

class MarkTokenDoneSchema(BaseModel):
    token_id: str

class NotifyNextSchema(BaseModel):
    outlet_category_id: str
    current_offset: int  # The offset BEFORE advancing (e.g., 0 means we've been on 1-10, clicking next moves to 11-20)

class NotifyAgainSchema(BaseModel):
    outlet_category_id: str
    current_offset: int  # The CURRENT already-applied offset (e.g., 10 means we ARE serving 11-20, re-notify same batch)

class NotifyPrevSchema(BaseModel):
    outlet_category_id: str
    current_offset: int  # The offset BEFORE going backward

# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def map_token(t: dict) -> dict:
    return {
        "_id": t["id"],
        "token_number": t["token_number"],
        "outlet_category_id": t["outlet_category_id"],
        "user_id": t["user_id"],
        "product_details": t["product_details"],
        "total_amt": float(t["total_amt"]),
        "status": t["status"],
        "notify_batch": t.get("notify_batch", 0),
        "created_at": t["created_at"]
    }

def map_cart_item(item: dict) -> dict:
    prod_data = None
    if item.get("products"):
        prod_data = {
            "_id": item["products"]["id"],
            "name": item["products"]["name"],
            "image": item["products"]["image"] or [],
            "price": float(item["products"]["price"]) if item["products"]["price"] is not None else 0.0,
            "discount": float(item["products"]["discount"]) if item["products"]["discount"] is not None else 0.0,
            "food_type": item["products"].get("food_type"),
            "prep_time": item["products"].get("prep_time", "8 mins"),
            "section": item["products"].get("section", "canteen"),
        }
    return {
        "_id": item["id"],
        "productId": prod_data,
        "quantity": item["quantity"],
        "outlet_category_id": item["outlet_category_id"]
    }

def require_canteen_auth(current_user_id: str, role: str = None):
    """Checks that the user is ADMIN or CANTEEN_OP."""
    user_res = supabase.table("users").select("role, outlet_category_id").eq("id", current_user_id).execute()
    if not user_res.data:
        raise HTTPException(status_code=403, detail="User not found")
    user = user_res.data[0]
    if user["role"] not in ["ADMIN", "CANTEEN_OP"]:
        raise HTTPException(status_code=403, detail="Canteen operator or admin access required")
    return user

# -------------------------------------------------------
# 1. Outlets (canteen categories)
# -------------------------------------------------------
@router.get("/outlets")
async def get_outlets():
    """Return all categories tagged as 'canteen' section."""
    res = supabase.table("categories").select("*").eq("section", "canteen").execute()
    outlets = []
    for item in res.data or []:
        item["_id"] = item["id"]
        outlets.append(item)
    return {
        "message": "Canteen outlets fetched",
        "data": outlets,
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 2. Canteen Products by Outlet
# -------------------------------------------------------
@router.get("/menu/{outlet_category_id}")
async def get_canteen_menu(outlet_category_id: str):
    """Get all canteen products for a specific outlet."""
    res = supabase.table("products").select("*, categories(*)") \
        .eq("category_id", outlet_category_id) \
        .eq("section", "canteen") \
        .eq("publish", True) \
        .execute()
    
    products = []
    for p in res.data or []:
        cat_info = []
        if p.get("categories"):
            cat_info = [{"_id": p["categories"]["id"], "name": p["categories"]["name"], "image": p["categories"].get("image", "")}]
        products.append({
            "_id": p["id"],
            "name": p["name"],
            "image": p["image"] or [],
            "unit": p["unit"],
            "stock": p["stock"],
            "price": float(p["price"]) if p["price"] is not None else 0.0,
            "discount": float(p["discount"]) if p["discount"] is not None else 0.0,
            "description": p["description"],
            "food_type": p.get("food_type"),
            "prep_time": p.get("prep_time", "8 mins"),
            "section": p.get("section", "canteen"),
            "category": cat_info,
        })
    return {
        "message": "Canteen menu",
        "data": products,
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 3. Canteen Cart (outlet-scoped)
# -------------------------------------------------------
@router.get("/cart")
async def get_canteen_cart(current_user_id: str = Depends(get_current_user_id)):
    """Get the student's current canteen cart."""
    res = supabase.table("canteen_cart_items") \
        .select("*, products(id, name, image, price, discount, food_type, prep_time, section)") \
        .eq("user_id", current_user_id).execute()
    
    items = [map_cart_item(item) for item in res.data or []]
    outlet_id = items[0]["outlet_category_id"] if items else None
    
    return {
        "message": "Canteen cart",
        "data": items,
        "outlet_category_id": outlet_id,
        "error": False,
        "success": True
    }

@router.post("/cart/add")
async def add_to_canteen_cart(data: CanteenCartAddSchema, current_user_id: str = Depends(get_current_user_id)):
    """Add an item to canteen cart. Enforces single-outlet constraint (Zomato-style)."""
    # Check current cart for any existing outlet conflict
    existing_cart = supabase.table("canteen_cart_items") \
        .select("outlet_category_id").eq("user_id", current_user_id).limit(1).execute()
    
    if existing_cart.data:
        current_outlet = existing_cart.data[0]["outlet_category_id"]
        if current_outlet != data.outlet_category_id:
            # Get outlet name for better error message
            outlet_res = supabase.table("categories").select("name").eq("id", current_outlet).execute()
            outlet_name = outlet_res.data[0]["name"] if outlet_res.data else "another outlet"
            return {
                "message": f"Your cart has items from {outlet_name}. Clear cart to order from a different outlet.",
                "error": True,
                "success": False,
                "conflict": True,
                "current_outlet_id": current_outlet
            }
    
    # Check if product already in cart
    existing_item = supabase.table("canteen_cart_items") \
        .select("*").eq("user_id", current_user_id).eq("product_id", data.product_id).execute()
    
    if existing_item.data:
        new_qty = existing_item.data[0]["quantity"] + data.quantity
        supabase.table("canteen_cart_items").update({"quantity": new_qty}) \
            .eq("id", existing_item.data[0]["id"]).execute()
    else:
        supabase.table("canteen_cart_items").insert({
            "user_id": current_user_id,
            "product_id": data.product_id,
            "outlet_category_id": data.outlet_category_id,
            "quantity": data.quantity
        }).execute()
    
    return {"message": "Item added to canteen cart", "error": False, "success": True}

@router.put("/cart/update")
async def update_canteen_cart_qty(data: CanteenCartUpdateSchema, current_user_id: str = Depends(get_current_user_id)):
    if data.qty <= 0:
        supabase.table("canteen_cart_items").delete().eq("id", data.id).eq("user_id", current_user_id).execute()
        return {"message": "Item removed", "error": False, "success": True}
    
    supabase.table("canteen_cart_items").update({"quantity": data.qty}).eq("id", data.id).eq("user_id", current_user_id).execute()
    return {"message": "Cart updated", "error": False, "success": True}

@router.delete("/cart/clear")
async def clear_canteen_cart(current_user_id: str = Depends(get_current_user_id)):
    supabase.table("canteen_cart_items").delete().eq("user_id", current_user_id).execute()
    return {"message": "Cart cleared", "error": False, "success": True}

@router.delete("/cart/item")
async def delete_canteen_cart_item(data: CanteenCartDeleteSchema, current_user_id: str = Depends(get_current_user_id)):
    supabase.table("canteen_cart_items").delete().eq("id", data.id).eq("user_id", current_user_id).execute()
    return {"message": "Item removed", "error": False, "success": True}

# -------------------------------------------------------
# 4. Canteen Checkout → Token Generation
# -------------------------------------------------------
@router.post("/checkout")
async def canteen_checkout(data: CanteenCheckoutSchema, current_user_id: str = Depends(get_current_user_id)):
    """Checkout canteen cart. Generates a sequential outlet-scoped token."""
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

    # 1. Fetch cart items
    cart_res = supabase.table("canteen_cart_items") \
        .select("*, products(id, name, image, price, discount, stock)") \
        .eq("user_id", current_user_id) \
        .eq("outlet_category_id", data.outlet_category_id).execute()
    
    if not cart_res.data:
        raise HTTPException(status_code=400, detail="Your canteen cart is empty")
    
    # 2. Build product snapshot, validate stock & compute total
    product_details = []
    stock_updates = []
    total_amt = 0.0
    for item in cart_res.data:
        prod = item["products"]
        
        # Validate stock first
        if "id" in prod:
            current_stock = int(prod.get("stock") or 0)
            if item["quantity"] > current_stock:
                raise HTTPException(status_code=400, detail=f"Not enough stock for {prod.get('name', 'Product')}. Available: {current_stock}")
            stock_updates.append({"id": prod["id"], "new_stock": current_stock - item["quantity"]})
            
        price = float(prod["price"]) if prod["price"] else 0.0
        discount = float(prod["discount"]) if prod["discount"] else 0.0
        effective_price = price * (1 - discount / 100)
        subtotal = effective_price * item["quantity"]
        total_amt += subtotal
        product_details.append({
            "name": prod["name"],
            "image": prod["image"][0] if prod["image"] else "",
            "price": price,
            "discount": discount,
            "quantity": item["quantity"],
            "subtotal": round(subtotal, 2)
        })
        
    # Deduct stock after all validations pass
    for update in stock_updates:
        supabase.table("products").update({"stock": update["new_stock"]}).eq("id", update["id"]).execute()
    
    # 3. Get next sequential token number for this outlet (MAX + 1)
    max_token_res = supabase.table("canteen_tokens") \
        .select("token_number") \
        .eq("outlet_category_id", data.outlet_category_id) \
        .order("token_number", desc=True).limit(1).execute()
    
    next_token_number = 1
    if max_token_res.data:
        next_token_number = max_token_res.data[0]["token_number"] + 1
    
    # 4. Calculate which notify batch this token belongs to
    notify_batch = (next_token_number - 1) // 10  # batch 0 = tokens 1-10, batch 1 = tokens 11-20...
    
    # 5. Insert the token
    insert_res = supabase.table("canteen_tokens").insert({
        "token_number": next_token_number,
        "outlet_category_id": data.outlet_category_id,
        "user_id": current_user_id,
        "product_details": product_details,
        "total_amt": round(total_amt, 2),
        "status": "ACTIVE",
        "notify_batch": notify_batch
    }).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to generate token")
    
    # 6. Clear the canteen cart
    supabase.table("canteen_cart_items").delete().eq("user_id", current_user_id).execute()
    
    token = map_token(insert_res.data[0])
    
    return {
        "message": f"Order placed! Your token number is #{next_token_number}",
        "error": False,
        "success": True,
        "data": token
    }

# -------------------------------------------------------
# 5. Student: View Their Own Tokens
# -------------------------------------------------------
@router.get("/my-tokens")
async def get_my_tokens(current_user_id: str = Depends(get_current_user_id)):
    """Get all canteen tokens belonging to the logged-in student."""
    res = supabase.table("canteen_tokens") \
        .select("*, categories(id, name, image)") \
        .eq("user_id", current_user_id) \
        .order("created_at", desc=True).execute()
    
    tokens = []
    for t in res.data or []:
        mapped = map_token(t)
        if t.get("categories"):
            mapped["outlet"] = {
                "_id": t["categories"]["id"],
                "name": t["categories"]["name"],
                "image": t["categories"].get("image", "")
            }
        tokens.append(mapped)
    
    return {
        "message": "My canteen tokens",
        "data": tokens,
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 6. Operator: View Tokens for Their Outlet
# -------------------------------------------------------
@router.get("/tokens/{outlet_category_id}")
async def get_outlet_tokens(outlet_category_id: str, current_user_id: str = Depends(get_current_user_id)):
    """Operator view: get all tokens for a specific outlet. Admin can access any, CANTEEN_OP only their own."""
    user = require_canteen_auth(current_user_id)
    
    # CANTEEN_OP can only access their own outlet
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != outlet_category_id:
        raise HTTPException(status_code=403, detail="You can only view tokens for your assigned outlet")
    
    res = supabase.table("canteen_tokens") \
        .select("*, users(name, email)") \
        .eq("outlet_category_id", outlet_category_id) \
        .order("token_number", desc=False).execute()
    
    tokens = []
    for t in res.data or []:
        mapped = map_token(t)
        if t.get("users"):
            mapped["student"] = {
                "name": t["users"]["name"],
                "email": t["users"]["email"]
            }
        tokens.append(mapped)
    
    # Also return today's notify batch offset
    active_tokens = [t for t in tokens if t["status"] == "ACTIVE"]
    
    return {
        "message": "Outlet tokens",
        "data": tokens,
        "active_count": len(active_tokens),
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 7. Operator: Mark Token Done
# -------------------------------------------------------
@router.put("/token/mark-done")
async def mark_token_done(data: MarkTokenDoneSchema, current_user_id: str = Depends(get_current_user_id)):
    """Mark a canteen token as DONE (served). Operator/Admin only."""
    user = require_canteen_auth(current_user_id)
    
    # Fetch the token to validate outlet ownership for CANTEEN_OP
    token_res = supabase.table("canteen_tokens").select("*").eq("id", data.token_id).execute()
    if not token_res.data:
        raise HTTPException(status_code=404, detail="Token not found")
    
    token = token_res.data[0]
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != token["outlet_category_id"]:
        raise HTTPException(status_code=403, detail="Cannot modify tokens from another outlet")
    
    update_res = supabase.table("canteen_tokens").update({"status": "DONE"}).eq("id", data.token_id).execute()
    
    return {
        "message": f"Token #{token['token_number']} marked as done",
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 8. Operator: Notify Next 10
# -------------------------------------------------------
@router.post("/notify-next")
async def notify_next_batch(data: NotifyNextSchema, current_user_id: str = Depends(get_current_user_id)):
    """Advance the notify batch window by 10. Returns the new batch range."""
    user = require_canteen_auth(current_user_id)
    
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != data.outlet_category_id:
        raise HTTPException(status_code=403, detail="Not your outlet")
    
    new_offset = data.current_offset + 10
    start = new_offset + 1
    end = new_offset + 10
    
    # Stamp tokens in this range with notify_batch so students can poll for their turn
    supabase.table("canteen_tokens") \
        .update({"notify_batch": new_offset}) \
        .eq("outlet_category_id", data.outlet_category_id) \
        .gte("token_number", start) \
        .lte("token_number", end) \
        .execute()

    # Fetch current notify_rev and increment it
    cur = supabase.table("categories").select("notify_rev").eq("id", data.outlet_category_id).execute()
    cur_rev = (cur.data[0].get("notify_rev") or 0) if cur.data else 0
    new_rev = cur_rev + 1

    # Persist the current notify offset and rev on the outlet category row
    supabase.table("categories") \
        .update({"notify_offset": new_offset, "notify_rev": new_rev}) \
        .eq("id", data.outlet_category_id) \
        .execute()
    
    return {
        "message": f"Now serving tokens {start}–{end}",
        "new_offset": new_offset,
        "notify_rev": new_rev,
        "range_start": start,
        "range_end": end,
        "error": False,
        "success": True
    }

@router.post("/notify-again")
async def notify_again(data: NotifyAgainSchema, current_user_id: str = Depends(get_current_user_id)):
    """Re-notify the SAME current batch (same offset, bumps notify_rev so students see it again)."""
    user = require_canteen_auth(current_user_id)

    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != data.outlet_category_id:
        raise HTTPException(status_code=403, detail="Not your outlet")

    # The current_offset IS the already-applied offset (serving start+1 to end+10)
    start = data.current_offset + 1
    end = data.current_offset + 10

    # Re-stamp tokens (same notify_batch value)
    supabase.table("canteen_tokens") \
        .update({"notify_batch": data.current_offset}) \
        .eq("outlet_category_id", data.outlet_category_id) \
        .gte("token_number", start) \
        .lte("token_number", end) \
        .execute()

    # Bump notify_rev so students' dismiss keys become stale and popup re-fires
    cur = supabase.table("categories").select("notify_rev").eq("id", data.outlet_category_id).execute()
    cur_rev = (cur.data[0].get("notify_rev") or 0) if cur.data else 0
    new_rev = cur_rev + 1

    supabase.table("categories") \
        .update({"notify_rev": new_rev}) \
        .eq("id", data.outlet_category_id) \
        .execute()

    return {
        "message": f"Re-notified tokens {start}–{end}",
        "notify_rev": new_rev,
        "range_start": start,
        "range_end": end,
        "error": False,
        "success": True
    }

@router.post("/notify-prev")
async def notify_prev_batch(data: NotifyPrevSchema, current_user_id: str = Depends(get_current_user_id)):
    """Go back to the previous notify batch window by 10."""
    user = require_canteen_auth(current_user_id)
    
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != data.outlet_category_id:
        raise HTTPException(status_code=403, detail="Not your outlet")
    
    new_offset = max(0, data.current_offset - 10)
    start = new_offset + 1
    end = new_offset + 10
    
    # Stamp tokens in this range with notify_batch so students can poll for their turn
    supabase.table("canteen_tokens") \
        .update({"notify_batch": new_offset}) \
        .eq("outlet_category_id", data.outlet_category_id) \
        .gte("token_number", start) \
        .lte("token_number", end) \
        .execute()

    # Fetch current notify_rev and increment it
    cur = supabase.table("categories").select("notify_rev").eq("id", data.outlet_category_id).execute()
    cur_rev = (cur.data[0].get("notify_rev") or 0) if cur.data else 0
    new_rev = cur_rev + 1

    # Persist the current notify offset and rev on the outlet category row
    supabase.table("categories") \
        .update({"notify_offset": new_offset, "notify_rev": new_rev}) \
        .eq("id", data.outlet_category_id) \
        .execute()
    
    return {
        "message": f"Now serving tokens {start}–{end}",
        "new_offset": new_offset,
        "notify_rev": new_rev,
        "range_start": start,
        "range_end": end,
        "error": False,
        "success": True
    }

@router.get("/notify-status/{outlet_category_id}")
async def get_notify_status(outlet_category_id: str):
    """Public endpoint. Returns the current token serving range and revision for a canteen outlet."""
    res = supabase.table("categories").select("notify_offset, notify_rev").eq("id", outlet_category_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Outlet not found")
    offset = res.data[0].get("notify_offset") or 0
    rev = res.data[0].get("notify_rev") or 0
    return {
        "success": True,
        "data": {
            "notify_offset": offset,
            "notify_rev": rev,
            "range_start": offset + 1,
            "range_end": offset + 10
        }
    }

# -------------------------------------------------------
# 9. Analytics for an Outlet
# -------------------------------------------------------
@router.get("/analytics/{outlet_category_id}")
async def get_outlet_analytics(outlet_category_id: str, current_user_id: str = Depends(get_current_user_id)):
    """Revenue + volume stats for an outlet. Admin or assigned CANTEEN_OP."""
    user = require_canteen_auth(current_user_id)
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != outlet_category_id:
        raise HTTPException(status_code=403, detail="Not your outlet")
    
    res = supabase.table("canteen_tokens").select("total_amt, status").eq("outlet_category_id", outlet_category_id).execute()
    tokens = res.data or []
    
    total_tokens = len(tokens)
    done_tokens = len([t for t in tokens if t["status"] == "DONE"])
    active_tokens = len([t for t in tokens if t["status"] == "ACTIVE"])
    total_revenue = sum(float(t["total_amt"]) for t in tokens if t["status"] == "DONE")
    
    return {
        "message": "Outlet analytics",
        "data": {
            "total_tokens": total_tokens,
            "done_tokens": done_tokens,
            "active_tokens": active_tokens,
            "total_revenue": round(total_revenue, 2),
            "avg_order_value": round(total_revenue / done_tokens, 2) if done_tokens > 0 else 0
        },
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 10. Operator Profile — Get their assigned outlet
# -------------------------------------------------------
@router.get("/my-outlet")
async def get_my_outlet(current_user_id: str = Depends(get_current_user_id)):
    """Returns the outlet assigned to the logged-in canteen operator."""
    user_res = supabase.table("users").select("role, outlet_category_id, name, email").eq("id", current_user_id).execute()
    if not user_res.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = user_res.data[0]
    if user["role"] not in ["ADMIN", "CANTEEN_OP"]:
        raise HTTPException(status_code=403, detail="Not a canteen operator")
    
    outlet = None
    if user["outlet_category_id"]:
        outlet_res = supabase.table("categories").select("*").eq("id", user["outlet_category_id"]).execute()
        if outlet_res.data:
            outlet = outlet_res.data[0]
            outlet["_id"] = outlet["id"]
    
    return {
        "message": "Operator outlet info",
        "data": {
            "name": user["name"],
            "email": user["email"],
            "role": user["role"],
            "outlet": outlet
        },
        "error": False,
        "success": True
    }

# -------------------------------------------------------
# 11. Reset Daily Tokens
# -------------------------------------------------------
class ResetTokensSchema(BaseModel):
    outlet_category_id: str

@router.post("/reset-tokens")
async def reset_daily_tokens(data: ResetTokensSchema, current_user_id: str = Depends(get_current_user_id)):
    """Deletes all tokens for the given outlet and resets notify offsets to 0. (Resets sales & revenue)."""
    user = require_canteen_auth(current_user_id)
    if user["role"] == "CANTEEN_OP" and user.get("outlet_category_id") != data.outlet_category_id:
        raise HTTPException(status_code=403, detail="Not your outlet")
    
    # 1. Delete all tokens for this outlet
    supabase.table("canteen_tokens").delete().eq("outlet_category_id", data.outlet_category_id).execute()
    
    # 2. Reset category tracking offsets
    supabase.table("categories").update({
        "notify_offset": 0,
        "notify_rev": 0
    }).eq("id", data.outlet_category_id).execute()
    
    return {
        "message": "Daily tokens and revenue reset successfully",
        "error": False,
        "success": True
    }
