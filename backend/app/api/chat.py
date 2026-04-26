import json
import asyncio
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from app.models.schemas import ChatRequest
from app.core.orchestrator import AIOrchestrator

router = APIRouter()
orchestrator = AIOrchestrator()

@router.post("/stream")
async def stream_chat(request: ChatRequest):
    """
    Streams responses from multiple AI agents simultaneously (Aggregator logic).
    """
    async def event_generator():
        # Using a Queue to aggregate chunks from multiple concurrent agents
        queue = asyncio.Queue()
        
        async def stream_agent(agent_id: str):
            try:
                # In IdeaGenie 2.0, orchestrator.chat_stream returns an async generator
                async for chunk in orchestrator.chat_stream(request.message, model_id=agent_id):
                    await queue.put({"agent": agent_id, "content": chunk})
            except Exception as e:
                await queue.put({"agent": agent_id, "error": str(e)})
            finally:
                # Signal that this agent is done
                await queue.put({"agent": agent_id, "done": True})

        # Start all agent tasks
        tasks = [asyncio.create_task(stream_agent(agent)) for agent in request.agents]
        
        active_tasks = len(tasks)
        while active_tasks > 0:
            item = await queue.get()
            if "done" in item:
                active_tasks -= 1
                continue
            
            yield f"data: {json.dumps(item)}\n\n"
        
        yield "data: [DONE]\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
