"""
Streaming Service - Server-Sent Events (SSE) for real-time responses
"""
import asyncio
from typing import AsyncGenerator, Optional
from fastapi import Response
from fastapi.responses import StreamingResponse
import json

class StreamingService:
    """
    Handles streaming responses using Server-Sent Events (SSE).
    """
    
    @staticmethod
    def create_sse_response(generator: AsyncGenerator) -> StreamingResponse:
        """Create an SSE streaming response."""
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            }
        )
    
    @staticmethod
    async def format_sse(data: dict, event: str = "message") -> str:
        """Format data as SSE message."""
        json_data = json.dumps(data, ensure_ascii=False)
        return f"event: {event}\ndata: {json_data}\n\n"
    
    @staticmethod
    async def stream_tokens(
        llm,
        prompt: str,
        on_token: Optional[callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream tokens from LLM and yield SSE-formatted messages.
        """
        full_response = ""
        
        try:
            # Send start event
            yield await StreamingService.format_sse(
                {"type": "start", "timestamp": asyncio.get_event_loop().time()},
                event="start"
            )
            
            # Stream tokens
            async for chunk in llm.astream(prompt):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += token
                
                if on_token:
                    on_token(token)
                
                yield await StreamingService.format_sse(
                    {"type": "token", "content": token},
                    event="token"
                )
            
            # Send completion event
            yield await StreamingService.format_sse(
                {
                    "type": "done",
                    "full_response": full_response,
                    "total_tokens": len(full_response.split())
                },
                event="done"
            )
            
        except Exception as e:
            yield await StreamingService.format_sse(
                {"type": "error", "message": str(e)},
                event="error"
            )
    
    @staticmethod
    async def stream_with_tools(
        llm,
        prompt: str,
        tools: list = None,
        on_tool_call: Optional[callable] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream response with tool call updates.
        """
        try:
            yield await StreamingService.format_sse(
                {"type": "start"},
                event="start"
            )
            
            # Simulate tool processing (replace with actual tool execution)
            if tools:
                for tool in tools:
                    yield await StreamingService.format_sse(
                        {"type": "tool_start", "tool": tool.get("name", "unknown")},
                        event="tool"
                    )
                    await asyncio.sleep(0.1)  # Simulated tool execution
                    yield await StreamingService.format_sse(
                        {"type": "tool_done", "tool": tool.get("name", "unknown")},
                        event="tool"
                    )
            
            # Stream main response
            full_response = ""
            async for chunk in llm.astream(prompt):
                token = chunk.content if hasattr(chunk, 'content') else str(chunk)
                full_response += token
                yield await StreamingService.format_sse(
                    {"type": "token", "content": token},
                    event="token"
                )
            
            yield await StreamingService.format_sse(
                {"type": "done", "full_response": full_response},
                event="done"
            )
            
        except Exception as e:
            yield await StreamingService.format_sse(
                {"type": "error", "message": str(e)},
                event="error"
            )


# Singleton instance
streaming = StreamingService()
