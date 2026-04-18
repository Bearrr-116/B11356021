# Spec-007: 生成協調器（Answer Contract + 受限敘事）

- Status: Draft
- Owner: RAG Engineer
- Last Updated: 2026-04-18

## 1. 目的

把 [Spec-005](./spec-005-jurisdiction-rule-engine.md) 的風險旗標與 [Spec-006](./spec-006-retrieval-pipeline.md) 的證據清單，組裝成 **兩階段** 回答：

* **Stage 1**：確定性 Answer Contract（純程式／可測試）
* **Stage 2**：受限 LLM 敘事（可關閉；僅在 `generation_mode` 允許時啟用）

## 2. 責任

* 產生 Answer Contract JSON（結構固定）
* 將 `evidence` 映射為可引用段落（含 `citation_key`）
* 呼叫 LLM 產生 Markdown 敘事，並以 prompt 限制其引用
* 寫入 `query_logs.answer_contract` 與 `generation_logs`

## 3. 非責任

* 追加檢索（屬 Spec-006）
* 重新 rerank（屬 Spec-006）

## 4. Stage 1：Answer Contract（九段）

| 段 | 內容 |
| --- | --- |
| A | 使用者問題重述（不得新增事實） |
| B | 檢索到的核心法條候選（Top 3 條文級引用） |
| C | 相關判決摘要候選（Top 3） |
| D | 爭點映射：問題句 → 可能涉及之法律概念（僅使用 evidence 中出現的詞彙庫） |
| E | 仍需補充之事實（來自 Spec-002 `missing_slots` 與 Spec-005 補問） |
| F | 風險揭露（`risk_flags` 人類可讀版本） |
| G | 引用清單（`legal_unit_id` + `citation_key`） |
| H | `generation_mode` 與是否進入 Stage 2 的判斷理由碼 |
| I | 固定欄位 `disclaimer`（免責聲明模板） |

### 4.1 REFUSAL 模式

當 `generation_mode=REFUSAL`：

* 不呼叫 LLM
* `H_markdown` 為 null
* `A~G` 仍完整輸出，用以稽核「為何拒答」

## 5. Stage 2：受限敘事（LLM）

### 5.1 模型參數（預設）

| 參數 | 預設 |
| --- | --- |
| temperature | 0.1 |
| max_tokens | 1200 |

### 5.2 Prompt 硬性規則（必須寫進 system prompt）

1. 只能使用 Answer Contract 中 `G_citations` 對應之文本內容
2. 不得預測案件勝敗、不得建議具體訴訟策略細節（例如「一定會贏」）
3. 不得引入證據未出現的條號或判決字號
4. 若 `risk_flags` 非空，必須在敘事首段提示「需進一步確認之事項」
5. 必須在文末重複 `I_disclaimer`（可縮短為一句，但不得刪除）

### 5.3 降級策略

| 情境 | 行為 |
| --- | --- |
| 無 API Key | 跳過 Stage 2 |
| LLM timeout | 輸出 Stage1 + 提示「無法產生敘事」 |
| LLM 輸出引用不在 `G_citations` | 整段捨棄，改用保守模板（後處理守門） |

## 6. 輸入契約

```json
{
  "raw_query": "string",
  "normalized_query_bundle": {},
  "retrieval": {"evidence": []},
  "rules": {"risk_flags": [], "suggested_questions": [], "generation_mode": "FULL"}
}
```

## 7. 輸出契約（摘要）

```json
{
  "answer_contract": {
    "A_query_restated": "string",
    "B_statute_candidates": [],
    "C_case_candidates": [],
    "D_issue_mapping": [],
    "E_missing_facts": [],
    "F_risk_notes": [],
    "G_citations": [],
    "H_generation": {"mode": "FULL", "stage2_enabled": true, "reason_codes": []},
    "I_disclaimer": "string"
  },
  "H_markdown": "string | null"
}
```

## 8. 驗收要求

* Stage 1 對同一輸入連跑 50 次：JSON canonical hash 必須一致
* Stage 2 啟用時：RAGAS `faithfulness` 門檻見 [Spec-009](./spec-009-evaluation-framework.md)
* `G_citations` 為空時：不得輸出 `H_markdown` 法律結論段落

## 9. 依賴 ADR

* [ADR-003](../adr/ADR-003-hallucination-control.md)
