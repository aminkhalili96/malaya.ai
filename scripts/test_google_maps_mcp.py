import asyncio
import os
import sys

# Add root to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp.client import MCPClientManager
from dotenv import load_dotenv

# Load .env explicitly
load_dotenv()

async def main():
    print("Testing Google Maps MCP Connection...")
    
    # Check for API Key
    if "GOOGLE_MAPS_API_KEY" not in os.environ:
        print("❌ GOOGLE_MAPS_API_KEY not found in environment variables.")
        # Try to print raw .env content path to debug
        print(f"Current CWD: {os.getcwd()}")
        print(f".env exists: {os.path.exists('.env')}")
        # Proceeding anyway to see if it fails gracefully
    else:
        print("✅ GOOGLE_MAPS_API_KEY is set.")

    manager = MCPClientManager()
    
    # Check config
    if "google_maps" not in manager.mcp_config:
        print("❌ 'google_maps' not found in mcp_servers config.")
        return

    print(f"Server Config: {manager.mcp_config['google_maps']}")

    try:
        await manager.connect_all()
        print("✅ Connected to MCP servers.")
        
        tools = await manager.list_tools()
        print(f"Found {len(tools)} tools.")
        
        maps_tools = [t['name'] for t in tools if 'maps' in t['name']]
        
        if maps_tools:
            print("✅ Google Maps Tools found:")
            for t in maps_tools:
                print(f"  - {t}")
        else:
            print("⚠️ No tools with 'maps' in name found. Listing all:")
            for t in tools:
                print(f"  - {t['name']}")

        await manager.close()

    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
