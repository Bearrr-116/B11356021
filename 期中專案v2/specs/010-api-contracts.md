# Spec-010: API 契約（REST + MCP Tools 草案）

- Status: Draft
- Owner: Platform Engineer
- Last Updated: 2026-04-18

## 1. 目的

定義對外介面，使教學 demo 可用 `curl` 驗收，並保留與 Cursor MCP 整合的擴充空間。

## 2. 共用原則

* JSON API；錯誤採 HTTP status + `{ "error": { "code": "...", "message": "..." } }`
* 所有成功回應包含 `trace_id`（UUID）
* 預設語言：`zh-Hant`

## 3. REST Endpoints

| Method | Path | 說明 |
| --- | --- | --- |
| GET | `/health` | 子系統狀態 |
| POST | `/v1/legal/query` | 端到端查詢（normalize→retrieve→rules→answer） |
| POST | `/v1/legal/retrieve` | 僅檢索（除錯／消融實驗） |
| POST | `/v1/legal/normalize` | 僅查詢正規化（除錯） |

### 3.1 `/health`

```json
{
  "status": "ok",
  "opensearch": true,
  "qdrant": true,
  "embedding_service": true,
  "llm_gateway": true,
  "ruleset_version": "legal_rules@v1"
}
```

### 3.2 `POST /v1/legal/query`

**Request**

```json
{
  "query": "string",
  "options": {
    "synthesize_markdown": true,
    "top_k": 8,
    "jurisdiction_default": "TW"
  }
}
```

**Response（摘要）**

```json
{
  "trace_id": "uuid",
  "answer_contract": {},
  "markdown": "string | null",
  "latency_ms": {"total": 0, "retrieve": 0, "rerank": 0, "llm": 0}
}
```

### 3.3 錯誤碼

| code | HTTP | 說明 |
| --- | --- | --- |
| `PII_DETECTED` | 400 | 查詢含疑似個資，拒絕處理 |
| `INDEX_UNAVAILABLE` | 503 | OpenSearch / Qdrant 不可用 |
| `REFUSAL` | 200 | 業務拒答（仍回 answer_contract） |

## 4. MCP Tools（草案）

| tool | input | output |
| --- | --- | --- |
| `legal_query` | `query`, `top_k?`, `synthesize_markdown?` | 同 REST `/v1/legal/query` |
| `legal_search_units` | `query`, `filters?`, `top_k?` | `legal_unit` 列表 + 分數 |
| `legal_explain_citation` | `citation_key` | parent+child 文本與 metadata |

## 5. 驗收要求

* `/health` 在任一後端故障時能正確顯示 false
* `legal_query` 在 `REFUSAL` 情境仍回可稽核 JSON（不得 500）

## 6. 依賴

* [Spec-007](./spec-007-generation-orchestrator.md)
