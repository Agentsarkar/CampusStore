from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
import uuid
from typing import Optional, List
from config import supabase
from utils.auth import hash_password, verify_password, create_access_token, get_current_user_id
import datetime

router = APIRouter(prefix="/api/rider", tags=["rider"])

class LoginSchema(BaseModel):
    email: str
    password: str

@router.get("/available-status")
async def check_rider_available_status():
    """Public status check returning whether any delivery partners (riders) are currently online."""
    try:
        riders_res = supabase.table("riders").select("id").eq("is_online", True).execute()
        count = len(riders_res.data) if riders_res.data else 0
        return {
            "success": True,
            "available": count > 0,
            "count": count
        }
    except Exception as e:
        return {
            "success": True,
            "available": False,
            "count": 0,
            "error": str(e)
        }


@router.post("/register")
async def register_rider(
    name: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    phone: str = Form(...),
    roll_number: str = Form(...),
    file: UploadFile = File(...)
):
    # Check if rider already exists
    response = supabase.table("riders").select("*").eq("email", email).execute()
    if response.data:
        return {"message": "Email already registered", "error": True, "success": False}
        
    # Generate unique filename for the ID card
    ext = file.filename.split(".")[-1] if "." in file.filename else "png"
    file_path = f"{uuid.uuid4()}.{ext}"
    
    # Upload to Supabase Storage 'id-card' bucket
    file_bytes = await file.read()
    try:
        res = supabase.storage.from_("id-card").upload(
            file_path, 
            file_bytes, 
            {"content-type": file.content_type}
        )
    except Exception as e:
        # If bucket doesn't exist or other error
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")
        
    # Get public URL
    public_url = supabase.storage.from_("id-card").get_public_url(file_path)
    
    hashed = hash_password(password)
    rider_payload = {
        "name": name,
        "email": email,
        "password_hash": hashed,
        "phone": phone,
        "roll_number": roll_number,
        "campus_id_url": public_url,
        "status": "PENDING"
    }
    
    insert_res = supabase.table("riders").insert(rider_payload).execute()
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to register rider")
        
    registered_rider = insert_res.data[0]
    registered_rider.pop("password_hash", None)
    
    return {
        "message": "Application submitted successfully",
        "error": False,
        "success": True,
        "data": registered_rider
    }

@router.post("/login")
async def login_rider(data: LoginSchema):
    response = supabase.table("riders").select("*").eq("email", data.email).execute()
    if not response.data:
        return {"message": "Invalid email or password", "error": True, "success": False}
        
    rider = response.data[0]
    
    if not verify_password(data.password, rider.get("password_hash")):
        return {"message": "Invalid email or password", "error": True, "success": False}
        
    # If pending or rejected, still allow login but frontend will handle redirect based on status
    token = create_access_token(rider["id"])
    rider.pop("password_hash", None)
    
    return {
        "message": "Login successful",
        "error": False,
        "success": True,
        "data": {
            "accessToken": token,
            "rider": rider
        }
    }

# Ensure the requester is a rider
def get_current_rider_id(user_id: str = Depends(get_current_user_id)) -> str:
    # Handle backward compatibility if token contains a dict
    if isinstance(user_id, dict):
        return user_id.get("id")
    return user_id

class ToggleOnlineSchema(BaseModel):
    is_online: bool

@router.put("/toggle-online")
async def toggle_online(payload: ToggleOnlineSchema, rider_id: str = Depends(get_current_rider_id)):
    update_data = {"is_online": payload.is_online}
    if payload.is_online:
        # Reset counters when going online
        update_data["declined_orders"] = 0
        
    try:
        res = supabase.table("riders").update(update_data).eq("id", rider_id).execute()
    except Exception as e:
        print(f"Fallback toggle_online (columns might not exist): {e}")
        res = supabase.table("riders").update({"is_online": payload.is_online}).eq("id", rider_id).execute()

    if not res.data:
        raise HTTPException(status_code=404, detail="Rider not found")
        
    return {
        "success": True,
        "message": "Status updated",
        "data": res.data[0]
    }

@router.put("/orders/penalty/{penalty_type}")
async def penalty_order(penalty_type: str, rider_id: str = Depends(get_current_rider_id)):
    """Handles incrementing declined or ignored orders for a rider"""
    if penalty_type not in ["decline", "ignore"]:
        return {"success": False, "message": "Invalid penalty type"}
        
    try:
        col = "declined_orders" if penalty_type == "decline" else "ignored_orders"
        limit = 3 if penalty_type == "decline" else 5
        
        rider_res = supabase.table("riders").select(col).eq("id", rider_id).execute()
        if not rider_res.data:
            return {"success": False, "message": "Rider not found"}
            
        current_val = rider_res.data[0].get(col)
        current_val = current_val if current_val is not None else 0
        new_val = current_val + 1
        
        is_online = True
        if new_val >= limit:
            is_online = False
            
        update_data = {col: new_val, "is_online": is_online}
        supabase.table("riders").update(update_data).eq("id", rider_id).execute()
        
        return {"success": True, "forced_offline": not is_online, "count": new_val}
    except Exception as e:
        print(f"Error in penalty: {e}")
        return {"success": False, "message": str(e)}

