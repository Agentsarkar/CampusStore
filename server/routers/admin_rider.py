from fastapi import APIRouter, HTTPException, Depends
from typing import List
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/admin/riders", tags=["admin_rider"])

def verify_admin(user_id: str = Depends(get_current_user_id)):
    # Check if user is an ADMIN
    res = supabase.table("users").select("role").eq("id", user_id).execute()
    if not res.data or res.data[0].get("role") != "ADMIN":
        raise HTTPException(status_code=403, detail="Super Admin privileges required")
    return user_id

@router.get("/pending")
async def get_pending_riders(admin_id: str = Depends(verify_admin)):
    res = supabase.table("riders").select("*").eq("status", "PENDING").execute()
    return {
        "success": True,
        "data": res.data
    }

@router.post("/{rider_id}/verify")
async def verify_rider(rider_id: str, admin_id: str = Depends(verify_admin)):
    # 1. Update the rider status
    res = supabase.table("riders").update({"status": "VERIFIED"}).eq("id", rider_id).execute()
    if not res.data:
        raise HTTPException(status_code=404, detail="Rider not found")
        
    rider = res.data[0]
    
    # 2. Delete the ID card from storage to save space
    campus_id_url = rider.get("campus_id_url")
    if campus_id_url:
        try:
            # Extract the filename from the URL
            filename = campus_id_url.split("/")[-1]
            if filename:
                # Remove the file from the bucket
                supabase.storage.from_("id-card").remove([filename])
                
                # Optional: Clear the URL in the database so we know it's gone
                supabase.table("riders").update({"campus_id_url": ""}).eq("id", rider_id).execute()
        except Exception as e:
            # Log the error but don't fail the verification process
            print(f"Warning: Failed to delete ID card for rider {rider_id}: {str(e)}")
            
    return {
        "success": True,
        "message": "Rider verified successfully",
        "data": rider
    }
