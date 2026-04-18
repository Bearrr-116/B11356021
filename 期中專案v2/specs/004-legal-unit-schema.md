# Spec-004: 法律知識單元 Schema（Legal Unit）

- Status: Draft
- Owner: Ontology / Legal Informatics
- Last Updated: 2026-04-18

## 1. 目的

定義系統中最小可索引單位 **`legal_unit`** 的型別、欄位契約、以及 **parent-child** 關聯，使檢索同時具備：

* child 粒度的高召回
* parent 粒度的高可讀性與可引用上下文

## 2. 設計原則

1. **chunk 邊界服從法律結構**（編章節、條項款、爭點段），不服從固定 token。
2. **每一個可被引用的主張**，必須能映射到 `legal_unit_id`。
3. **版本化**：法規修訂不覆寫舊向量；以 `law_version_id` 區分。

## 3. `unit_type` 枚舉

| unit_type | 說明 | 典型 parent |
| --- | --- | --- |
| `STATUTE_PARENT` | 整條或整節的可讀上下文 | 無，或上層 `HIERARCHY_NODE` |
| `STATUTE_CHILD` | 可檢索的最小法條片段 | `STATUTE_PARENT` |
| `INTERPRETATION_BLOCK` | 函釋段落 | 函釋主文件 parent |
| `CASE_FACTS` | 判決摘要的事實段 | `CASE_PARENT` |
| `CASE_HOLDING` | 判決摘要的見解／理由段 | `CASE_PARENT` |
| `CASE_PARENT` | 單一判決摘要文件層級 | 無 |

## 4. 欄位契約（logical schema）

> 實體存放對應見 [Spec-008](./spec-008-storage-schema.md)。此處為跨儲存層一致的邏輯欄位。

| 欄位 | 型別 | 必填 | 說明 |
| --- | --- | --- | --- |
| `legal_unit_id` | string | Y | 穩定 id（含版本與 hash） |
| `unit_type` | enum | Y | 見 §3 |
| `parent_unit_id` | string | N | parent-child 關聯 |
| `source_document_id` | string | Y | 回溯原始來源 |
| `law_name` | string | 條文類必填 | 法規全名 |
| `article_no` | int | 視情況 | 無條號結構者允許 null |
| `law_version_id` | string | Y | 對應公布／施行版本 |
| `authority_level` | int | Y | 0–100，對齊 Spec-003 分層 |
| `clean_markdown` | string | Y | 人類可讀正文 |
| `embedding_text` | string | Y | 實際送入 embedding 模型之文字 |
| `legal_domain_tags` | string[] | Y | 封閉集合 |
| `legal_issue_tags` | string[] | Y | 封閉集合 |
| `citation_key` | string | Y | 人類引用鍵（例如：`民法_184_2024-01-01_v3#child-2`） |
| `quality_score` | int | N | 0–100，ETL 驗證與抽樣評分 |
| `is_active` | bool | Y | soft delete |

判決摘要專用欄位（`CASE_*`）：

| 欄位 | 型別 | 必填 |
| --- | --- | --- |
| `court_code` | string | Y |
| `jcase_year` | int | Y |
| `jcase_no` | string | 視資料來源 |
| `cause_of_action` | string | Y |
| `parties_redacted` | bool | Y |

## 5. Parent-Child 不變式（Constraints）

* `STATUTE_CHILD.parent_unit_id` 必須指向 `STATUTE_PARENT`
* `STATUTE_PARENT` 不得引用不存在的 `law_version_id`
* 同一 `citation_key` 在相同 `law_version_id` 下必須唯一

## 6. `embedding_text` 組合規則

必須以結構化標頭開頭（見 [Spec-003 §6](./spec-003-knowledge-etl.md)），再加上：

* 若為 child：附加「與前後文銜接的一句話摘要」（由規則式或 LLM 產生，需標註 `bridge_summary_source`）

## 7. 驗收要求

* Random sample 50：`parent_unit_id` 違反不變式 = 0
* 所有 `legal_unit_id` 可從 `source_document_id` 追溯
* `embedding_text` 平均字數與 `clean_markdown` 字數差異需落在合理範圍（避免標頭過長稀释語義）

## 8. 依賴 ADR

* [ADR-002](../adr/ADR-002-retrieval-strategy.md)
