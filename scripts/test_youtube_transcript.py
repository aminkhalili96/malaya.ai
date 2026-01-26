import asyncio
import os
import sys

# Add root to pythonpath
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.mcp.client import MCPClientManager
from dotenv import load_dotenv

load_dotenv()

async def main():
    print("🚀 Testing YouTube Transcript Fetch...")
    
    manager = MCPClientManager()
    await manager.connect_all()
    await manager.list_tools() # Populate tool registry
    
    print("✅ Connected to MCP Servers. Calling get_youtube_transcript...")
    
    video_url = "https://www.youtube.com/watch?v=jNQXAC9IVRw" # Me at the zoo
    
    try:
        # Check if tool exists
        if "get_youtube_transcript" not in manager.tools:
            print("❌ Tool 'get_youtube_transcript' not found in available tools.")
            # Print available tools to help debug
            print("Available tools:", list(manager.tools.keys()))
        else:
            result = await manager.call_tool("get_youtube_transcript", {"url": video_url})
            print("\n📺 Result:")
            print(result[:500] + "..." if len(result) > 500 else result)
            
            if "Error" in result or "403" in result:
                print("\n❌ API Error Detected inside tool output.")
            else:
                print("\n✅ Transcript retrieved successfully!")

    except Exception as e:
        print(f"\n❌ Exception during tool call: {e}")

    await manager.close()

if __name__ == "__main__":
    asyncio.run(main())
