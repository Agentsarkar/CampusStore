from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/address", tags=["address"])

BUILDING_MAP = {
    "AU 1": 1,
    "AU 2": 2,
    "AU 3": 3,
    "AU 4": 4,
    "AU 5": 5,
    "AU 6": 6,
    "AU 7": 7,
    "AU 8": 8,
    "AU 9": 9,
    "Girls Hostel": 10,
    "International Girls Hostel": 11,
    "Boys Hostel": 12,
}

BUILDING_CODE_TO_NAME = {
    1: "AU 1",
    2: "AU 2",
    3: "AU 3",
    4: "AU 4",
    5: "AU 5",
    6: "AU 6",
    7: "AU 7",
    8: "AU 8",
    9: "AU 9",
    10: "Girls Hostel",
    11: "International Girls Hostel",
    12: "Boys Hostel",
}

BUILDING_BASE_PRICES = {
    1: 15,   # AU 1
    2: 18,   # AU 2
    3: 21,   # AU 3
    4: 25,   # AU 4
    5: 25,   # AU 5
    6: 15,   # AU 6
    7: 30,   # AU 7
    8: 30,   # AU 8
    9: 18,   # AU 9
    10: 20,  # Girls Hostel
    11: 28,  # International Girls Hostel
    12: 25,  # Boys Hostel
}

# Pydantic Schemas
class CreateAddressSchema(BaseModel):
    room_number: str
    building_name: str
    branch: str
    building_code: Optional[int] = None

class UpdateAddressSchema(BaseModel):
    _id: str
    room_number: Optional[str] = None
    building_name: Optional[str] = None
    branch: Optional[str] = None
    building_code: Optional[int] = None

class DisableAddressSchema(BaseModel):
    _id: str

class FeeCalculationSchema(BaseModel):
    building_name: Optional[str] = None
    building_code: Optional[int] = None
    room_number: str

def extract_floor_level(room_number: str) -> int:
    room_str = str(room_number or "").strip()
    if not room_str.isdigit():
        return 0

    if len(room_str) == 3:
        # 3-digit (e.g. 104 -> 1st digit '1' -> Floor 0 Ground; 205 -> 1st digit '2' -> Floor 1)
        first_digit = int(room_str[0])
        return max(0, first_digit - 1)
    elif len(room_str) == 4:
        # 4-digit (e.g. 1001 -> 2nd digit '0' -> Floor 0 Ground; 1208 -> 2nd digit '2' -> Floor 2)
        second_digit = int(room_str[1])
        return max(0, second_digit)
    
    return 0

def calculate_delivery_fee_details(building_name: str, room_number: str, building_code: Optional[int] = None) -> dict:
    b_name, r_num, b_code = sanitize_address_fields(building_name, room_number, building_code)
    base_price = BUILDING_BASE_PRICES.get(b_code, 20)
    floor_level = extract_floor_level(r_num)
    
    # 15% surcharge per floor above Ground Floor (Floor 0)
    floor_multiplier = 1.0 + (floor_level * 0.15)
    delivery_fee = int(round(base_price * floor_multiplier))

    return {
        "building_code": b_code,
        "building_name": b_name,
        "room_number": r_num,
        "base_price": base_price,
        "floor_level": floor_level,
        "floor_multiplier": round(floor_multiplier, 2),
        "delivery_fee": delivery_fee
    }

def sanitize_address_fields(building_name: str, room_number: str, building_code: Optional[int] = None):
    b_name = str(building_name or "").strip()
    r_num = str(room_number or "").strip()

    # Detect if frontend or previous save inverted building_name and room_number
    if b_name.isdigit() and (r_num in BUILDING_MAP or (r_num.isdigit() and int(r_num) in BUILDING_CODE_TO_NAME)):
        b_name, r_num = r_num, b_name

    if b_name in BUILDING_MAP:
        b_code = BUILDING_MAP[b_name]
    elif b_name.isdigit() and int(b_name) in BUILDING_CODE_TO_NAME:
        b_code = int(b_name)
        b_name = BUILDING_CODE_TO_NAME[b_code]
    elif building_code and building_code in BUILDING_CODE_TO_NAME:
        b_code = building_code
        b_name = BUILDING_CODE_TO_NAME[b_code]
    else:
        b_code = 1
        b_name = "AU 1"

    return b_name, r_num, b_code

