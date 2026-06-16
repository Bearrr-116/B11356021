import asyncio
import os
import httpx
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json",
}

RICH_MENU = {
    "size": {"width": 2500, "height": 1686},
    "selected": True,
    "name": "法律選單",
    "chatBarText": "法律服務選單",
    "areas": [
        {
            "bounds": {"x": 0, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "法律諮詢據點查詢"}
        },
        {
            "bounds": {"x": 833, "y": 0, "width": 834, "height": 843},
            "action": {"type": "uri", "uri": "https://www.laf.org.tw"}
        },
        {
            "bounds": {"x": 1667, "y": 0, "width": 833, "height": 843},
            "action": {"type": "message", "text": "地方法院據點查詢"}
        },
        {
            "bounds": {"x": 0, "y": 843, "width": 833, "height": 843},
            "action": {"type": "message", "text": "法律扶助基金會據點查詢"}
        },
        {
            "bounds": {"x": 833, "y": 843, "width": 834, "height": 843},
            "action": {"type": "message", "text": "法條查詢"}
        },
        {
            "bounds": {"x": 1667, "y": 843, "width": 833, "height": 843},
            "action": {"type": "uri", "uri": "tel:0241285182"}
        },
    ],
}


async def create_rich_menu():
    async with httpx.AsyncClient() as client:
        r = await client.post(
            "https://api.line.me/v2/bot/richmenu",
            headers=HEADERS,
            json=RICH_MENU,
        )
        data = r.json()
        print(f"建立選單：{data}")

        rich_menu_id = data.get("richMenuId")
        if not rich_menu_id:
            print("建立失敗")
            return

        r2 = await client.post(
            f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
            headers=HEADERS,
        )
        print(f"設為預設：{r2.status_code}")
        print(f"Rich Menu ID: {rich_menu_id}")
        return rich_menu_id


asyncio.run(create_rich_menu())