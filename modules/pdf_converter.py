"""PDF 轉換模組 - 使用 LibreOffice headless"""

import subprocess
import shutil
from pathlib import Path


def convert_to_pdf(docx_path: str, output_dir: str) -> str | None:
    """
    將 DOCX 轉為 PDF。成功回傳 PDF 路徑，失敗回傳 None。
    """
    docx_path = Path(docx_path)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 尋找 LibreOffice 執行檔
    lo_path = shutil.which("libreoffice") or shutil.which("soffice")
    if not lo_path:
        return None

    try:
        subprocess.run(
            [lo_path, "--headless", "--convert-to", "pdf", "--outdir", str(output_dir), str(docx_path)],
            capture_output=True,
            timeout=60,
            check=True,
        )
        pdf_path = output_dir / (docx_path.stem + ".pdf")
        if pdf_path.exists():
            return str(pdf_path)
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        pass

    return None
