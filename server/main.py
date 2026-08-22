import sys
import os
from pathlib import Path

# Fix for Vercel deployment: Add the 'server' folder to Python's import path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from dotenv import load_dotenv

# Load env variables
load_dotenv()

# Import routers
from routers.user import router as user_router
from routers.category import router as category_router
from routers.product import router as product_router
from routers.cart import router as cart_router
from routers.address import router as address_router
from routers.order import router as order_router
from routers.upload import router as upload_router
from routers.canteen import router as canteen_router
from routers.rider import router as rider_router
from routers.admin_rider import router as admin_rider_router
from routers.payment import router as payment_router
from routers.print import router as print_router
from routers.flights import router as flights_router

app = FastAPI(title="Campus E-Commerce API", version="1.0.0")

# Setup CORS (still needed for dev tools / external access)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API routers FIRST (so they take priority over static files)
app.include_router(user_router)
app.include_router(category_router)
app.include_router(product_router)
app.include_router(cart_router)
app.include_router(address_router)
app.include_router(order_router)
app.include_router(upload_router)
app.include_router(canteen_router)
app.include_router(rider_router)
app.include_router(admin_rider_router)
app.include_router(payment_router)
app.include_router(print_router)
app.include_router(flights_router, prefix="/api")

# Serve the frontend client folder as static files at root
CLIENT_DIR = Path(__file__).parent.parent / "client"

@app.get("/")
def serve_index():
    """Serve the main index.html"""
    return FileResponse(CLIENT_DIR / "index.html")

@app.get("/api/status")
def read_root():
    port = os.getenv("PORT", "8000")
    return {"message": f"Server is running on port {port}"}

# Mount static files LAST (catch-all for frontend assets)
if CLIENT_DIR.exists() and not os.getenv("VERCEL"):
    app.mount("/", StaticFiles(directory=str(CLIENT_DIR), html=True), name="static")
