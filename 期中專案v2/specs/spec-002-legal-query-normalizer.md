# Spec-002: 法律查詢正規化器（Legal Query Normalizer）

- Status: Draft
- Owner: NLP / Legal Tech Engineer
- Last Updated: 2026-04-18

## 1. 目的

將使用者自然語言查詢轉為 **利於檢索的結構化訊號**：條號提示、法規別名、案由標籤、可展開之法律術語、以及 BM25／Dense 各自的最佳查詢字串。

本模組是法律 RAG 的「前網關」，目標是降低 **漏召回**（尤其是條號與專有名词）與 **跨條文語意漂移**。

## 2. 責任

* 抽取／推測 `article_hints`（例如：民法 184、民法第一八四條、第184條）
* 對常見法規簡稱做 `law_alias_resolution`（例如：「消保法」→《消費者保護法》）
* 輸出 `fts_query`：保留條號數字、法規全名、關鍵術語；去除口語贅字
* 輸出 `dense_query`：保留完整爭點敘述，必要時補上「構成要件／效果／舉證責任」等中性提示詞（不得引入未提供事實）
* 產出 `case_intent_tags`：`判決查詢` / `要件分析` / `程序問題` / `定義查詢` 等粗分類
* 標註 `missing_slots`：管轄、時間點、契約類型、主體身份等影響適用之資訊是否不足

## 3. 非責任

* 實際檢索與重排（屬 [Spec-006](./spec-006-retrieval-pipeline.md)）
* 法效價值判斷（屬 [Spec-005](./spec-005-jurisdiction-rule-engine.md) 與 [Spec-007](./spec-007-generation-orchestrator.md)）

## 4. 輸入契約

```json
{
  "raw_query": "string",
  "user_locale": "zh-Hant",
  "jurisdiction_default": "TW",
  "session_id": "uuid | null"
}
```

## 5. 輸出契約

```json
{
  "normalized_query": "string",
  "fts_query": "string",
  "dense_query": "string",
  "article_hints": [
    {"law_guess": "民法", "article_no": 184, "confidence": 0.74}
  ],
  "law_aliases": [
    {"alias": "消保法", "resolved_name": "消費者保護法", "confidence": 0.91}
  ],
  "case_intent_tags": ["要件分析"],
  "missing_slots": ["管轄法院層級", "行為發生日期"],
  "expansions_applied": [
    {"term": "侵權行為", "expanded_to": ["民法第184條脈絡用語"], "source": "legal_alias_table@v3"}
  ]
}
```

## 6. 規則優先序（Determinism）

1. **明確條號 regex** 命中者優先於模型推測
2. **法規別名表**（curated）優先於 LLM 產生的法規名猜測
3. 若 regex 與 LLM 衝突：採 regex，並在 `warnings` 記錄衝突（供 log）

## 7. LLM 使用邊界（可選）

MVP 可用規則式完成 70% 查詢型態；以下情境允許呼叫 LLM 做 slot-filling：

* 使用者以故事性敘述提問，無任何條號線索
* 需從長文中抽取「可能爭點」

LLM 輸出必須通過 JSON Schema 驗證；不得直接作為答案文本。

## 8. 驗收要求

* 內建 30 條測試查詢（見 [../examples/sample-queries.md](../examples/sample-queries.md)），`article_hints` 召回率 ≥ 0.85（相對標註答案）
* `law_aliases` 對 curated 別名表準確率 ≥ 0.95
* 同一輸入連跑 20 次：結構欄位（條號列表排序後）必須一致

## 9. 依賴 ADR

* [ADR-002](../adr/ADR-002-retrieval-strategy.md)（為何需要獨立 fts_query 與 dense_query）
