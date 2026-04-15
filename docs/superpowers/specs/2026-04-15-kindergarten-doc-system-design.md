# 幼兒園教學口述自動生成文件系統 — 設計規格

**日期**：2026-04-15  
**狀態**：已確認，待實作

---

## 一、專案目標

讓幼兒園老師透過手機或電腦瀏覽器，對著麥克風口述本週教學情況，系統自動產出：
- 班刊（給家長閱讀）
- 教學週誌（正式存檔文件）

輸出格式：DOCX（必備）+ PDF（選配）

---

## 二、技術選型

| 項目 | 選擇 | 說明 |
|------|------|------|
| 語言 | Python 3.11+ | 主要開發語言 |
| 介面 | Streamlit | 瀏覽器介面，支援手機 |
| 部署 | Streamlit Community Cloud | 免費，GitHub 部署，手機可用 |
| STT | OpenAI Whisper API | 中文辨識準確率高 |
| LLM | OpenAI GPT-4o | 結構化輸出穩定 |
| DOCX 產生 | python-docx | 套用範本欄位 |
| PDF 轉換 | LibreOffice headless（雲端）+ DOCX 下載（備用）| A+B 方案 |
| 語言 | 全程繁體中文 | 符合台灣幼兒園場景 |

---

## 三、專案結構

```
幼稚園學姊/
├── app.py                    # Streamlit 主介面
├── modules/
│   ├── stt.py               # 語音轉文字（Whisper API）
│   ├── llm.py               # LLM 呼叫（GPT-4o）：整理 JSON、生成班刊、生成週誌
│   ├── docx_generator.py    # 讀取範本、填入資料、產出 DOCX
│   └── pdf_converter.py     # LibreOffice headless 轉 PDF
├── prompts/
│   ├── structuring.txt      # 逐字稿→JSON 提示詞
│   ├── newsletter.txt       # JSON→班刊 提示詞
│   └── weekly_log.txt       # JSON→週誌 提示詞
├── templates/
│   ├── 班刊範本.docx         # 使用者提供的班刊模板
│   └── 週誌範本.docx         # 使用者提供的週誌模板
├── outputs/                 # 每次執行自動產出檔案
│   ├── transcript.txt
│   ├── structured_data.json
│   ├── 班刊.docx
│   ├── 週誌.docx
│   ├── 班刊.pdf（若可）
│   └── 週誌.pdf（若可）
├── .streamlit/
│   └── secrets.toml.example # API Key 設定範例
├── .env.example
├── requirements.txt
├── packages.txt             # Streamlit Cloud 系統套件（LibreOffice）
└── README.md
```

---

## 四、資料流

```
[輸入] 錄音 / 上傳音檔 / 貼上逐字稿
           ↓
     [stt.py] Whisper API
           ↓
     逐字稿顯示區（可手動編輯）
           ↓
     [llm.py] GPT-4o 整理成 JSON
           ↓
     structured_data.json（可檢視）
           ↓              ↓
  [llm.py] 班刊內容   [llm.py] 週誌內容
           ↓              ↓
  [docx_generator]  [docx_generator]
     套用班刊範本      套用週誌範本
           ↓              ↓
       班刊.docx       週誌.docx
           ↓              ↓
   [pdf_converter]  [pdf_converter]
           ↓              ↓
       班刊.pdf       週誌.pdf
```

---

## 五、介面設計（Streamlit）

### 區塊一：輸入
- Tab A：🎙️ 直接錄音（`st.audio_input()`，手機支援）
- Tab B：📁 上傳音檔（mp3 / wav / m4a）
- Tab C：✏️ 直接貼上逐字稿文字

### 區塊二：逐字稿
- 顯示辨識結果（可編輯的文字區塊）
- 「整理成結構化資料」按鈕

### 區塊三：結構化資料
- 顯示整理後的 JSON（可展開檢視）
- 欄位包含：主題名稱、教師姓名、週次、日期區間、主題活動、大肌肉活動、學習指標、教學觀察、問題、延伸決定、行為輔導、親師溝通、照片記錄說明、老師叮嚀、給老師的話

### 區塊四：文件產出
- 「生成班刊 DOCX」按鈕
- 「生成週誌 DOCX」按鈕
- 「匯出 PDF」按鈕（嘗試 LibreOffice，失敗時提示下載 DOCX）
- 下載按鈕（班刊.docx、週誌.docx、班刊.pdf、週誌.pdf）

### 區塊五：狀態提示
- 每個步驟顯示進度 spinner 與成功/失敗訊息

---

## 六、LLM 提示詞策略

### 整理 JSON（structuring.txt）
- 輸入：逐字稿
- 輸出：符合固定格式的 JSON
- 規則：不可虛構、缺資料填 `[待補]`、學習指標可合理建議但標示「建議補充」

### 生成班刊（newsletter.txt）
- 輸入：JSON
- 輸出：給家長閱讀的親切文字
- 語氣：溫暖、清楚、適合台灣幼兒園家長

### 生成週誌（weekly_log.txt）
- 輸入：JSON
- 輸出：正式教學存檔文件
- 語氣：專業、完整、可作為行政紀錄

---

## 七、DOCX 模板套用策略

1. 啟動時讀取 `templates/` 目錄下的兩份範本 DOCX
2. 分析範本的段落結構、表格欄位、標題層級
3. 產出時以範本為基礎，用 `python-docx` 定位佔位符或表格格，填入對應資料
4. 若範本使用複雜排版（如多欄、文字方塊），退而保留欄位名稱與順序
5. 佔位符格式：`{{欄位名稱}}`（若範本無佔位符，則程式自動依段落順序對應）

---

## 八、PDF 轉換策略

- **雲端**：使用 `packages.txt` 安裝 LibreOffice，執行 `libreoffice --headless --convert-to pdf`
- **本機 Windows**：同樣嘗試 LibreOffice；若未安裝，提示使用者下載 DOCX 後自行轉換
- 無論 PDF 是否成功，DOCX 一定提供下載

---

## 九、部署方式

1. 推送到 GitHub（私有倉庫）
2. 連結 Streamlit Community Cloud
3. 在 Streamlit Cloud 的 Secrets 設定 `OPENAI_API_KEY`
4. `packages.txt` 列出 `libreoffice` 讓雲端自動安裝

---

## 十、安全性

- API Key 絕不寫入程式碼，只存於 `.streamlit/secrets.toml`（本機）或 Streamlit Cloud Secrets（雲端）
- 上傳的音檔只暫存於 session，不永久儲存於伺服器
- 輸出檔案提供下載後可清除

---

## 十一、不在範圍內（此版本不做）

- 使用者帳號系統
- 多班級管理
- 歷史紀錄查詢
- 自動排程
