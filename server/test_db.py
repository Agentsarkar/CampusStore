from config import supabase

try:
    res = supabase.table("riders").select("is_online, id").limit(1).execute()
    print("Success! is_online exists:", res.data)
except Exception as e:
    print("Error:", e)
