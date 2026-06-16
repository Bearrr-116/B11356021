import os
import hashlib
from dotenv import load_dotenv
load_dotenv()

from supabase import create_client

SUPABASE_URL = os.environ["SUPABASE_URL"]
SUPABASE_KEY = os.environ["SUPABASE_SERVICE_ROLE_KEY"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

LAW_FILES = [
    {"file": "docs/民法.md", "category": "legal"},
    {"file": "docs/消費者保護法.md", "category": "rights"},
    {"file": "docs/勞動基準法.md", "category": "rights"},
    {"file": "docs/刑法.md", "category": "legal"},
    {"file": "docs/民事訴訟法.md", "category": "legal"},
    {"file": "docs/法律諮詢資源.md", "category": "legal"},
    {"file": "docs/法律扶助基金會.md", "category": "legal"},
    {"file": "docs/地方法院.md", "category": "legal"},
]

def chunk_text(text: str, chunk_size: int = 3000) -> list:
    chunks = []
    lines = text.split("\n")
    current = ""
    for line in lines:
        if len(current) + len(line) > chunk_size and current:
            chunks.append(current.strip())
            current = line
        else:
            current += "\n" + line
    if current.strip():
        chunks.append(current.strip())
    return chunks

def ingest_file(file_path: str, category: str):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    chunks = chunk_text(content)
    print(f"{file_path}：{len(chunks)} 個段落")
    
    success = 0
    for chunk in chunks:
        if len(chunk) < 20:
            continue
        content_hash = hashlib.md5(chunk.encode()).hexdigest()
        try:
            supabase.table("private_knowledge").upsert({
                "content": chunk,
                "content_hash": content_hash,
                "category": category,
                "source": file_path,
            }, on_conflict="content_hash").execute()
            success += 1
        except Exception as e:
            print(f"錯誤：{e}")
    
    print(f"成功匯入 {success} 個段落")

if __name__ == "__main__":
    for law in LAW_FILES:
        print(f"\n匯入：{law['file']}")
        ingest_file(law["file"], law["category"])
    print("\n完成！")