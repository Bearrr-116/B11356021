# Spec-001: 系統總覽

- Status: Draft
- Owner: RAG Architect
- Last Updated: 2026-04-18

## 1. 目的

定義《法條檢索與案例輔助 RAG 系統》的模組邊界、端到端資料流與非功能需求，作為其他 spec 的根節點。

## 2. 系統定位

本系統為 **法律知識檢索與案例摘要輔助引擎**，不替代律師、不提供個案最終法律意見、不自動產出訴狀或策略結論。

其回答須具備：

* 可追溯引用（法規名稱＋條號；判決摘要之識別欄位）
* 檢索候選排序與信心分數
* 法域風險揭露（管轄、時效、程序事項之「需確認」提示）
* 證據不足時的補問與拒答策略

## 3. 模組總覽

| 模組 | 對應 Spec | 責任 |
| --- | --- | --- |
| Legal Query Normalizer | [Spec-002](./spec-002-legal-query-normalizer.md) | 自然語言 → 條號候選、法規別名、案由標籤、術語展開 |
| Knowledge ETL | [Spec-003](./spec-003-knowledge-etl.md) | 外部資料 → `legal_units`（child）＋ `parent_documents` |
| Legal Unit Schema | [Spec-004](./spec-004-legal-unit-schema.md) | 單元型別、metadata 契約、parent-child 關聯 |
| Jurisdiction Rule Engine | [Spec-005](./spec-005-jurisdiction-rule-engine.md) | 風險旗標、補問模板、候選法條／判決加減分 |
| Retrieval Pipeline | [Spec-006](./spec-006-retrieval-pipeline.md) | Hybrid 召回、parent 還原、rerank、輸出 Top-K 證據 |
| Generation Orchestrator | [Spec-007](./spec-007-generation-orchestrator.md) | Answer Contract（結構化）＋ 受限 LLM 敘事 |
| Storage | [Spec-008](./spec-008-storage-schema.md) | Qdrant、OpenSearch、原文儲存、查詢日誌 |
| Evaluation | [Spec-009](./spec-009-evaluation-framework.md) | 多層指標、Golden Set、離線／線上監控 |
| API | [Spec-010](./spec-010-api-contracts.md) | REST／MCP Tools 介面 |

## 4. 端到端資料流

```
User Query (natural language)
      │
      ▼
[Spec-002] Legal Query Normalizer
  └─→ normalized_query, article_hints, law_aliases, case_intent_tags
      │
      ▼
[Spec-006] Retrieval Pipeline
  ├─ BM25（OpenSearch：條號、法規名、專有術語）
  ├─ Dense（Qdrant：語義、爭點敘述）
  └─ Parent-Document Reconstruction
  └─→ evidence_units (ranked, with scores)
      │
      ▼
[Spec-005] Jurisdiction Rule Engine
  └─→ risk_flags, suggested_questions, score_adjustments
      │
      ▼
[Spec-007] Generation Orchestrator
  ├─ Stage 1: Answer Contract（JSON，確定性／可測試）
  └─ Stage 2: Markdown synthesis（LLM，受限於已檢索證據）
      │
      ▼
Persist to query_logs / retrieval_logs / generation_logs
      │
      ▼
[Spec-009] Offline Evaluation（Golden Set / RAGAS / TruLens）
```

## 5. 向量化邊界（作業要求明示）

| 階段 | 邊界前／後 | 說明 |
| --- | --- | --- |
| Ingest → Clean → Chunk → Annotate | **向量化之前** | 仍屬非結構／半結構文本處理；產出 `legal_text_for_embed` 與 metadata |
| Embed → Index | **向量化之後** | 進入向量空間與近似搜尋；payload 寫入向量資料庫 |

**Rerank 介入點**：在 Hybrid 召回合併去重後、進入 LLM 之前（見 [Spec-006 §6](./spec-006-retrieval-pipeline.md)）。

## 6. 非功能需求

### 6.1 確定性（Determinism）

* Spec-002 / Spec-005 / Spec-006 的核心排序與閾值邏輯在相同輸入、相同索引版本下必須可重現
* Spec-007 Stage 1（Answer Contract）必須完全由程式組裝，不得依賴 LLM
* Spec-007 Stage 2 允許非確定性，但其引用集合不得超出 Stage 1 所列 `evidence_unit_ids`

### 6.2 可追溯性（Traceability）

* 每個出現在答案中的法條主張，必須對應至少一筆 `legal_unit_id`
* `retrieval_logs` 必須記錄：BM25 query、vector query、fusion 分數、rerank 分數
* `query_logs` 必須記錄：模型名稱、latency、拒答原因碼

### 6.3 可演化性（Evolvability）

* `legal_unit_id` 採穩定命名規則（hash 來源＋條號＋版本），法規修訂時以**新版本**追加，不覆寫舊向量（利於審計與回放評估）
* metadata 採可擴充 JSON／payload 欄位，新增欄位不破壞既有索引讀取

### 6.4 可觀測性（Observability）

* 各子階段（normalize / bm25 / vector / rerank / llm）分別計時
* 健康檢查需揭露：OpenSearch cluster、Qdrant、embedding service、LLM gateway（見 [Spec-010](./spec-010-api-contracts.md)）

## 7. 非功能需求：效能（SLO）

| 指標 | 目標 | 量測方式 |
| --- | --- | --- |
| API P95 Latency | ≤ 2.0s | 含檢索＋rerank＋Stage1；Stage2 可選非同步 |
| 檢索子系統 P95 | ≤ 600ms | 不含 LLM；seed 規模見 [Spec-011](./spec-011-roadmap-and-deliverables.md) |
| 索引重建 | Phase 1 內可完成 | 全量重建 < 4h（可平行化） |

## 8. 安全邊界

| 要求 | 強制方 |
| --- | --- |
| 禁止無證據的法律結論 | Spec-007 Prompt + Stage1 證據列表為空時拒答 |
| 禁止臆測判決結果或勝敗 | Spec-005 高風險模板 + Spec-007 |
| 個資最小化 | Spec-003 去識別化；不儲存當事人完整姓名與身分證字號 |
| 必附免責聲明 | Spec-007 固定 `disclaimer` 欄位 |

## 9. 非責任範圍

* 正式法律意見書、訴訟策略、和解金評估
* 即時連線官方資料庫（MVP 以批次同步為主）
* 跨法域自動適用（除非使用者明確指定法域）

## 10. 驗收要求（期中）

* `docs/specs` 內 Spec-001～011 齊備且互相引用一致
* `docs/architecture` 圖示清楚標出：ETL、embedding、向量拓撲、Hybrid、parent-child、rerank 介入點
* Golden Set 規格與評估流程可執行描述完整（見 [Spec-009](./spec-009-evaluation-framework.md)）

## 11. 依賴 ADR

* [ADR-001](../adr/ADR-001-embedding-model.md)
* [ADR-002](../adr/ADR-002-retrieval-strategy.md)
* [ADR-003](../adr/ADR-003-hallucination-control.md)
