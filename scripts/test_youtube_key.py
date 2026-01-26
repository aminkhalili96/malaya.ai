import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    print("❌ GOOGLE_API_KEY not found in .env")
    exit(1)

print(f"🔑 Testing Key: {API_KEY[:10]}...")

# Unauthenticated search for a video (Requires YouTube Data API v3)
url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q=Malaya&type=video&key={API_KEY}"

try:
    response = requests.get(url)
    data = response.json()
    
    if response.status_code == 200:
        print("\n✅ SUCCESS! YouTube Data API is enabled.")
        print(f"   Found {len(data.get('items', []))} results.")
        print("   You do NOT need a new key.")
    else:
        print(f"\n❌ FAILED. Status Code: {response.status_code}")
        print(f"   Error: {data.get('error', {}).get('message')}")
        print("\n👇 ACTION REQUIRED:")
        print("   1. Go to Google Cloud Console (https://console.cloud.google.com/apis/library)")
        print("   2. Search for 'YouTube Data API v3'")
        print("   3. Click 'ENABLE'")
except Exception as e:
    print(f"\n❌ Error connecting: {e}")
