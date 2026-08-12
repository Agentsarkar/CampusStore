import uuid
from fastapi import APIRouter, File, UploadFile, Depends, HTTPException
from config import supabase
from utils.auth import get_current_user_id

router = APIRouter(prefix="/api/file", tags=["upload"])

@router.post("/upload")
async def upload_image(image: UploadFile = File(...), current_user_id: str = Depends(get_current_user_id)):
    # Verify user is ADMIN (since only admins upload products/categories)
    user_res = supabase.table("users").select("role").eq("id", current_user_id).execute()
    if not user_res.data or user_res.data[0]["role"] != "ADMIN":
        raise HTTPException(status_code=403, detail="Admin permissions required")
        
    try:
        # Create a unique file path
        file_ext = image.filename.split(".")[-1] if "." in image.filename else "jpg"
        file_path = f"uploads/{uuid.uuid4()}.{file_ext}"
        
        # Read file contents
        file_content = await image.read()
        
        # Upload to Supabase Storage
        upload_res = supabase.storage.from_("grocery-images").upload(
            file_path,
            file_content,
            {"content-type": image.content_type}
        )
        
        # Get public URL
        public_url = supabase.storage.from_("grocery-images").get_public_url(file_path)
        
        return {
            "message": "Upload done",
            "success": True,
            "error": False,
            "data": {
                "url": public_url
            }
        }
    except Exception as e:
        return {
            "message": str(e),
            "success": False,
            "error": True
        }
