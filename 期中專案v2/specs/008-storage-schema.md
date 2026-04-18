# Spec-008: 儲存 Schema（Qdrant + OpenSearch + Logs）

- Status: Draft
- Owner: Data Platform / DBA
- Last Updated: 2026-04-18

## 1. 目的

定義向量檢索、關鍵字檢索、原文留存與稽核日誌所需的儲存層，使 [Spec-004](./spec-004-legal-unit-schema.md)、[Spec-006](./spec-006-retrieval-pipeline.md)、[Spec-007](./spec-007-generation-orchestrator.md) 可落地實作。

## 2. 執行環境

* Qdrant 1.x（向量 + payload filter）
* OpenSearch 2.x（BM25；中文 analyzer 需可配置）
* Object Storage（S3 相容）或檔案系統：保存 `raw_bytes` / `clean_markdown` 大物件
* PostgreSQL（建議）或 ClickHouse：query／retrieval logs（二選一；以下以 PostgreSQL 敘述）

## 3. Qdrant：Collections 拓撲

### 3.1 `legal_units_vectors`（主 collection）

* `vector_size`：與 embedding 模型一致（BGE-M3 以實際輸出為準）
* `distance`：Cosine（預設）

**Payload 欄位（最小集合）**：

| payload key | 用途 |
| --- | --- |
| `legal_unit_id` | 主鍵 |
| `unit_type` | filter |
| `law_name` / `article_no` / `law_version_id` | filter + 顯示 |
| `authority_level` | filter |
| `legal_domain_tags` | filter |
| `legal_issue_tags` | filter |
| `citation_key` | 顯示／debug |
| `parent_unit_id` | parent 還原 |
| `is_active` | filter |
| `clean_markdown_excerpt` | 列表預覽（可截斷） |

> 長文本全文放物件儲存；Qdrant 只存 excerpt 以降低 payload 成本。

### 3.2 索引策略

* 對常用 filter 組合建立 payload index（`law_version_id`, `unit_type`, `is_active`）
* 定期 snapshot + 版本化重建（對齊法規修訂）

## 4. OpenSearch：Index Mapping（`legal_units_bm25`）

**建議欄位**：

| 欄位 | 說明 |
| --- | --- |
| `legal_unit_id` | keyword（與向量庫 join） |
| `citation_key` | text + keyword multi-field |
| `law_name` | keyword + text |
| `article_no` | integer |
| `clean_markdown` | text（BM25） |
| `legal_issue_tags` | keyword[] |

**Analyzer**：

* 預設：`icu_analyzer` 或 `smartcn`（依部署環境選擇）
* 必須提供「條號數字不被過度切分」的測試用例（見 Spec-009）

## 5. PostgreSQL：Logs

### 5.1 `query_logs`

| 欄位 | 型別 |
| --- | --- |
| `query_id` | uuid |
| `raw_query` | text |
| `normalized_json` | jsonb |
| `answer_contract` | jsonb |
| `model_name` | text |
| `latency_ms` | int |
| `created_at` | timestamptz |

### 5.2 `retrieval_logs`

| 欄位 | 型別 |
| --- | --- |
| `query_id` | uuid |
| `stage` | text（`bm25`/`vec`/`fusion`/`rerank`） |
| `payload` | jsonb |

## 6. 資料治理

* 禁止硬刪除知識單元：使用 `is_active=false`
* `law_version_id` 變更必須新增資料，不得原地覆寫向量與 BM25 文件（保留審計）
* 判決資料必須通過去識別化檢查（regex + 人工抽樣）

## 7. 驗收要求

* 以 1k `legal_units` 種子資料：P95 檢索延遲滿足 [Spec-001](./spec-001-system-overview.md)
* `legal_unit_id` 在 Qdrant 與 OpenSearch 必須可 join 成功率 100%
* snapshot 可還原至指定 `law_version_id` 集合

## 8. 依賴 ADR

* [ADR-001](../adr/ADR-001-embedding-model.md)
* [ADR-002](../adr/ADR-002-retrieval-strategy.md)
