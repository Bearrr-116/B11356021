# Spec-003a: ETL 標註 Prompt 模板（Legal Unit Metadata）

- Status: Draft
- Owner: Prompt Engineer
- Last Updated: 2026-04-18

## 1. 目的

定義 ETL 階段（[Spec-003 §5.4](./spec-003-knowledge-etl.md)）使用 LLM 協助標註時的 **系統提示、上下文邊界、輸出 schema**，確保：

* 輸出可機器驗證（JSON Schema）
* 不引入法效判斷（僅做「標籤與摘要」）
* 與向量品質相關之欄位穩定（`legal_issue_tags` 等）

## 2. 系統提示（System）

```
你是臺灣法學資料標註助理。你的任務是把給定的法律文本片段，標註成結構化 metadata。
硬性規則：
1) 只能根據輸入文本與已提供的來源欄位推理，不得引用外部法源或補全世界觀。
2) 不得輸出法律意見、勝訴策略、或對當事人行為合法與否下結論。
3) 所有標籤必須來自允許的封閉集合；若不确定，使用 "UNKNOWN" 並降低 confidence。
4) 輸出必須是單一 JSON 物件，符合指定 schema，不得包含 Markdown 围栏。
```

## 3. 使用者提示模板（User）

```
[CONTEXT]
source_type: {{source_type}}          # statute | interpretation | case_summary
authority_level: {{authority_level}} # 0-100
law_name: {{law_name | null}}
article_no: {{article_no | null}}
clean_markdown_excerpt:
---
{{clean_markdown_excerpt}}
---

[TASK]
請產生下列欄位：
- legal_domain_tags: 陣列，最多 3 個，封閉集合：{{ALLOWED_DOMAINS}}
- legal_issue_tags: 陣列，最多 5 個，封閉集合：{{ALLOWED_ISSUES}}
- holding_summary: 字串，<= 120 字，僅在 source_type=case_summary 時必填；其他填 null
- ambiguity_notes: 字串陣列，描述文本內在的不清楚處（例如引用條號不完整）
- confidence: 0~1

[SCHEMA_VERSION]
{{schema_version}}
```

## 4. 輸出 JSON Schema（摘要）

```json
{
  "type": "object",
  "required": ["legal_domain_tags", "legal_issue_tags", "holding_summary", "ambiguity_notes", "confidence", "schema_version"],
  "properties": {
    "legal_domain_tags": {"type": "array", "items": {"type": "string"}, "maxItems": 3},
    "legal_issue_tags": {"type": "array", "items": {"type": "string"}, "maxItems": 5},
    "holding_summary": {"type": ["string", "null"], "maxLength": 200},
    "ambiguity_notes": {"type": "array", "items": {"type": "string"}},
    "confidence": {"type": "number", "minimum": 0, "maximum": 1},
    "schema_version": {"type": "string"}
  },
  "additionalProperties": false
}
```

## 5. 封閉集合範例（MVP）

`ALLOWED_DOMAINS` 範例：

* `CIVIL_LAW`
* `CRIMINAL_LAW`
* `ADMIN_LAW`
* `LABOR_LAW`
* `COMPANY_LAW`
* `UNKNOWN`

`ALLOWED_ISSUES` 範例：

* `CONSTITUENT_ELEMENTS`（構成要件）
* `CAUSATION`（因果關係）
* `DAMAGES`（損害賠償）
* `BURDEN_OF_PROOF`（舉證責任）
* `GOOD_FAITH_THIRD_PARTY`（善意第三人）
* `STATUTE_OF_LIMITATIONS`（時效）
* `PROCEDURE`（程序）
* `UNKNOWN`

## 6. 驗收要求

* 100 筆標註樣本中，JSON Schema 失敗率 = 0
* 人工抽檢 20 筆：`holding_summary` 不得包含未在文本出現的具體數字或日期
* 對 L0 法條：`holding_summary` 必須為 null（避免把條文改寫成判決要旨）

## 7. 依賴

* [Spec-003](./spec-003-knowledge-etl.md)
* [Spec-004](./spec-004-legal-unit-schema.md)
