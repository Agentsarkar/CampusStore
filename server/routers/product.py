from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional, Any
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/product", tags=["product"])

# Pydantic Schemas
class CreateProductSchema(BaseModel):
    name: str
    image: List[str]
    category: List[str]  # Accepts list of category IDs
    subCategory: Optional[List[str]] = [] # Ignored for simplified version
    unit: str
    stock: int
    price: float
    discount: Optional[float] = 0
    description: str
    more_details: Optional[Any] = {}
    section: Optional[str] = "flash"       # 'flash' or 'canteen'
    food_type: Optional[str] = None        # 'veg' or 'non-veg'
    prep_time: Optional[str] = "8 mins"   # Canteen prep time

class GetProductSchema(BaseModel):
    page: Optional[int] = 1
    limit: Optional[int] = 10
    search: Optional[str] = ""

class GetProductByCategorySchema(BaseModel):
    id: str

class GetProductByCategoryAndSubCategorySchema(BaseModel):
    categoryId: str
    subCategoryId: Optional[str] = ""
    page: Optional[int] = 1
    limit: Optional[int] = 10

class GetProductDetailsSchema(BaseModel):
    productId: str

class UpdateProductSchema(BaseModel):
    id: str
    name: Optional[str] = None
    image: Optional[List[str]] = None
    category: Optional[List[str]] = None
    unit: Optional[str] = None
    stock: Optional[int] = None
    price: Optional[float] = None
    discount: Optional[float] = None
    description: Optional[str] = None
    more_details: Optional[Any] = None
    section: Optional[str] = None
    food_type: Optional[str] = None
    prep_time: Optional[str] = None

class DeleteProductSchema(BaseModel):
    id: str

class SearchProductSchema(BaseModel):
    search: Optional[str] = ""
    page: Optional[int] = 1
    limit: Optional[int] = 10

# Helpers to map Supabase products to React style
def map_product(item: dict) -> dict:
    cat_info = []
    if item.get("categories"):
        cat_info = [{
            "_id": item["categories"]["id"],
            "name": item["categories"]["name"],
            "image": item["categories"]["image"]
        }]
    return {
        "_id": item["id"],
        "name": item["name"],
        "image": item["image"] or [],
        "unit": item["unit"],
        "stock": item["stock"],
        "price": float(item["price"]) if item["price"] is not None else 0.0,
        "discount": float(item["discount"]) if item["discount"] is not None else 0.0,
        "description": item["description"],
        "publish": item["publish"],
        "section": item.get("section", "flash"),
        "food_type": item.get("food_type"),
        "prep_time": item.get("prep_time", "8 mins"),
        "category": cat_info,
        "subCategory": []  # Empty list to prevent frontend crash
    }

