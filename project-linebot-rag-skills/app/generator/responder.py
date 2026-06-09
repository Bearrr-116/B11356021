from app.config import settings
from app.ai.factory import get_openai_client

SKILL_PROMPTS = {
    "legal_advisor": "你是一個專業法律顧問，專長台灣法律、民法、刑法、勞動法與契約法。回答要引用相關法條，給出具體建議，並提醒用戶諮詢專業律師。",
    "contract_reviewer": "你是一個契約審查專家，專長合約條款分析、風險識別與修改建議。回答要指出潛在風險條款，給出具體修改建議。",
    "legal_research": "你是一個法律研究員，專長判例分析、法規查詢與法律趨勢。回答要有條理，引用相關法規與判例。",
    "rights_advisor": "你是一個權益保障顧問，專長消費者保護、勞工權益與基本人權。回答要站在當事人立場，給出維權步驟。",
    "general": "你是一個友善的 AI 助手，回答簡潔清楚。",
}

async def generate_response(skill: str, message: str, context: str = "") -> str:
    client = get_openai_client()
    system_prompt = SKILL_PROMPTS.get(skill, SKILL_PROMPTS["general"])
    
    user_content = message
    if context:
        user_content = f"參考資料：\n{context}\n\n用戶問題：{message}"
    
    response = await client.chat.completions.create(
        model=settings.generator_model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content}
        ],
    )
    return response.choices[0].message.content