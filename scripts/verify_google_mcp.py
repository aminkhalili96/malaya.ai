import asyncio
import os
import sys

# Add root to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp.client import MCPClientManager
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("🚀 Connecting to MCP Servers (Google Maps & YouTube)...")
    
    manager = MCPClientManager()
    await manager.connect_all()
    
    tools = await manager.list_tools()
    print(f"\n✅ Total Tools Found: {len(tools)}")
    
    print("\n🗺️  Google Maps Tools:")
    for t in tools:
        if "maps" in t['name']:
            print(f"   - {t['name']}")

    print("\n📺 YouTube Tools:")
    found_youtube = False
    for t in tools:
        if "youtube" in t['name']:
            found_youtube = True
            print(f"   - {t['name']}")
    
    if not found_youtube:
        print("   ❌ No YouTube tools found! Check installation of @kazuph/mcp-youtube")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
