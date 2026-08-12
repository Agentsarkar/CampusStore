from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import supabase
from utils.razorpay_client import razorpay_client, RAZORPAY_KEY_ID
import uuid

router = APIRouter(
    prefix="/api/payment",
    tags=["payment"]
)

class CreatePaymentOrderSchema(BaseModel):
    amount: float
    is_delivery: Optional[bool] = True

@router.get("/config")
async def get_payment_config():
    """Return the public Razorpay Key ID for frontend initialization."""
    if not RAZORPAY_KEY_ID:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server")
    return {
        "success": True,
        "data": {
            "key_id": RAZORPAY_KEY_ID
        }
    }

@router.post("/create-order")
async def create_razorpay_order(data: CreatePaymentOrderSchema):
    """Create an order directly on Razorpay for a given amount, after verifying delivery partner availability."""
    if not razorpay_client:
        raise HTTPException(status_code=500, detail="Razorpay is not configured on the server")

    # 1. Check if any delivery partners (riders) are online and verified for delivery orders
    if data.is_delivery:
        riders_res = supabase.table("riders").select("id").eq("is_online", True).eq("status", "VERIFIED").execute()
        if not riders_res.data or len(riders_res.data) == 0:
            raise HTTPException(status_code=400, detail="No delivery partners are currently available. Please try again later.")
        
    amount_in_paise = int(data.amount * 100)
    if amount_in_paise < 100:
        raise HTTPException(status_code=400, detail="Minimum amount is INR 1.00")
        
    receipt_id = f"R-${str(uuid.uuid4())[:8]}"
    
    try:
        order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": receipt_id
        })
        
        return {
            "success": True,
            "data": {
                "razorpay_order_id": order["id"],
                "amount": order["amount"],
                "currency": order["currency"]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

