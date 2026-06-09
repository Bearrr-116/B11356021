from app.storage.supabase_client import get_supabase

async def retrieve_context(query: str, categories: list[str], top_k: int = 4) -> str:
    supabase = get_supabase()
    
    try:
        # 全文搜尋
        result = supabase.table("private_knowledge") \
            .select("content, source") \
            .ilike("content", f"%{query}%") \
            .in_("category", categories if categories else ["legal", "contract", "case_law", "rights", "general"]) \
            .limit(top_k) \
            .execute()
        
        if not result.data:
            return ""
        
        context_parts = []
        for item in result.data:
            source = item.get("source", "未知來源")
            content = item.get("content", "")
            context_parts.append(f"【來源：{source}】\n{content}")
        
        return "\n\n".join(context_parts)
    
    except Exception as e:
        print(f"Retrieval error: {e}")
        return ""