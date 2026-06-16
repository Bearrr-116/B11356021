from fastapi import APIRouter, Request, HTTPException
import hashlib
import hmac
import base64
import httpx
import asyncio
import json
import re
from app.config import settings
from app.router.intent_router import route_intent
from app.rag.retriever import retrieve_context
from app.generator.responder import generate_response
from app.storage.supabase_client import get_supabase

router = APIRouter()

user_states = {}

CITIES = [
    "台北", "臺北", "新北", "桃園", "新竹", "苗栗", "台中", "臺中",
    "彰化", "南投", "雲林", "嘉義", "台南", "臺南", "高雄", "屏東",
    "台東", "臺東", "花蓮", "宜蘭", "基隆", "澎湖", "金門", "連江"
]

LAW_PATTERN = re.compile(r'(民法|刑法|消費者保護法|勞動基準法|民事訴訟法|消保法|勞基法)第\s*\d+(?:-\d+)?\s*條')

LAW_PROMPT_TEMPLATE = """查詢法條：{query}

請依照以下格式回答：

📖 法條名稱
（完整法條名稱）

📜 法條內容
（引用法條原文，不得自行捏造）

💡 白話解釋
（用一般民眾容易理解的方式說明）

📝 適用情況
（列出常見適用案例）

⚠️ 注意事項
（提醒法條限制、例外規定或實務常見問題）

規則：
1. 優先依據提供的法條資料庫回答
2. 不得自行捏造法條內容
3. 若資料庫沒有該法條，請明確告知查無資料
4. 白話解釋需簡潔易懂
5. 回答使用繁體中文"""

async def save_user(user_id: str):
    try:
        supabase = get_supabase()
        supabase.table("line_users").upsert(
            {"user_id": user_id},
            on_conflict="user_id"
        ).execute()
    except Exception as e:
        print(f"save_user error: {e}")

async def send_reply(reply_token: str, message: str):
    url = f"{settings.line_api_base}/v2/bot/message/reply"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.line_channel_access_token}",
    }
    chunks = [message[i:i+4500] for i in range(0, len(message), 4500)]
    messages = [{"type": "text", "text": chunk} for chunk in chunks[:5]]
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json={
            "replyToken": reply_token,
            "messages": messages,
        })

async def push_message(user_id: str, message: str):
    url = f"{settings.line_api_base}/v2/bot/message/push"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {settings.line_channel_access_token}",
    }
    async with httpx.AsyncClient() as client:
        await client.post(url, headers=headers, json={
            "to": user_id,
            "messages": [{"type": "text", "text": message}]
        })

async def handle_law_query(reply_token: str, user_message: str):
    context = await retrieve_context(user_message, ["legal"])
    print(f"法條查詢：{user_message}，context length={len(context)}")
    if context:
        prompt = LAW_PROMPT_TEMPLATE.format(query=user_message)
        response = await generate_response("legal_advisor", prompt, context)
    else:
        response = (
            f"查無「{user_message}」相關法條資料。\n\n"
            "請確認法條名稱是否正確，\n"
            "或嘗試輸入完整名稱，例如：\n"
            "• 民法第184條\n"
            "• 消費者保護法第19條"
        )
    await send_reply(reply_token, response)