# Helper to map Supabase address to React style
def map_address(item: dict) -> dict:
    b_raw = str(item.get("building_name", "")).strip()
    r_raw = str(item.get("room_number", "")).strip()
    b_code_raw = item.get("building_code")

    b_name, r_num, b_code = sanitize_address_fields(b_raw, r_raw, b_code_raw)
    fee_details = calculate_delivery_fee_details(b_name, r_num, b_code)

    return {
        "_id": item["id"],
        "room_number": r_num,
        "building_name": b_name,
        "building_code": b_code,
        "branch": item.get("branch", "Main Campus"),
        "delivery_fee": fee_details["delivery_fee"],
        "fee_details": fee_details,
        "status": item.get("status", True)
    }

# Endpoints
@router.post("/calculate-fee")
async def calculate_fee_endpoint(data: FeeCalculationSchema):
    fee_details = calculate_delivery_fee_details(
        data.building_name or "", data.room_number, data.building_code
    )
    return {
        "message": "Fee calculated successfully",
        "error": False,
        "success": True,
        "data": fee_details
    }

@router.post("/create")
async def create_address(data: CreateAddressSchema, current_user_id: str = Depends(get_current_user_id)):
    b_name, room_str, b_code = sanitize_address_fields(data.building_name, data.room_number, data.building_code)

    if not (room_str.isdigit() and 3 <= len(room_str) <= 4):
        raise HTTPException(status_code=400, detail="Room number must be a 3-digit or 4-digit number (e.g. 104 or 1208)")

    insert_payload = {
        "user_id": current_user_id,
        "room_number": room_str,
        "building_name": b_name,
        "branch": data.branch,
        "status": True
    }

    try:
        insert_res = supabase.table("addresses").insert({**insert_payload, "building_code": b_code}).execute()
    except Exception:
        insert_res = supabase.table("addresses").insert(insert_payload).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create address")

    res_data = insert_res.data[0]
    res_data["building_name"] = b_name
    res_data["room_number"] = room_str
    res_data["building_code"] = b_code
    return {
        "message": "Address created successfully",
        "error": False,
        "success": True,
        "data": map_address(res_data)
    }

@router.get("/get")
async def get_addresses(current_user_id: str = Depends(get_current_user_id)):
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
    if data.room_number is not None or data.building_name is not None:
        b_name, room_str, b_code = sanitize_address_fields(
            data.building_name or "", data.room_number or "", data.building_code
        )
        if data.room_number is not None:
            if not (room_str.isdigit() and 3 <= len(room_str) <= 4):
                raise HTTPException(status_code=400, detail="Room number must be a 3-digit or 4-digit number (e.g. 104 or 1208)")
            update_data["room_number"] = room_str
        if data.building_name is not None:
            update_data["building_name"] = b_name

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

class DisableAddressSchema(BaseModel):
    _id: Optional[str] = None
    id: Optional[str] = None
    address_id: Optional[str] = None

async def _perform_disable_address(target_id: str, current_user_id: str):
    if not target_id:
        raise HTTPException(status_code=40, detail="Address ID is required")
        
    try:
        response = supabase.table("addresses").update({"status": False}).eq("id", target_id).eq("user_id", current_user_id).execute()
        if not response.data:
            # Fallback: try hard delete if soft delete returned empty
            response = supabase.table("addresses").delete().eq("id", target_id).eq("user_id", current_user_id).execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to remove address: {str(e)}")

    return {
        "message": "Address disabled successfully",
        "error": False,
        "success": True
    }

@router.delete("/disable")
@router.post("/disable")
async def disable_address_body(data: Optional[DisableAddressSchema] = None, address_id: Optional[str] = None, current_user_id: str = Depends(get_current_user_id)):
    target_id = address_id
    if data:
        target_id = data._id or data.id or data.address_id or target_id
    return await _perform_disable_address(target_id, current_user_id)

@router.delete("/disable/{address_id}")
@router.post("/disable/{address_id}")
async def disable_address_path(address_id: str, current_user_id: str = Depends(get_current_user_id)):
    return await _perform_disable_address(address_id, current_user_id)




