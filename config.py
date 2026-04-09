# config.py
from dotenv import load_dotenv
import os

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
NEIS_API_KEY = os.getenv("NEIS_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")