# Endpoints
@router.post("/create")
async def create_product(data: CreateProductSchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    category_id = data.category[0] if data.category else None
    
    insert_res = supabase.table("products").insert({
        "name": data.name,
        "image": data.image,
        "category_id": category_id,
        "unit": data.unit,
        "stock": data.stock,
        "price": data.price,
        "discount": data.discount,
        "description": data.description,
        "section": data.section or "flash",
        "food_type": data.food_type,
        "prep_time": data.prep_time or "8 mins",
        "publish": True
    }).execute()
    
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to create product")
        
    return {
        "message": "Product Created Successfully",
        "data": map_product(insert_res.data[0]),
        "error": False,
        "success": True
    }

@router.post("/get")
async def get_products(data: GetProductSchema):
    page = data.page or 1
    limit = data.limit or 50
    skip = (page - 1) * limit
    
    query = supabase.table("products").select("*, categories(*)").order("created_at", desc=True)
    
    # Simple search filter if provided
    if data.search:
        query = query.ilike("name", f"%{data.search}%")
    
    # Section filter (default to flash for storefront)
    if hasattr(data, 'section') and data.section:
        query = query.eq("section", data.section)
        
    # Get total count first
    count_res = supabase.table("products").select("id", count="exact")
    if data.search:
        count_res = count_res.ilike("name", f"%{data.search}%")
    count_data = count_res.execute()
    total_count = count_data.count or 0
    
    # Fetch chunk
    response = query.range(skip, skip + limit - 1).execute()
    
    mapped_data = [map_product(item) for item in response.data or []]
    
    return {
        "message": "Product data",
        "error": False,
        "success": True,
        "totalCount": total_count,
        "totalNoPage": (total_count + limit - 1) // limit,
        "data": mapped_data
    }


@router.post("/get-product-by-category")
async def get_product_by_category(data: GetProductByCategorySchema):
    # Search products matching category_id
    response = supabase.table("products").select("*, categories(*)").eq("category_id", data.id).limit(15).execute()
    mapped_data = [map_product(item) for item in response.data or []]
    return {
        "message": "category product list",
        "data": mapped_data,
        "error": False,
        "success": True
    }

@router.post("/get-pruduct-by-category-and-subcategory")
async def get_product_by_category_and_subcategory(data: GetProductByCategoryAndSubCategorySchema):
    # For simplified version, we just search by categoryId since subcategory is removed
    page = data.page or 1
    limit = data.limit or 10
    skip = (page - 1) * limit
    
    count_res = supabase.table("products").select("id", count="exact").eq("category_id", data.categoryId).execute()
    total_count = count_res.count or 0
    
    response = supabase.table("products").select("*, categories(*)").eq("category_id", data.categoryId).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
    mapped_data = [map_product(item) for item in response.data or []]
    
    return {
        "message": "Product list",
        "data": mapped_data,
        "totalCount": total_count,
        "page": page,
        "limit": limit,
        "success": True,
        "error": False
    }

@router.post("/get-product-details")
async def get_product_details(data: GetProductDetailsSchema):
    response = supabase.table("products").select("*, categories(*)").eq("id", data.productId).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="Product not found")
        
    return {
        "message": "product details",
        "data": map_product(response.data[0]),
        "error": False,
        "success": True
    }

@router.put("/update-product-details")
async def update_product_details(data: UpdateProductSchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    update_data = {}
    if data.name is not None:
        update_data["name"] = data.name
    if data.image is not None:
        update_data["image"] = data.image
    if data.category is not None and len(data.category) > 0:
        update_data["category_id"] = data.category[0]
    if data.unit is not None:
        update_data["unit"] = data.unit
    if data.stock is not None:
        update_data["stock"] = data.stock
    if data.price is not None:
        update_data["price"] = data.price
    if data.discount is not None:
        update_data["discount"] = data.discount
    if data.description is not None:
        update_data["description"] = data.description
    if data.section is not None:
        update_data["section"] = data.section
    if data.food_type is not None:
        update_data["food_type"] = data.food_type
    if data.prep_time is not None:
        update_data["prep_time"] = data.prep_time
        
    if not update_data:
        return {
            "message": "No update fields provided",
            "error": True,
            "success": False
        }
        
    response = supabase.table("products").update(update_data).eq("id", data.id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update product")
        
    return {
        "message": "updated successfully",
        "data": response.data[0],
        "error": False,
        "success": True
    }

@router.delete("/delete-product")
async def delete_product(data: DeleteProductSchema, current_user_id: str = Depends(get_current_user_id)):
    # Verify ADMIN
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    response = supabase.table("products").delete().eq("id", data.id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to delete product")
        
    return {
        "message": "Delete successfully",
        "error": False,
        "success": True
    }

@router.post("/search-product")
async def search_product(data: SearchProductSchema):
    page = data.page or 1
    limit = data.limit or 10
    skip = (page - 1) * limit
    
    query = supabase.table("products").select("*, categories(*)").order("created_at", desc=True)
    if data.search:
        query = query.ilike("name", f"%{data.search}%")
        
    count_res = supabase.table("products").select("id", count="exact")
    if data.search:
        count_res = count_res.ilike("name", f"%{data.search}%")
    count_data = count_res.execute()
    total_count = count_data.count or 0
    
    response = query.range(skip, skip + limit - 1).execute()
    mapped_data = [map_product(item) for item in response.data or []]
    
    return {
        "message": "Product data",
        "error": False,
        "success": True,
        "data": mapped_data,
        "totalCount": total_count,
        "totalPage": (total_count + limit - 1) // limit,
        "page": page,
        "limit": limit
    }
