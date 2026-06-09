import requests
from bs4 import BeautifulSoup
import time
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LAWS = [
    {"name": "民法", "pcode": "B0000001", "category": "legal"},
    {"name": "消費者保護法", "pcode": "J0170001", "category": "rights"},
    {"name": "勞動基準法", "pcode": "N0030001", "category": "rights"},
]

def fetch_law(pcode: str) -> str:
    url = f"https://law.moj.gov.tw/LawClass/LawAll.aspx?pcode={pcode}"
    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers, timeout=30, verify=False)
    soup = BeautifulSoup(response.text, "html.parser")
    
    content = []
    articles = soup.select(".law-article")
    for article in articles:
        text = article.get_text(strip=True)
        if text:
            content.append(text)
    
    if not content:
        # 嘗試其他選擇器
        articles = soup.select("div.ArticleContent")
        for article in articles:
            text = article.get_text(strip=True)
            if text:
                content.append(text)
    
    return "\n\n".join(content)

def save_law(name: str, content: str):
    filename = f"docs/{name}.md"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# {name}\n\n")
        f.write(content)
    print(f"已儲存：{filename}（{len(content)} 字）")

if __name__ == "__main__":
    import os
    os.makedirs("docs", exist_ok=True)
    
    for law in LAWS:
        print(f"抓取：{law['name']}...")
        content = fetch_law(law["pcode"])
        if content:
            save_law(law["name"], content)
        else:
            print(f"警告：{law['name']} 抓取失敗，內容為空")
        time.sleep(2)
    
    print("完成！")