from utils.auth import decode_token

@router.post("/offline-beacon")
async def offline_beacon(token: str = Form(...)):
    """
    Called by navigator.sendBeacon when a rider closes their tab.
    Avoids CORS preflight by using a simple POST with FormData.
    """
    try:
        user_id = decode_token(token)
        if isinstance(user_id, dict):
            user_id = user_id.get("id")
            
        if user_id:
            supabase.table("riders").update({"is_online": False}).eq("id", user_id).execute()
    except Exception as e:
        print(f"[BEACON ERROR]: {e}")
    return {"success": True}

@router.get("/orders/available")
async def get_available_orders(rider_id: str = Depends(get_current_rider_id)):
    # Fetch orders that are PENDING
    response = supabase.table("orders").select("*, users(name, mobile)").eq("delivery_status", "PENDING").execute()
    return {
        "success": True,
        "data": response.data
    }

@router.post("/orders/{order_id}/accept")
async def accept_order(order_id: str, rider_id: str = Depends(get_current_rider_id)):
    # Verify order is still pending
    chk = supabase.table("orders").select("delivery_status").eq("id", order_id).execute()
    if not chk.data or chk.data[0].get("delivery_status") != "PENDING":
        raise HTTPException(status_code=400, detail="Order is no longer available")
        
    # Assign to rider and take offline
    res = supabase.table("orders").update({
        "delivery_status": "PROCESSING",
        "rider_id": rider_id
    }).eq("id", order_id).execute()
    
    # Mark rider offline so they don't get double assigned
    supabase.table("riders").update({"is_online": False}).eq("id", rider_id).execute()
    
    return {
        "success": True,
        "message": "Order assigned",
        "data": res.data[0]
    }

from typing import Optional

class StatusUpdate(BaseModel):
    status: str # 'PICKED_UP' or 'OUT_FOR_DELIVERY' or 'COMPLETED'
    otp: Optional[str] = None

@router.put("/orders/{order_id}/status")
async def update_order_status(order_id: str, payload: StatusUpdate, rider_id: str = Depends(get_current_rider_id)):
    if payload.status == "COMPLETED":
        if not payload.otp:
            raise HTTPException(status_code=400, detail="OTP is required to complete delivery")
            
        # Verify OTP
        chk_res = supabase.table("orders").select("delivery_otp").eq("id", order_id).eq("rider_id", rider_id).execute()
        if not chk_res.data:
            raise HTTPException(status_code=404, detail="Order not found")
            
        if chk_res.data[0].get("delivery_otp") != payload.otp:
            raise HTTPException(status_code=400, detail="Invalid Delivery OTP")

    update_data = {"delivery_status": payload.status}
    if payload.status == "COMPLETED":
        update_data["payment_status"] = "PAID"
        
    res = supabase.table("orders").update(update_data).eq("id", order_id).eq("rider_id", rider_id).execute()
    
    if not res.data:
        raise HTTPException(status_code=404, detail="Order not found or not assigned to you")
        
    # If completed, add 20 to earnings and put rider back online
    if payload.status == "COMPLETED":
        rider_res = supabase.table("riders").select("earnings").eq("id", rider_id).execute()
        if rider_res.data:
            current_earnings = rider_res.data[0].get("earnings", 0)
            supabase.table("riders").update({
                "earnings": float(current_earnings) + 20.0,
                "is_online": True
            }).eq("id", rider_id).execute()
            
    return {
        "success": True,
        "message": f"Order status updated to {payload.status}",
        "data": res.data[0]
    }

@router.get("/stats")
async def get_rider_stats(rider_id: str = Depends(get_current_rider_id)):
    rider_res = supabase.table("riders").select("earnings").eq("id", rider_id).execute()
    earnings = 0
    if rider_res.data:
        earnings = rider_res.data[0].get("earnings", 0)
        
    orders_res = supabase.table("orders").select("id").eq("rider_id", rider_id).eq("delivery_status", "COMPLETED").execute()
    total_orders = len(orders_res.data) if orders_res.data else 0
    
    return {
        "success": True,
        "data": {
            "todayEarnings": earnings,
            "totalOrders": total_orders
        }
    }

@router.get("/history")
async def get_rider_history(rider_id: str = Depends(get_current_rider_id)):
    res = supabase.table("orders").select("*").eq("rider_id", rider_id).eq("delivery_status", "COMPLETED").execute()
    return {
        "success": True,
        "data": res.data or []
    }

@router.get("/profile")
async def get_rider_profile(rider_id: str = Depends(get_current_rider_id)):
    res = supabase.table("riders").select("*").eq("id", rider_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Rider not found")
    rider = res.data[0]
    rider.pop("password_hash", None)
    return {
        "success": True,
        "data": rider
    }

class ProfileUpdate(BaseModel):
    phone: str

@router.put("/profile")
async def update_rider_profile(payload: ProfileUpdate, rider_id: str = Depends(get_current_rider_id)):
    res = supabase.table("riders").update({"phone": payload.phone}).eq("id", rider_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Rider not found")
    return {
        "success": True,
        "message": "Profile updated successfully",
        "data": res.data[0]
    }
