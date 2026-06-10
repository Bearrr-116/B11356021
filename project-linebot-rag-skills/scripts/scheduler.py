import asyncio
import schedule
import time
import random
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]
TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

LAW_TIPS = [
    "📌 法律小知識：民法第184條規定，因故意或過失不法侵害他人權利者，須負損害賠償責任。",
    "📌 法律小知識：勞基法規定，每週工時不得超過40小時，加班每小時須加給1/3以上工資。",
    "📌 法律小知識：消保法規定，網路購物享有7天鑑賞期，可無條件退貨。",
    "📌 法律小知識：刑法第320條規定，竊盜罪最高可處5年有期徒刑。",
    "📌 法律小知識：租屋押金依法不得超過2個月租金，房東須在退租後返還。",
    "📌 法律小知識：勞基法規定，雇主不得任意解僱員工，須符合法定事由並給予資遣費。",
    "📌 法律小知識：民事訴訟法規定，一般民事案件時效為15年，侵權行為為2年。",
]

async def push_to_all(message: str):
    result = supabase.table("line_users").select("user_id").eq("subscribed", True).execute()
    users = result.data
    print(f"推播給 {len(users)} 位使用者：{message[:20]}...")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {TOKEN}",
    }

    async with httpx.AsyncClient() as client:
        for user in users:
            await client.post(
                "https://api.line.me/v2/bot/message/push",
                headers=headers,
                json={
                    "to": user["user_id"],
                    "messages": [{"type": "text", "text": message}]
                }
            )

def job():
    tip = random.choice(LAW_TIPS)
    asyncio.run(push_to_all(tip))

# 每天早上 8 點推播
schedule.every().day.at("08:00").do(job)

print("定時推播已啟動，每天 08:00 發送法律小知識...")
print("按 Ctrl+C 停止")

while True:
    schedule.run_pending()
    time.sleep(60)