"""幼稚園學姊 - 幼兒園教學口述自動生成文件系統"""

import json
import os
from pathlib import Path

import streamlit as st

from modules.stt import transcribe
from modules.llm import structure_transcript, generate_newsletter, generate_weekly_log
from modules.docx_generator import (
    generate_newsletter as gen_newsletter_docx,
    generate_weekly_log as gen_weekly_log_docx,
)
from modules.pdf_converter import convert_to_pdf

# ── 頁面設定 ──────────────────────────────────────────
st.set_page_config(page_title="幼稚園學姊", page_icon="🎒", layout="wide")
st.title("🎒 幼稚園學姊")
st.caption("幼兒園教學口述 → 班刊 + 週誌 自動產出系統")

OUTPUTS_DIR = Path("outputs")
OUTPUTS_DIR.mkdir(exist_ok=True)


# ── API Key ───────────────────────────────────────────
def get_api_key() -> str | None:
    # 優先順序：Streamlit secrets > 環境變數 > sidebar 輸入
    try:
        if "OPENAI_API_KEY" in st.secrets:
            return st.secrets["OPENAI_API_KEY"]
    except Exception:
        pass
    if os.environ.get("OPENAI_API_KEY"):
        return os.environ["OPENAI_API_KEY"]
    return None


api_key = get_api_key()
if not api_key:
    with st.sidebar:
        api_key = st.text_input("OpenAI API Key", type="password", help="請輸入您的 OpenAI API Key")
    if not api_key:
        st.warning("請在側邊欄輸入 OpenAI API Key 以開始使用。")
        st.stop()


