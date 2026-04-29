import os
import sys

# Ensure the project root is in the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.serving.mcp.server import server

async def test():
    # Simulate an agent calling the 'get_daily_trends' tool
    print("Testing get_daily_trends...")
    try:
        from src.serving.mcp.server import handle_call_tool
        result = await handle_call_tool("get_daily_trends", {"start_date": "2024-05-12", "end_date": "2024-05-15"})
        print(result[0].text)
        
        print("\nTesting retrieve_articles...")
        result2 = await handle_call_tool("retrieve_articles", {"keyword": "ai", "limit": 2})
        print(result2[0].text)
    except Exception as e:
        print(f"Test failed: {e}")

if __name__ == "__main__":
    import asyncio
    asyncio.run(test())
