# Spec-005: 法域規則引擎（Jurisdiction Rule Engine）

- Status: Draft
- Owner: Legal Product / Compliance
- Last Updated: 2026-04-18

## 1. 目的

在檢索結果進入生成前，對「高風險、強依賴事實、或易誤導」的法律查詢進行 **規則化調整**：

* 對特定證據單元加減分（避免錯誤類案）
* 加上 `risk_flags` 與 `suggested_questions`
* 在證據不足時觸發拒答或降級輸出

本模組對齊中醫專案中的 Rule Engine 角色，但規則內容改為 **法域風險與程序敏感度**。

## 2. 責任

* 讀取 [Spec-002](./spec-002-legal-query-normalizer.md) 的 `missing_slots`
* 讀取 [Spec-006](./spec-006-retrieval-pipeline.md) 的候選證據列表
* 輸出：
  * `score_adjustments: {legal_unit_id: delta}`
  * `risk_flags: string[]`
  * `suggested_questions: string[]`
  * `generation_mode: FULL | CONSERVATIVE | REFUSAL`

## 3. 非責任

* 重新檢索（屬 Spec-006）
* 自然語言敘事（屬 Spec-007）

## 4. 規則表（MVP 範例）

### R-001：程序高敏感

**條件**：`case_intent_tags` 包含 `程序問題` 且 `missing_slots` 含「管轄法院層級」

**動作**：

* `generation_mode = CONSERVATIVE`
* `risk_flags += ["PROCEDURE_FACT_DEPENDENT"]`
* `suggested_questions += ["請問案件目前進行到哪一審？是否已有確定判決？"]`

### R-002：時效／除斥期間

**條件**：`legal_issue_tags` 命中 `STATUTE_OF_LIMITATIONS` 或使用者文本含「多久內要提」

**動作**：

* `risk_flags += ["LIMITATION_FACT_SENSITIVE"]`
* 對所有 `CASE_HOLDING` 類型證據：`score_adjustments -= 0.05`（避免過度依賴個案見解）
* `suggested_questions += ["請提供可確定起算日的關鍵時間點（例如知悉日、終止日）。"]`

### R-003：證據不足

**條件**：候選證據最大 `rerank_score < 0.42`

**動作**：

* `generation_mode = REFUSAL`
* `suggested_questions += ["請用更具体的法律用语或條號（例如：民法第184條第1項前段）重試。"]`

### R-004：個資疑慮

**條件**：`raw_query` 命中身分證字號、完整手機號碼 regex

**動作**：

* 立即中止 pipeline，回傳錯誤碼 `PII_DETECTED`（見 [Spec-010](./spec-010-api-contracts.md)）

## 5. 輸入契約

```json
{
  "normalized_query_bundle": {},
  "retrieval_candidates": [
    {"legal_unit_id": "string", "unit_type": "STATUTE_CHILD", "rerank_score": 0.0}
  ]
}
```

## 6. 輸出契約

```json
{
  "score_adjustments": {"lu_xxx": -0.05, "lu_yyy": 0.0},
  "risk_flags": ["LIMITATION_FACT_SENSITIVE"],
  "suggested_questions": ["..."],
  "generation_mode": "CONSERVATIVE"
}
```

## 7. 驗收要求

* 規則表需有版本號 `ruleset_version`；變更需附 migration note
* 對 20 條合成測試輸入，規則觸發結果必須 100% 可重現
* `REFUSAL` 不得進入 Spec-007 Stage 2（僅允許固定模板短答）

## 8. 依賴 ADR

* [ADR-003](../adr/ADR-003-hallucination-control.md)
