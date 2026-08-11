from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/address", tags=["address"])

# Pydantic Schemas
class CreateAddressSchema(BaseModel):
    room_number: str
    building_name: str
    branch: str

class UpdateAddressSchema(BaseModel):
    _id: str
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    branch: Optional[str] = None

class DisableAddressSchema(BaseModel):
    _id: str

# Helper to map Supabase address to React style
def map_address(item: dict) -> dict:
    return {
        "_id": item["id"],
        "room_number": item["room_number"],
        "building_name": item["building_name"],
        "branch": item["branch"],
        "status": item["status"]
    }

# Endpoints
@router.post("/create")
async def create_address(data: CreateAddressSchema, current_user_id: str = Depends(get_current_user_id)):
    insert_res = supabase.table("addresses").insert({
        "user_id": current_user_id,
        "room_number": data.room_number,
        "building_name": data.building_name,
        "branch": data.branch,
        "status": True
    }).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create address")
        
    return {
        "message": "Address created successfully",
        "error": False,
        "success": True,
        "data": map_address(insert_res.data[0])
    }

@router.get("/get")
async def get_addresses(current_user_id: str = Depends(get_current_user_id)):
    # Retrieve active addresses (status = True)
    response = supabase.table("addresses").select("*").eq("user_id", current_user_id).eq("status", True).execute()
    mapped_data = [map_address(item) for item in response.data or []]
    
    return {
        "message": "Addresses fetched successfully",
        "error": False,
        "success": True,
        "data": mapped_data
    }

@router.put("/update")
async def update_address(data: UpdateAddressSchema, current_user_id: str = Depends(get_current_user_id)):
    update_data = {}
    if data.room_number is not None:
        update_data["room_number"] = data.room_number
    if data.building_name is not None:
        update_data["building_name"] = data.building_name
    if data.branch is not None:
        update_data["branch"] = data.branch
        
    if not update_data:
        return {
            "message": "No update fields provided",
            "error": True,
            "success": False
        }
        
    response = supabase.table("addresses").update(update_data).eq("id", data._id).eq("user_id", current_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update address")
        
    return {
        "message": "Address updated successfully",
        "error": False,
        "success": True,
        "data": map_address(response.data[0])
    }

@router.delete("/disable")
async def disable_address(data: DisableAddressSchema, current_user_id: str = Depends(get_current_user_id)):
    # Simply set status to False instead of deleting, to maintain history of orders
    response = supabase.table("addresses").update({"status": False}).eq("id", data._id).eq("user_id", current_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to disable address")
        
    return {
        "message": "Address disabled successfully",
        "error": False,
        "success": True
    }
