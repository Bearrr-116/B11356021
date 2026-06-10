import httpx
import json
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

async def create_rich_menu():
    rich_menu = {
        "size": {"width": 2500, "height": 843},
        "selected": True,
        "name": "法律選單",
        "chatBarText": "法律服務選單",
        "areas": [
            {
                "bounds": {"x": 0, "y": 0, "width": 833, "height": 421},
                "action": {"type": "message", "text": "民法相關問題"}
            },
            {
                "bounds": {"x": 833, "y": 0, "width": 834, "height": 421},
                "action": {"type": "message", "text": "勞工權益問題"}
            },
            {
                "bounds": {"x": 1667, "y": 0, "width": 833, "height": 421},
                "action": {"type": "message", "text": "消費者保護問題"}
            },
            {
                "bounds": {"x": 0, "y": 421, "width": 833, "height": 422},
                "action": {"type": "message", "text": "刑法相關問題"}
            },
            {
                "bounds": {"x": 833, "y": 421, "width": 834, "height": 422},
                "action": {"type": "message", "text": "契約審查問題"}
            },
            {
                "bounds": {"x": 1667, "y": 421, "width": 833, "height": 422},
                "action": {"type": "message", "text": "我需要法律諮詢"}
            },
        ]
    }

    async with httpx.AsyncClient() as client:
        # 建立 Rich Menu
        r = await client.post(
            "https://api.line.me/v2/bot/richmenu",
            headers=HEADERS,
            json=rich_menu
        )
        data = r.json()
        print(f"建立選單：{data}")
        rich_menu_id = data.get("richMenuId")

        if not rich_menu_id:
            print("建立失敗")
            return

        # 設為預設選單
        r2 = await client.post(
            f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
            headers=HEADERS
        )
        print(f"設為預設：{r2.status_code}")
        print(f"Rich Menu ID: {rich_menu_id}")
        print("完成！但還需要上傳選單圖片")

import asyncio
asyncio.run(create_rich_menu())