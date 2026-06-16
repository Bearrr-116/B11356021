import httpx
import asyncio
import os
from dotenv import load_dotenv
load_dotenv()

TOKEN = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]

async def upload_rich_menu_image(rich_menu_id: str, image_path: str):
    url = f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "image/jpeg",
    }
    with open(image_path, "rb") as f:
        image_data = f.read()

    async with httpx.AsyncClient() as client:
        r = await client.post(url, headers=headers, content=image_data)
        print(f"上傳結果：{r.status_code}")
        print(r.text)

        if r.status_code == 200:
            # 設為預設選單
            r2 = await client.post(
                f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
                headers={"Authorization": f"Bearer {TOKEN}"},
            )
            print(f"設為預設：{r2.status_code}")
            print("完成！選單已上傳並設為預設")

RICH_MENU_ID = "richmenu-3622663a6072344b87106d4a52ab2708"
IMAGE_PATH = "richmenu.jpg"

asyncio.run(upload_rich_menu_image(RICH_MENU_ID, IMAGE_PATH))