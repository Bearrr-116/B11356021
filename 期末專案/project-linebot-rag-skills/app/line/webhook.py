from fastapi import APIRouter, Request, HTTPException
from fastapi.concurrency import run_in_threadpool
import hashlib
import hmac
import base64
import httpx
import asyncio
from app.config import settings
from app.router.intent_router import route_intent
from app.rag.retriever import retrieve_context
from app.generator.responder import generate_response

router = APIRouter()

async def send_reply(reply_token: str, message: str):
    url = f"{settings.line_api_base}/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.line_channel_access_token}",
    }
    # 分割長訊息
    chunks = [message[i:i+4500] for i in range(0, len(message), 4500)]
    messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]
    
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json={
            "replyToken": reply_token,
            "messages": messages,
        })

async def process_message(reply_token: str, user_message: str):
    try:
        # 1. 路由
        route = await route_intent(user_message)
        skill = route.get("skill", "general")
        need_rag = route.get("need_rag", False)
        rag_categories = route.get("rag_categories", [])
        
        # 2. RAG 檢索
        context = ""
        if need_rag:
            context = await retrieve_context(user_message, rag_categories)
        
        # 3. 生成回覆
        response = await generate_response(skill, user_message, context)
        
        # 4. 回覆
        await send_reply(reply_token, response)
    
    except Exception as e:
        print(f"Error: {e}")
        await send_reply(reply_token, "系統暫時無法處理，請稍後再試。")

@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    
    # 驗證簽章
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(
        settings.line_channel_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash).decode("utf-8")
    
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    
    import json
    data = json.loads(body)
    
    for event in data.get("events", []):
        if event.get("type") == "message" and event["message"].get("type") == "text":
            reply_token = event.get("replyToken")
            user_message = event["message"]["text"]
            asyncio.create_task(process_message(reply_token, user_message))
    
    return {"status": "ok"}