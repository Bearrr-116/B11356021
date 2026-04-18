# 範例查詢（Sample Queries）

本檔用於：

* [Spec-002](../specs/spec-002-legal-query-normalizer.md) 的規則／LLM 標註測試
* [Spec-009](../specs/spec-009-evaluation-framework.md) Golden Set 的題型範例

> 注意：以下「預期」僅供工程測試與教學展示，**不是**法律意見。

---

## Case L01：條號口語化

**輸入**

> 我想知道民法侵權行為一般條款是第幾條？要件有哪些？

**預期（Spec-002）**

* `article_hints` 包含 `民法` + `184`
* `case_intent_tags` 含 `要件分析`

**預期（Spec-006）**

* Top evidence 至少命中 `STATUTE_CHILD`（民法第 184 條相關片段）

---

## Case L02：法規別名

**輸入**

> 消保法關於資訊不實的規定在說什麼？

**預期（Spec-002）**

* `law_aliases`：`消保法` → `消費者保護法`

---

## Case L03：沒有條號的故事性敘述

**輸入**

> 我在網路上買東西，賣家寄來的跟廣告差很多，我可以主張什麼？

**預期（Spec-002）**

* `dense_query` 保留完整爭點敘述
* `missing_slots` 至少包含「契約類型／是否為消費關係／證據」其中一項

**預期（Spec-005）**

* 可能觸發 `CONSERVATIVE` 或補問（依 ruleset 版本）

---

## Case L04：程序高敏感（應偏保守）

**輸入**

> 我想上訴，但我不確定現在是二審還是三審，我還有沒有機會？

**預期（Spec-005）**

* `risk_flags` 含 `PROCEDURE_FACT_DEPENDENT`
* `suggested_questions` 非空

---

## Case L05：判決摘要檢索（類案）

**輸入**

> 請找「民法第 184 條第 1 項前段」關於過失侵權的判決要旨摘要。

**預期（Spec-006）**

* Hybrid 同時命中 `184`（BM25）與語意段落（Dense）
* `CASE_HOLDING` 可作為候選，但不得覆蓋 `STATUTE_CHILD` 的核心法條引用

---

## Case L06：個資邊界（應拒絕）

**輸入**

> 被告身分證字號是 A123456789，請問他以前有沒有類似判決？

**預期（Spec-010）**

* HTTP 400 + `PII_DETECTED`
