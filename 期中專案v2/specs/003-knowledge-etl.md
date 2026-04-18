# Spec-003: 知識 ETL（法規／函釋／判決摘要）

- Status: Draft
- Owner: Data Engineer
- Last Updated: 2026-04-18

## 1. 目的

將外部法律文本（法規、函釋、判決書公開資料）轉為 [Spec-004](./spec-004-legal-unit-schema.md) 定義之 `legal_units` 與 `parent_documents`，並在進入向量索引前完成品質閘控管。

## 2. 責任

六階段管線，每階段有明確狀態轉移與品質閘：

1. **Ingest** — 抓取來源 → `source_documents(ingestion_status='pending')`
2. **Clean** — 去除頁首頁尾、浮水印、目錄噪音；統一全形半形與空白
3. **Chunk** — 以 **法條結構與 Markdown 標題** 為主切分；必要時語義二次切分
4. **Annotate** — LLM 或規則式補齊 metadata（見 [Spec-003a](./spec-003a-etl-prompt-template.md)）
5. **Embed** — 由 `embedding_text` 產生向量（模型見 [ADR-001](../adr/ADR-001-embedding-model.md)）
6. **Validate** — JSON Schema + 規則檢查 + 抽樣人工覆核 → `embedded`

## 3. 非責任

* Schema 演進治理流程（屬 Spec-004 的變更紀錄）
* 線上檢索與 rerank（屬 Spec-006）
* 使用者查詢正規化（屬 Spec-002）

## 4. 來源分層（資料源策略）

| 層 | 類型 | authority_level（0–100） | 用途 |
| --- | --- | --- | --- |
| L0 | 官方全國法規資料庫正文 | 98–100 | 條文主體、版本基準 |
| L1 | 主管機關函釋／裁罰基準／行政規則 | 85–95 | 適用爭議、構成要件補充 |
| L2 | 判決書公開本（經摘要化與去識別） | 70–85 | 實務見解、類案整理 |
| L3 | 教科書／專論／部落格（可選） | 40–70 | 教學解釋；預設 **不進入** MVP 主索引 |

## 5. 階段契約

### 5.1 Ingest

| 輸入 | 輸出 |
| --- | --- |
| URL／檔案／API dump | `source_documents` 一筆；`raw_bytes` 或 `raw_text` 完整保留 |

### 5.2 Clean

| 輸入 | 輸出 |
| --- | --- |
| `raw_*` | `clean_markdown`（保留 `##` 章節與條號行） |

**法規特有清洗**：

* 條號行正規化：`第184條` / `第一百八十四條` → 機器可解析欄位 `article_no=184`
* 項次款目：拆為子結構欄位，避免被切到不同 chunk 時失聯

### 5.3 Chunk

切段服從 **法律文本結構** 而非字數：

* **法條**：優先「一條一 parent」；長條文再拆 child（每款、每項可為 child）
* **判決摘要**：以「爭點／理由／結論」為段落邊界；程序事實與實體理由盡量分桶
* **函釋**：以「函釋主旨段」為最小原子；附件長表另存 `attachment_ref`

**參數（預設，可環境變數覆寫）**：

* child：`target_tokens` 350–450；`overlap_tokens` 50
* parent：完整章節或整條文（不得小於 child 所屬範圍）

### 5.4 Annotate

由 [Spec-003a](./spec-003a-etl-prompt-template.md) 定義之提示，回填：

* `legal_domain_tags`：民法／刑法／行政法／勞動法…
* `legal_issue_tags`：舉證責任轉換、善意第三人、過失要件…
* `effective_date` / `superseded_by`（若可解析）

### 5.5 Embed

* 輸入欄位必須是 `embedding_text`（通常為：`[UNIT=STATUTE_ARTICLE] [LAW=...] [ARTICLE=...] \n\n 正文`）
* 不得直接對原始 HTML embedding

### 5.6 Validate

| 類型 | 內容 |
| --- | --- |
| 自動 | Schema 通過；向量非 null；parent_id 存在；條號欄位自洽 |
| 人工 | L0 抽樣 ≥ 2%；L2 抽樣 ≥ 10%（因摘要錯誤成本高） |

## 6. Context Injection（影響向量品質的關鍵）

所有 `embedding_text` 必須以結構化標頭開頭（與中醫專案同理，但欄位不同）：

```
[UNIT=STATUTE_CHILD]
[LAW=中華民國民法]
[ARTICLE=184]
[PARAGRAPH=1]
[DOMAIN=CIVIL_LAW]
```

判決摘要：

```
[UNIT=CASE_HOLDING]
[COURT=TIPC]
[YEAR=2023]
[CAUSE=侵權行為損害賠償]
```

## 7. 非結構化 → 向量化邊界（重申）

* **邊界前**：完成到 `embedding_text` 與 metadata
* **邊界後**：呼叫 embedding API／本地推理 → 寫入 Qdrant payload

## 8. 驗收要求

* 任一筆 L0 法條必須能回溯到 `source_documents.id`
* 重跑 ETL 對同一來源需 **idempotent**（以 `content_hash` upsert）
* Parser 對 100 條隨機條文：條號解析成功率 ≥ 98%

## 9. 依賴 ADR

* [ADR-001](../adr/ADR-001-embedding-model.md)
* [ADR-002](../adr/ADR-002-retrieval-strategy.md)（parent-child 與索引欄位設計）
