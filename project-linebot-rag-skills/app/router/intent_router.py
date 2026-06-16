import json
from app.config import settings
from app.ai.factory import get_openai_client

ROUTE_PROMPT = """
你是一個意圖分類器。根據用戶訊息，判斷應該使用哪個 skill。

可用的 skill：
- legal_advisor：一般法律問題、法條解釋、法律建議
- contract_reviewer：合約審查、條款分析、契約風險
- legal_research：判例查詢、法規研究、法律趨勢
- rights_advisor：消費者保護、勞工權益、基本人權
- general：其他一般問題

回覆只能是 JSON 格式：
{"skill": "skill名稱", "need_rag": true或false, "rag_categories": ["類別"]}

need_rag 判斷規則：
- 問到法律諮詢地點、地址、電話、服務時間 → need_rag: true
- 問到特定法條內容 → need_rag: true
- 問到法律資源、去哪裡諮詢 → need_rag: true
- 一般法律概念問題 → need_rag: false

rag_categories 從以下選擇：legal, contract, case_law, rights, general
"""

async def route_intent(message: str) -> dict:
    client = get_openai_client()
    response = await client.chat.completions.create(
        model=settings.router_model,
        messages=[
            {"role": "system", "content": ROUTE_PROMPT},
            {"role": "user", "content": message}
        ],
        response_format={"type": "json_object"},
    )
    text = response.choices[0].message.content
    try:
        return json.loads(text)
    except Exception:
        return {"skill": "general", "need_rag": False, "rag_categories": []}