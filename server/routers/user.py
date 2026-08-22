import random
import datetime
from fastapi import APIRouter, HTTPException, Depends, status, Header
from pydantic import BaseModel, EmailStr
from typing import Optional
from config import supabase
from utils.auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    create_reset_token,
    verify_reset_token,
    decode_token,
    get_current_user_id
)
from utils.email import send_otp_email

router = APIRouter(prefix="/api/user", tags=["user"])

# Pydantic Schemas
class RegisterSchema(BaseModel):
    name: str
    email: EmailStr
    password: str
    mobile: Optional[str] = None

class LoginSchema(BaseModel):
    email: EmailStr
    password: str

class UpdateUserSchema(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    mobile: Optional[str] = None

class ForgotPasswordSchema(BaseModel):
    email: EmailStr

class VerifyOtpSchema(BaseModel):
    email: EmailStr
    otp: str

class ResetPasswordSchema(BaseModel):
    resetToken: Optional[str] = None
    email: Optional[EmailStr] = None
    newPassword: str


# Endpoints
@router.post("/register")
async def register(data: RegisterSchema):
    if len(data.password) < 6:
        return {
            "message": "Password must be at least 6 characters long",
            "error": True,
            "success": False
        }
        
    # Check if user already exists
    response = supabase.table("users").select("*").eq("email", data.email).execute()
    if response.data:
        return {
            "message": "Already registered email",
            "error": True,
            "success": False
        }
    
    # If this is the first user in the system, make them an ADMIN
    users_check = supabase.table("users").select("id", count="exact").execute()
    user_count = users_check.count or 0
    role = "ADMIN" if user_count == 0 else "USER"

    hashed = hash_password(data.password)
    user_payload = {
        "name": data.name,
        "email": data.email,
        "password": hashed,
        "role": role,
        "status": "Active",
        **(({"mobile": data.mobile}) if data.mobile else {})
    }
    
    insert_res = supabase.table("users").insert(user_payload).execute()
    if not insert_res.data:
        raise HTTPException(status_code=500, detail="Failed to register user")
    
    registered_user = insert_res.data[0]
    # Delete password from output
    registered_user.pop("password", None)
    
    return {
        "message": "User register successfully",
        "error": False,
        "success": True,
        "data": registered_user
    }

@router.post("/login")
async def login(data: LoginSchema):
    # Fetch user
    response = supabase.table("users").select("*").eq("email", data.email).execute()
    if not response.data:
        return {
            "message": "User not registered",
            "error": True,
            "success": False
        }
    
    user = response.data[0]
    if user.get("status") != "Active":
        return {
            "message": "Contact to Admin",
            "error": True,
            "success": False
        }
    
    if not verify_password(data.password, user.get("password")):
        return {
            "message": "Check your password",
            "error": True,
            "success": False
        }
    
    access_token = create_access_token(user["id"])
    refresh_token = create_refresh_token(user["id"])
    
    return {
        "message": "Login successfully",
        "error": False,
        "success": True,
        "data": {
            "accessToken": access_token,
            "refreshToken": refresh_token
        }
    }

@router.get("/logout")
async def logout(current_user_id: str = Depends(get_current_user_id)):
    return {
        "message": "Logout successfully",
        "error": False,
        "success": True
    }

@router.get("/user-details")
async def user_details(current_user_id: str = Depends(get_current_user_id)):
    response = supabase.table("users").select("*").eq("id", current_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=404, detail="User not found")
    
    user = response.data[0]
    user.pop("password", None)
    return {
        "message": "User details",
        "error": False,
        "success": True,
        "data": user
    }

@router.put("/update-user")
async def update_user(data: UpdateUserSchema, current_user_id: str = Depends(get_current_user_id)):
    update_data = {}
    if data.name:
        update_data["name"] = data.name
    if data.email:
        # Check email uniqueness
        email_check = supabase.table("users").select("id").eq("email", data.email).execute()
        if email_check.data and email_check.data[0]["id"] != current_user_id:
            return {
                "message": "Email already in use by another account",
                "error": True,
                "success": False
            }
        update_data["email"] = data.email
    if data.mobile:
        update_data["mobile"] = data.mobile
        
    if not update_data:
        return {
            "message": "No update fields provided",
            "error": True,
            "success": False
        }
        
    response = supabase.table("users").update(update_data).eq("id", current_user_id).execute()
    if not response.data:
        raise HTTPException(status_code=500, detail="Failed to update user")
        
    updated_user = response.data[0]
    updated_user.pop("password", None)
    return {
        "message": "Updated successfully",
        "error": False,
        "success": True,
        "data": updated_user
    }

@router.post("/refresh-token")
async def refresh_token(authorization: str = Header(None)):
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid refresh token header")
        
    token = authorization.split()[1]
    user_id = decode_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Expired or invalid refresh token")
        
    # Generate new access token
    new_access = create_access_token(user_id)
    return {
        "message": "New access token",
        "error": False,
        "success": True,
        "data": {
            "accessToken": new_access
        }
    }

# In-memory OTP storage fallback (in case DB table otp_codes migration is pending)
IN_MEMORY_OTP_STORE = {}

@router.put("/forgot-password")
@router.post("/forgot-password")
async def forgot_password(data: ForgotPasswordSchema):
    # Verify email exists in users table
    response = supabase.table("users").select("id").eq("email", data.email).execute()
    if not response.data:
        return {
            "message": "Email not registered",
            "error": True,
            "success": False
        }
    
    # Generate 6-digit OTP code
    otp_code = str(random.randint(100000, 999999))
    now_utc = datetime.datetime.now(datetime.timezone.utc)
    expires_dt = now_utc + datetime.timedelta(minutes=10)
    expires_at = expires_dt.isoformat()
    
    # Save to in-memory store fallback
    IN_MEMORY_OTP_STORE[data.email] = {
        "otp_code": otp_code,
        "expires_at": expires_dt
    }

    # Attempt to save into Supabase otp_codes table
    try:
        supabase.table("otp_codes").delete().eq("email", data.email).execute()
        supabase.table("otp_codes").insert({
            "email": data.email,
            "otp_code": otp_code,
            "expires_at": expires_at
        }).execute()
    except Exception as db_err:
        print(f"[NOTE] Supabase table otp_codes insertion skipped (using in-memory store): {db_err}")

    # Send email (or log to dev console)
    send_otp_email(data.email, otp_code)
    
    return {
        "message": "OTP code sent to your email address",
        "error": False,
        "success": True,
        "data": {
            "email": data.email
        }
    }

@router.put("/verify-otp")
@router.post("/verify-otp")
async def verify_otp(data: VerifyOtpSchema):
    otp_record = None
    now_utc = datetime.datetime.now(datetime.timezone.utc)

    # 1. Try fetching from Supabase table first
    try:
        res = supabase.table("otp_codes").select("*").eq("email", data.email).order("created_at", desc=True).limit(1).execute()
        if res.data:
            rec = res.data[0]
            expires_str = rec.get("expires_at")
            expires_at_dt = datetime.datetime.fromisoformat(expires_str.replace("Z", "+00:00")) if expires_str else None
            otp_record = {
                "otp_code": rec.get("otp_code"),
                "expires_at": expires_at_dt
            }
    except Exception:
        pass

    # 2. Fallback to in-memory store if DB record not found
    if not otp_record and data.email in IN_MEMORY_OTP_STORE:
        otp_record = IN_MEMORY_OTP_STORE[data.email]

    if not otp_record:
        return {
            "message": "Invalid or expired OTP",
            "error": True,
            "success": False
        }
    
    # Check if OTP matches
    if otp_record.get("otp_code") != data.otp.strip():
        return {
            "message": "Incorrect OTP code",
            "error": True,
            "success": False
        }
    
    # Check expiration
    expires_at = otp_record.get("expires_at")
    if expires_at and now_utc > expires_at:
        IN_MEMORY_OTP_STORE.pop(data.email, None)
        try:
            supabase.table("otp_codes").delete().eq("email", data.email).execute()
        except Exception:
            pass
        return {
            "message": "OTP code has expired. Please request a new one.",
            "error": True,
            "success": False
        }

    # OTP is valid! Cleanup OTP
    IN_MEMORY_OTP_STORE.pop(data.email, None)
    try:
        supabase.table("otp_codes").delete().eq("email", data.email).execute()
    except Exception:
        pass
    
    # Generate short-lived signed password reset token (15 mins)
    reset_token = create_reset_token(data.email)
    
    return {
        "message": "OTP verified successfully",
        "error": False,
        "success": True,
        "data": {
            "resetToken": reset_token,
            "email": data.email
        }
    }


@router.put("/reset-password")
@router.post("/reset-password")
async def reset_password(data: ResetPasswordSchema):
    target_email = None

    # Preferred security path: Verify signed resetToken
    if data.resetToken:
        target_email = verify_reset_token(data.resetToken)
        if not target_email:
            return {
                "message": "Invalid or expired reset token. Please request a new OTP.",
                "error": True,
                "success": False
            }
    elif data.email:
        # Fallback if email is passed (verify user exists)
        target_email = data.email
    else:
        return {
            "message": "Missing reset token or email address",
            "error": True,
            "success": False
        }

    if len(data.newPassword) < 6:
        return {
            "message": "Password must be at least 6 characters long",
            "error": True,
            "success": False
        }

    # Retrieve user by target_email
    user_check = supabase.table("users").select("id").eq("email", target_email).execute()
    if not user_check.data:
        return {
            "message": "User account not found",
            "error": True,
            "success": False
        }
    
    user_id = user_check.data[0]["id"]
    hashed = hash_password(data.newPassword)
    
    # Update password
    update_res = supabase.table("users").update({"password": hashed}).eq("id", user_id).execute()
    if not update_res.data:
        raise HTTPException(status_code=500, detail="Failed to reset password")
        
    return {
        "message": "Password reset successfully! Please log in with your new password.",
        "error": False,
        "success": True
    }

