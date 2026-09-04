import os
from pathlib import Path
from dotenv import load_dotenv

# Search for .env in current folder, parent, or backend folder
env_path = Path(__file__).resolve().parent / '.env'
if not env_path.exists():
    env_path = Path(__file__).resolve().parent.parent / '.env'
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
else:
    load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('FLASK_SECRET_KEY', 'smartcare-secure-jwt-flask-key-2026')
    SUPABASE_URL = os.environ.get('SUPABASE_URL', '').strip()
    SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY', '').strip()
    SUPABASE_SERVICE_ROLE_KEY = os.environ.get('SUPABASE_SERVICE_ROLE_KEY', '').strip()
    
    # Frontend CORS origins
    FRONTEND_URL = os.environ.get('FRONTEND_URL', '*')
    
    # Check whether real Supabase credentials are provided
    IS_SUPABASE_CONFIGURED = bool(
        SUPABASE_URL and 
        not SUPABASE_URL.startswith('https://your-project') and 
        SUPABASE_ANON_KEY and 
        not SUPABASE_ANON_KEY.startswith('your-anon')
    )