async def process_message(reply_token: str, user_message: str, user_id: str):
    try:
        await save_user(user_id)

        state = user_states.get(user_id, {})

        # 法條查詢狀態
        if state.get("waiting_for") == "law_article":
            user_states.pop(user_id, None)
            await handle_law_query(reply_token, user_message)
            return

        # 法律諮詢據點查詢
        if state.get("waiting_for") == "city_legal":
            city = None
            for c in CITIES:
                if c in user_message:
                    city = c
                    break

            if city:
                user_states.pop(user_id, None)
                context = await retrieve_context(city, ["legal"])
                print(f"搜尋：{city}，context length={len(context)}")
                if context:
                    prompt = (
                        f"請根據以下資料，列出「{city}」所有免費法律諮詢據點。\n"
                        f"每個據點請用以下格式：\n\n"
                        f"🏢 機構名稱\n"
                        f"📌 地址：xxx\n"
                        f"📞 電話：xxx\n"
                        f"🕐 服務時間：xxx\n"
                        f"📝 備註：xxx（若無備註則省略）\n"
                        f"────────────\n\n"
                        f"所有據點都要列出，不可省略。"
                    )
                    response = await generate_response("legal_advisor", prompt, context)
                else:
                    response = (
                        f"抱歉，目前沒有「{city}」的法律諮詢據點資料。\n\n"
                        f"建議直接撥打法扶全國專線：\n"
                        f"📞 02-412-8518 轉 2"
                    )
            else:
                response = "請輸入縣市名稱，例如：台北、高雄、台中、台南等。"

            await send_reply(reply_token, response)
            return

        # 地方法院查詢
        if state.get("waiting_for") == "city_court":
            city = None
            for c in CITIES:
                if c in user_message:
                    city = c
                    break

            if city:
                user_states.pop(user_id, None)
                context = await retrieve_context(city + "地方法院", ["legal"])
                if context:
                    prompt = (
                        f"請根據以下資料，列出「{city}」的地方法院資訊。\n"
                        f"每個法院請用以下格式：\n\n"
                        f"🏛️ 法院名稱\n"
                        f"📌 地址：xxx\n"
                        f"📞 電話：xxx\n"
                        f"🕐 服務時間：xxx\n"
                        f"📝 備註：xxx（若無備註則省略）\n"
                        f"────────────\n\n"
                        f"所有法院都要列出，不可省略。"
                    )
                    response = await generate_response("legal_advisor", prompt, context)
                else:
                    response = f"抱歉，目前沒有「{city}」地方法院的資料。"
            else:
                response = "請輸入縣市名稱，例如：台北、高雄、台中、台南等。"

            await send_reply(reply_token, response)
            return

        # 法扶據點查詢
        if state.get("waiting_for") == "city_laf":
            city = None
            for c in CITIES:
                if c in user_message:
                    city = c
                    break

            if city:
                user_states.pop(user_id, None)
                context = await retrieve_context(city, ["legal"])
                if context:
                    prompt = (
                        f"請根據以下資料，列出「{city}」所有法律扶助基金會（法扶）據點。\n"
                        f"每個據點請用以下格式：\n\n"
                        f"⚖️ 機構名稱\n"
                        f"📌 地址：xxx\n"
                        f"📞 電話：xxx\n"
                        f"🕐 服務時間：xxx\n"
                        f"📋 預約方式：xxx\n"
                        f"📝 備註：xxx（若無備註則省略）\n"
                        f"────────────\n\n"
                        f"所有據點都要列出，不可省略。"
                    )
                    response = await generate_response("legal_advisor", prompt, context)
                else:
                    response = (
                        f"抱歉，目前沒有「{city}」法扶據點的資料。\n\n"
                        f"建議直接撥打法扶全國專線：\n"
                        f"📞 02-412-8518 轉 2"
                    )
            else:
                response = "請輸入縣市名稱，例如：台北、高雄、台中、台南等。"

            await send_reply(reply_token, response)
            return

        # 選單觸發
        if user_message == "法律諮詢據點查詢":
            user_states[user_id] = {"waiting_for": "city_legal"}
            response = (
                "📍 請輸入縣市名稱查詢法律諮詢據點\n\n"
                "例如：台北、新北、台中、台南、高雄"
            )
            await send_reply(reply_token, response)
            return

        if user_message == "地方法院據點查詢":
            user_states[user_id] = {"waiting_for": "city_court"}
            response = (
                "🏛️ 請輸入縣市名稱查詢地方法院\n\n"
                "例如：台北、新北、台中、台南、高雄"
            )
            await send_reply(reply_token, response)
            return

        if user_message == "法律扶助基金會據點查詢":
            user_states[user_id] = {"waiting_for": "city_laf"}
            response = (
                "⚖️ 請輸入縣市名稱查詢法扶據點\n\n"
                "例如：台北、新北、台中、台南、高雄"
            )
            await send_reply(reply_token, response)
            return

        if user_message == "法條查詢":
            user_states[user_id] = {"waiting_for": "law_article"}
            response = (
                "⚖️ 請輸入想查詢的法條\n\n"
                "例如：\n"
                "• 民法第184條\n"
                "• 刑法第320條\n"
                "• 消費者保護法第19條\n"
                "• 勞動基準法第38條"
            )
            await send_reply(reply_token, response)
            return

        # 直接輸入法條格式，自動套用結構化格式
        if LAW_PATTERN.search(user_message):
            await handle_law_query(reply_token, user_message)
            return

        # 一般訊息處理
        route = await route_intent(user_message)
        skill = route.get("skill", "general")
        need_rag = route.get("need_rag", False)
        rag_categories = route.get("rag_categories", [])

        print(f"Route: skill={skill}, need_rag={need_rag}, categories={rag_categories}")

        context = ""
        keywords = ["地址", "電話", "哪裡", "諮詢", "公所", "法扶", "法律扶助", "據點"]
        if need_rag or any(kw in user_message for kw in keywords):
            context = await retrieve_context(user_message, rag_categories if rag_categories else ["legal"])
            print(f"RAG context length={len(context)}")

        response = await generate_response(skill, user_message, context)
        await send_reply(reply_token, response)

    except Exception as e:
        print(f"Error: {e}")
        await send_reply(reply_token, "系統暫時無法處理，請稍後再試。")

@router.post("/webhook")
async def webhook(request: Request):
    body = await request.body()
    signature = request.headers.get("X-Line-Signature", "")
    hash = hmac.new(
        settings.line_channel_secret.encode("utf-8"),
        body,
        hashlib.sha256
    ).digest()
    expected = base64.b64encode(hash).decode("utf-8")
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=400, detail="Invalid signature")
    data = json.loads(body)
    for event in data.get("events", []):
        if event.get("type") == "message" and event["message"].get("type") == "text":
            reply_token = event.get("replyToken")
            user_message = event["message"]["text"]
            user_id = event["source"]["userId"]
            asyncio.create_task(process_message(reply_token, user_message, user_id))
    return {"status": "ok"}