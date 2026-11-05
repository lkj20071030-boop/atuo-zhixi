"""Minimal real chat bridge; diagnosis/RAG endpoints are intentionally not implemented."""
import os
from typing import Literal
import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

app = FastAPI(title="知析 AI · Ollama 聊天桥接示例")
origins = os.getenv("FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173").split(",")
app.add_middleware(CORSMiddleware, allow_origins=[o.strip() for o in origins if o.strip()], allow_credentials=False, allow_methods=["GET", "POST"], allow_headers=["Content-Type"])
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://127.0.0.1:11434/api/chat")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

class Message(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=20000)

class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=2000)
    history: list[Message] = Field(default_factory=list, max_length=100)

@app.get("/health")
@app.get("/api/v1/health")
async def health():
    # Checks this web service only; does not assert that Ollama/model is available.
    return {"status": "ok", "service": "zhixi-chat-bridge"}

@app.post("/chat")
@app.post("/api/v1/chat")
async def chat(body: ChatRequest):
    messages = [{"role": "system", "content": "你是耐心的中文学习助手。解释概念与前置知识；没有检索依据时，不要声称完成了资料检索。"}]
    messages.extend(m.model_dump() for m in body.history[-20:])
    messages.append({"role": "user", "content": body.message})
    try:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(OLLAMA_URL, json={"model": OLLAMA_MODEL, "messages": messages, "stream": False})
        response.raise_for_status()
        data = response.json()
        reply = data.get("message", {}).get("content")
        if not isinstance(reply, str) or not reply.strip():
            raise HTTPException(status_code=502, detail="Ollama 未返回有效文本")
        return {"reply": reply}
    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="模型响应超时，请稍后重试")
    except (httpx.HTTPError, ValueError, TypeError, AttributeError):
        raise HTTPException(status_code=502, detail="无法获得 Ollama 响应，请检查服务、模型与后端日志")
