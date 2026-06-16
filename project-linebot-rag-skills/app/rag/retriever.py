import re
from app.storage.supabase_client import get_supabase

CITY_KEYWORDS = [
    "台北", "臺北", "新北", "桃園", "台中", "臺中", "台南", "臺南",
    "高雄", "基隆", "宜蘭", "花蓮", "台東", "臺東", "屏東", "嘉義",
    "雲林", "彰化", "南投", "苗栗", "新竹", "澎湖", "金門", "連江",
]

LEGAL_KEYWORDS = [
    "法律諮詢", "法扶", "法律扶助", "調解", "公所", "地址", "電話",
    "服務時間", "諮詢地點", "免費諮詢", "法律援助", "律師",
    "民法", "刑法", "勞基法", "消保法", "民事訴訟", "消費者保護",
    "加班費", "特休", "押金", "合約", "契約", "損害賠償", "侵權",
    "竊盜", "詐騙", "傷害", "妨害名譽",
]

async def retrieve_context(query: str, categories: list[str], top_k: int = 5) -> str:
    supabase = get_supabase()

    try:
        results = []
        seen = set()

        # 建立搜尋變體（處理法條格式）
        search_queries = [query]
        law_match = re.search(r'第\s*(\d+(?:-\d+)?)\s*條', query)
        if law_match:
            num = law_match.group(1)
            search_queries.append(f"第 {num} 條")
            search_queries.append(f"第{num}條")
            search_queries.append(f"{num}條")
            search_queries.append(num)

        print(f"搜尋變體：{search_queries}")

        # 先用所有變體搜尋
        for q in search_queries:
            r = supabase.table("private_knowledge") \
                .select("content, source") \
                .ilike("content", f"%{q}%") \
                .limit(top_k) \
                .execute()

            if r.data:
                for item in r.data:
                    content = item.get("content", "")
                    if content not in seen:
                        seen.add(content)
                        results.append(item)

        # 再用關鍵字補充搜尋
        if len(results) < top_k:
            matched_keywords = []
            for kw in CITY_KEYWORDS + LEGAL_KEYWORDS:
                if kw in query:
                    matched_keywords.append(kw)

            if not matched_keywords:
                matched_keywords = [query[:6]]

            print(f"搜尋關鍵字：{matched_keywords}")

            for keyword in matched_keywords[:3]:
                r = supabase.table("private_knowledge") \
                    .select("content, source") \
                    .ilike("content", f"%{keyword}%") \
                    .limit(top_k) \
                    .execute()

                if r.data:
                    for item in r.data:
                        content = item.get("content", "")
                        if content not in seen:
                            seen.add(content)
                            results.append(item)

        results = results[:top_k]

        if not results:
            print("RAG 搜尋無結果")
            return ""

        context_parts = []
        for item in results:
            source = item.get("source", "未知來源")
            content = item.get("content", "")
            context_parts.append(f"【來源：{source}】\n{content}")

        return "\n\n".join(context_parts)

    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""