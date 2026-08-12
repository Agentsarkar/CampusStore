from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/category", tags=["category"])

# Pydantic Schemas
class AddCategorySchema(BaseModel):
    name: str
    image: str
    section: Optional[str] = "flash"  # 'flash' or 'canteen'
    address: Optional[str] = ""       # Physical location of the outlet

class UpdateCategorySchema(BaseModel):
    id: str
    name: Optional[str] = None
    image: Optional[str] = None
    section: Optional[str] = None
    address: Optional[str] = None

class DeleteCategorySchema(BaseModel):
    id: str

# Endpoints
@router.post("/add-category")
async def add_category(data: AddCategorySchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify user is ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    # Check if category already exists
    exists_res = supabase.table("categories").select("*").eq("name", data.name).execute()
    if exists_res.data:
        return {
            "message": "Category already exists",
            "error": True,
            "success": False
        }
        
    insert_res = supabase.table("categories").insert({
        "name": data.name,
        "image": data.image,
        "section": data.section or "flash",
        "address": data.address or ""
    }).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to insert category")
        
    return {
        "message": "Category added successfully",
        "error": False,
        "success": True,
        "data": insert_res.data[0]
    }

@router.get("/get")
async def get_categories(section: Optional[str] = None):
    query = supabase.table("categories").select("*")
    if section:
        query = query.eq("section", section)
    response = query.execute()
    # Map 'id' to '_id' for compatibility with React/original frontend client logic
    mapped_data = []
    for item in response.data or []:
        item["_id"] = item["id"]
        mapped_data.append(item)
        
    return {
        "message": "All categories fetched",
        "error": False,
        "success": True,
        "data": mapped_data
    }

@router.put("/update")
async def update_category(data: UpdateCategorySchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify user is ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    update_data = {}
    if data.name:
        update_data["name"] = data.name
    if data.image is not None:
        update_data["image"] = data.image
    if data.section is not None:
        update_data["section"] = data.section
    if data.address is not None:
        update_data["address"] = data.address
        
    if not update_data:
        return {
            "message": "No update fields provided",
            "error": True,
            "success": False
        }
        
    response = supabase.table("categories").update(update_data).eq("id", data.id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update category")
        
    updated_cat = response.data[0]
    updated_cat["_id"] = updated_cat["id"]
    
    return {
        "message": "Category updated successfully",
        "error": False,
        "success": True,
        "data": updated_cat
    }

@router.delete("/delete")
async def delete_category(data: DeleteCategorySchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify user is ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    response = supabase.table("categories").delete().eq("id", data.id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to delete category or category does not exist")
        
    return {
        "message": "Category deleted successfully",
        "error": False,
        "success": True
    }
