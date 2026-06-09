# 小熊法律屋 🐻 — 法律常識 LINE Bot

## 專題資訊
- **姓名**：熊婉其
- **學號**：B11356021
- **主題**：法律常識助理

---

## 專題動機
法律問題常常讓一般民眾感到困惑，許多人遇到法律問題不知道從何尋求協助。本專題透過 LINE Bot 結合 RAG 技術，讓使用者可以用日常語言詢問法律問題，系統自動從台灣法規資料庫中檢索相關法條，提供即時的法律常識說明。

---

## 系統架構
使用者 LINE 訊息
↓
LINE Webhook（FastAPI）
↓
意圖路由（OpenAI gpt-4o-mini）
↓
RAG 檢索（Supabase pgvector）
↓
回覆生成（OpenAI gpt-4o-mini）
↓
LINE 回覆

---

## Skill 設計

| Skill | 說明 |
|-------|------|
| legal_advisor | 一般法律問題、法條解釋、法律建議 |
| contract_reviewer | 合約審查、條款分析、契約風險 |
| legal_research | 判例查詢、法規研究、法律趨勢 |
| rights_advisor | 消費者保護、勞工權益、基本人權 |
| general | 其他一般問題 |

---

## 知識庫來源

| 法規 | 來源 | 段落數 |
|------|------|--------|
| 民法 | 全國法規資料庫 | 234 |
| 消費者保護法 | 全國法規資料庫 | 21 |
| 勞動基準法 | 全國法規資料庫 | 36 |

資料來源：[全國法規資料庫](https://law.moj.gov.tw)

---

## 技術架構

- **後端**：FastAPI + Python
- **LLM**：OpenAI gpt-4o-mini
- **資料庫**：Supabase（PostgreSQL + pgvector）
- **Webhook Tunnel**：ngrok
- **訊息平台**：LINE Messaging API

---

## 系統操作說明

### 啟動步驟

1. 安裝套件：
```bash
pip install -e ".[dev]"
```

2. 設定 `.env`（填入 LINE、OpenAI、Supabase 憑證）

3. 啟動 App：
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

4. 啟動 ngrok：
```bash
ngrok http 8000
```

5. 更新 LINE Webhook URL

### 可詢問的問題範例

- 「民法第184條是什麼？」
- 「勞基法加班費怎麼算？」
- 「消費者保護法第19條是什麼？」
- 「房租押金糾紛怎麼處理？」

---

## 操作截圖

<img width="1438" height="517" alt="image" src="https://github.com/user-attachments/assets/d33a0507-7ff2-4688-9bb1-f3b75d3b5fa0" />


---

## 結論與未來改進

本專題成功實現法律常識 LINE Bot，能夠根據使用者問題自動分類意圖、檢索相關法條，並生成具體的法律說明。

未來可改進的方向：
- 增加更多法規（刑法、民事訴訟法等）
- 加入裁判書判例
- 實作向量搜尋（embedding）提升檢索準確度
- 部署到 GCP Cloud Run 提供穩定服務
