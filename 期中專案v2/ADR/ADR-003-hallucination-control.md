# ADR-003: Hallucination 控制（Rerank + Grounded Generation + 規則拒答）

**狀態**：Accepted  
**日期**：2026-04-18  
**決策者**：Student / RAG Architect  
**對應 Spec**：[Spec-005](../specs/spec-005-jurisdiction-rule-engine.md)、[Spec-007](../specs/spec-007-generation-orchestrator.md)

> 期中格式對照：**Context**＝「脈絡與問題」；**Decision**＝「決策」；**Status**＝本文件抬頭狀態；**Consequences**＝「後果（含風險與緩解）」。

---

## 脈絡與問題

法律場景的「幻覺」不只是捏造事實，更常見的是：

* **錯置條號**：引用看似合理但不符合使用者法域／版本／構成要件脈絡。
* **錯置判決意旨**：把 A 類案的要旨套到 B 類案。
* **把教學性描述當成實務結論**：在證據不足時仍給出確定語氣。

因此，抑制幻覺不能只靠 prompt「請不要亂講」，而需要 **證據關卡 + 結構化輸出 + 後處理守門**。

---

## 決策

採用三層控制：

1. **檢索後**：cross-encoder rerank，降低低相關片段進入生成的機率。  
2. **生成前**：Jurisdiction Rule Engine 依程序／時效／證據不足旗標調整 `generation_mode`。  
3. **生成格式**：Stage 1 `Answer Contract` 完全確定；Stage 2 LLM 只能在 `G_citations` 範圍內敘事。

---

## 被拒絕的方案

### 方案 A：端到端由 LLM 直接回答（不使用 RAG）

* **結論**：拒絕（法律高風險）。

### 方案 B：RAG 但不限制引用集合（只把 top chunks 丟給模型）

* **問題**：模型仍可能引用 chunk 外的條號或判決字號。  
* **結論**：拒絕；必須 `G_citations` 守門。

### 方案 C：以「提高 temperature 讓回答更自然」

* **結論**：拒絕；法律敘事寧可保守，不追求花俏。

---

## 後果

### 正面影響

* `faithfulness` / `groundedness` 可顯著提升（以 RAGAS／TruLens 驗證）。
* 拒答與補問可被稽核（對老師展示「為何不敢回答」很重要）。

### 負面影響與風險

* rerank 增加延遲；需要在 SLO 內做 budget（例如限制 rerank 輸入長度）。
* Stage 2 後處理若過於嚴格，可能導致「可用但不完整」的回答體驗。

### 緩解措施

* rerank 只對 top-50 執行；parent 全文不進 reranker。
* 以 TruLens 監控 groundedness 分佈，調整拒答閾值。

---

## 相關文件

* [Spec-009：評估框架](../specs/spec-009-evaluation-framework.md)
* [白皮書](../whitepaper/legal-rag-whitepaper.md)