# ── 初始化 session state ──────────────────────────────
for key in ["transcript", "structured_data", "newsletter_content", "log_content"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ══════════════════════════════════════════════════════
# 區塊一：輸入
# ══════════════════════════════════════════════════════
st.header("一、輸入音檔或逐字稿")

tab_record, tab_upload, tab_paste = st.tabs(["🎙️ 直接錄音", "📁 上傳音檔", "✏️ 貼上逐字稿"])

audio_bytes = None
audio_filename = "recording.wav"

with tab_record:
    recorded = st.audio_input("按下錄音鍵開始口述")
    if recorded:
        audio_bytes = recorded.getvalue()
        audio_filename = "recording.wav"

with tab_upload:
    uploaded = st.file_uploader("上傳音檔", type=["mp3", "wav", "m4a", "ogg", "webm"])
    if uploaded:
        audio_bytes = uploaded.getvalue()
        audio_filename = uploaded.name

with tab_paste:
    pasted = st.text_area("直接貼上逐字稿文字", height=200)
    if pasted:
        st.session_state.transcript = pasted

# 語音轉文字
if audio_bytes and st.session_state.transcript is None:
    with st.spinner("語音辨識中..."):
        try:
            st.session_state.transcript = transcribe(audio_bytes, api_key, audio_filename)
            st.success("語音辨識完成！")
        except Exception as e:
            st.error(f"語音辨識失敗：{e}")


# ══════════════════════════════════════════════════════
# 區塊二：逐字稿
# ══════════════════════════════════════════════════════
if st.session_state.transcript is not None:
    st.header("二、逐字稿（可編輯）")
    if st.button("⬅️ 重新輸入音檔/逐字稿", key="back_to_input"):
        st.session_state.transcript = None
        st.session_state.structured_data = None
        st.session_state.newsletter_content = None
        st.session_state.log_content = None
        st.rerun()
    edited_transcript = st.text_area(
        "逐字稿內容",
        value=st.session_state.transcript,
        height=250,
        label_visibility="collapsed",
    )
    st.session_state.transcript = edited_transcript

    # 儲存逐字稿
    (OUTPUTS_DIR / "transcript.txt").write_text(edited_transcript, encoding="utf-8")

    if st.button("📊 整理成結構化資料", type="primary"):
        with st.spinner("AI 正在整理結構化資料..."):
            try:
                st.session_state.structured_data = structure_transcript(edited_transcript, api_key)
                st.success("結構化資料整理完成！")
                # 儲存 JSON
                (OUTPUTS_DIR / "structured_data.json").write_text(
                    json.dumps(st.session_state.structured_data, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
            except Exception as e:
                st.error(f"整理失敗：{e}")


# ══════════════════════════════════════════════════════
# 區塊三：結構化資料
# ══════════════════════════════════════════════════════
if st.session_state.structured_data is not None:
    st.header("三、結構化資料")
    if st.button("⬅️ 回到逐字稿編輯", key="back_to_transcript"):
        st.session_state.structured_data = None
        st.session_state.newsletter_content = None
        st.session_state.log_content = None
        st.rerun()
    with st.expander("檢視 JSON 資料", expanded=True):
        st.json(st.session_state.structured_data)

    # ══════════════════════════════════════════════════
    # 區塊四：文件產出
    # ══════════════════════════════════════════════════
    st.header("四、文件產出")
    col1, col2 = st.columns(2)

    # ── 班刊 ──
    with col1:
        st.subheader("📰 班刊")
        if st.button("生成班刊", type="primary", key="gen_newsletter"):
            with st.spinner("AI 正在撰寫班刊..."):
                try:
                    st.session_state.newsletter_content = generate_newsletter(
                        st.session_state.structured_data, api_key
                    )
                    newsletter_path = str(OUTPUTS_DIR / "班刊.docx")
                    gen_newsletter_docx(
                        st.session_state.structured_data,
                        st.session_state.newsletter_content,
                        newsletter_path,
                    )
                    st.success("班刊生成完成！")
                except Exception as e:
                    st.error(f"班刊生成失敗：{e}")

        newsletter_docx = OUTPUTS_DIR / "班刊.docx"
        if newsletter_docx.exists():
            st.download_button(
                "⬇️ 下載班刊 DOCX",
                data=newsletter_docx.read_bytes(),
                file_name="班刊.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_newsletter_docx",
            )
            if st.button("轉換班刊 PDF", key="conv_newsletter_pdf"):
                with st.spinner("轉換 PDF 中..."):
                    pdf_path = convert_to_pdf(str(newsletter_docx), str(OUTPUTS_DIR))
                    if pdf_path:
                        st.success("PDF 轉換完成！")
                    else:
                        st.warning("PDF 轉換失敗（未偵測到 LibreOffice），請下載 DOCX 後自行轉換。")

            newsletter_pdf = OUTPUTS_DIR / "班刊.pdf"
            if newsletter_pdf.exists():
                st.download_button(
                    "⬇️ 下載班刊 PDF",
                    data=newsletter_pdf.read_bytes(),
                    file_name="班刊.pdf",
                    mime="application/pdf",
                    key="dl_newsletter_pdf",
                )

    # ── 週誌 ──
    with col2:
        st.subheader("📋 教學週誌")
        if st.button("生成週誌", type="primary", key="gen_log"):
            with st.spinner("AI 正在撰寫週誌..."):
                try:
                    st.session_state.log_content = generate_weekly_log(
                        st.session_state.structured_data, api_key
                    )
                    log_path = str(OUTPUTS_DIR / "週誌.docx")
                    gen_weekly_log_docx(
                        st.session_state.structured_data,
                        st.session_state.log_content,
                        log_path,
                    )
                    st.success("週誌生成完成！")
                except Exception as e:
                    st.error(f"週誌生成失敗：{e}")

        log_docx = OUTPUTS_DIR / "週誌.docx"
        if log_docx.exists():
            st.download_button(
                "⬇️ 下載週誌 DOCX",
                data=log_docx.read_bytes(),
                file_name="週誌.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                key="dl_log_docx",
            )
            if st.button("轉換週誌 PDF", key="conv_log_pdf"):
                with st.spinner("轉換 PDF 中..."):
                    pdf_path = convert_to_pdf(str(log_docx), str(OUTPUTS_DIR))
                    if pdf_path:
                        st.success("PDF 轉換完成！")
                    else:
                        st.warning("PDF 轉換失敗（未偵測到 LibreOffice），請下載 DOCX 後自行轉換。")

            log_pdf = OUTPUTS_DIR / "週誌.pdf"
            if log_pdf.exists():
                st.download_button(
                    "⬇️ 下載週誌 PDF",
                    data=log_pdf.read_bytes(),
                    file_name="週誌.pdf",
                    mime="application/pdf",
                    key="dl_log_pdf",
                )


# ── 頁尾 ─────────────────────────────────────────────
st.divider()
st.caption("幼稚園學姊 v1.0 — 讓老師專心教學，文件交給 AI")
