"""
SmartCare Queue AI - Supabase Database Initializer & Verification Utility
Tests connection to Supabase and verifies table accessibility.
"""
import sys
import os
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(root_dir))

from backend.config import Config
from backend.services.supabase_service import db

def test_supabase_connection():
    print("=" * 65)
    print("SmartCare Queue AI - Supabase Connection & Verification")
    print("=" * 65)
    
    url = Config.SUPABASE_URL
    anon_key = Config.SUPABASE_ANON_KEY
    role_key = Config.SUPABASE_SERVICE_ROLE_KEY

    print(f"SUPABASE_URL:             {url or '(not configured)'}")
    print(f"SUPABASE_ANON_KEY:        {'[CONFIGURED]' if anon_key else '(empty)'}")
    print(f"SUPABASE_SERVICE_ROLE_KEY:{'[CONFIGURED]' if role_key else '(empty)'}")
    print(f"IS_SUPABASE_CONFIGURED:   {Config.IS_SUPABASE_CONFIGURED}")
    print("-" * 65)

    if not Config.IS_SUPABASE_CONFIGURED:
        print("[!] Live Supabase credentials not found in backend/.env.")
        print("    The system is running with the offline/cache database engine.")
        print("    To connect your live Supabase project:")
        print("    1. Copy backend/.env.example to backend/.env")
        print("    2. Fill in your SUPABASE_URL, SUPABASE_ANON_KEY, and SUPABASE_SERVICE_ROLE_KEY")
        print("    3. Run schema.sql, policies.sql, functions.sql, and seed.sql in the Supabase SQL Editor.")
        print("=" * 65)
        return False

    if not db.admin_client and not db.client:
        print("[-] Failed to initialize Supabase client. Please check your credentials.")
        return False

    client = db.admin_client or db.client
    tables = [
        "profiles",
        "departments",
        "doctors",
        "queues",
        "queue_entries",
        "appointments",
        "lab_orders",
        "bills",
        "payments",
        "notifications",
        "hospital_locations",
        "priority_requests",
        "feedback"
    ]

    print("[*] Testing read access to all 13 Supabase schema tables:")
    all_ok = True
    for table in tables:
        try:
            res = client.table(table).select("*").limit(1).execute()
            count_info = f"OK ({len(res.data)} sample rows)" if hasattr(res, 'data') else "OK"
            print(f"  ✓ {table:22}: {count_info}")
        except Exception as e:
            all_ok = False
            print(f"  ✗ {table:22}: Error - {e}")

    print("-" * 65)
    if all_ok:
        print("[SUCCESS] All 13 tables are connected and accessible in Supabase!")
        print("All records will be stored directly into your Supabase database.")
    else:
        print("[NOTE] Some tables were not found or not yet created.")
        print("Please copy and run the contents of 'supabase/schema.sql' inside")
        print("your Supabase Dashboard -> SQL Editor.")
    print("=" * 65)
    return all_ok

if __name__ == "__main__":
    test_supabase_connection()
