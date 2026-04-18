# ADR-001: Legal RAG 的 Embedding Model 選擇（BGE-M3 vs OpenAI text-embedding-3）

**狀態**：Accepted  
**日期**：2026-04-18  
**決策者**：Student / RAG Architect  
**對應 Spec**：[Spec-003](../specs/spec-003-knowledge-etl.md)、[Spec-008](../specs/spec-008-storage-schema.md)

> 期中格式對照：**Context**＝「脈絡與問題」；**Decision**＝「決策」；**Status**＝本文件抬頭狀態；**Consequences**＝「後果（含風險與緩解）」。

---

## 脈絡與問題

法律 RAG 的檢索輸入同時包含兩類語言現象：

1. **高精準關鍵詞**：條號、法規全名、專有法學術語、裁判字別中的數字與代碼。
2. **高語意彈性**：使用者以故事性敘述描述爭點，且常混用口語與半專業詞彙。

Embedding 模型的選擇因此不是「哪個分數最高」的單題答案，而是 **效果 × 成本 × 可部署性 × 可審計性** 的權衡。

此外，法律資料會進行版本化與重建索引；embedding 服務若不可自控，將增加資料外送與合規審查成本。

---

## 決策

採用 **BGE-M3 作為主 embedding 模型**，並保留 **OpenAI `text-embedding-3-large` 作為 offline A/B 對照組**。

### 核心決策點

1. **主索引以自建推理服務為優先**  
   讓 ETL 與重建索引可在內網批次完成，並保存可重現的 `model_revision` 與 `embedding_config`。

2. **不把「條號命中」完全交給向量模型**  
   條號與法規名稱的精準命中主要由 BM25 與正規化器完成；向量模型負責爭點語意與跨段落關聯。

3. **embedding_text 與 clean_markdown 分離**  
   以結構化標頭注入 domain 訊息（見 Spec-003），避免模型只看到「裸文本」而降低可檢索性。

---

## 被拒絕的方案

### 方案 A：只使用 OpenAI embedding 作為唯一主索引

* **問題**：大量法規與判決文本重建索引時成本高；資料外送合規路徑複雜；對「可離線重跑評估」不友善。  
* **結論**：拒絕作為唯一方案（允許作為對照）。

### 方案 B：只使用小型中文模型（極低成本）

* **問題**：對長法條、複合爭點、以及中英混排（國際私法、比較法引用）語意表現不穩定。  
* **結論**：拒絕作為 MVP 主方案。

### 方案 C：以 LLM 直接生成「檢索用 embedding 文字」但不驗證

* **問題**：容易引入模型幻覺標籤，污染索引與 filter。  
* **結論**：拒絕；必須 JSON Schema + 規則驗證（Spec-003a）。

---

## 後果

### 正面影響

* 索引重建成本可控，便於作業與研究反覆實驗。
* 可記錄完整 `model_revision`，提升審計與可重現性。
* 與 reranker（cross-encoder）搭配時，dense retrieval 可用「較寬鬆召回」策略。

### 負面影響與風險

* 需自建 embedding 服務與 GPU／CPU 資源規劃。
* 模型升級會造成向量空間漂移，需要重新評估與（可選）dual-write 遷移策略。

### 緩解措施

* 以 `law_version_id + model_revision` 作為索引世代鍵，避免混用不同模型向量。
* 以 Golden Set 做 A/B：每次模型升級必跑 [Spec-009](../specs/spec-009-evaluation-framework.md)。

---

## 相關文件

* [ADR-002](./ADR-002-retrieval-strategy.md)
* [白皮書：法條與案例 RAG](../whitepaper/legal-rag-whitepaper.md)
