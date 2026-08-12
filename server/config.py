import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables (try local directory first, then default)
current_dir = os.path.dirname(os.path.abspath(__file__))
load_dotenv(os.path.join(current_dir, ".env"))
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")
SECRET_KEY = os.getenv("SECRET_KEY", "fallback-jwt-secret-key-12345")

if not SUPABASE_URL or not SUPABASE_ANON_KEY:
    # We will log a warning instead of raising an error directly, so the app doesn't crash on startup
    # before the user creates their .env file.
    print("WARNING: SUPABASE_URL and SUPABASE_ANON_KEY are not set. Database integrations will fail until they are configured.")

supabase: Client = None
if SUPABASE_URL and SUPABASE_ANON_KEY:
    supabase = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)
