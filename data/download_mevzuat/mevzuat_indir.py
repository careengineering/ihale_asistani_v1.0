import os
import ssl
import urllib3
import pandas as pd
import requests
import zipfile
import rarfile
from datetime import date
from pathlib import Path
from urllib.parse import urlparse
from requests.adapters import HTTPAdapter
import re
import unicodedata

# SSL uyarılarını bastır
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# TLS uyumlu bağlantı için özel adapter
class TLSAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        ctx.set_ciphers("DEFAULT@SECLEVEL=1")
        kwargs["ssl_context"] = ctx
        return super().init_poolmanager(*args, **kwargs)

session = requests.Session()
session.mount("https://", TLSAdapter())

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/123.0 Safari/537.36"
    )
}

# Karakter temizleme fonksiyonu
def temizle_metin(metin):
    metin = str(metin).lower()
    metin = unicodedata.normalize('NFD', metin).encode('ascii', 'ignore').decode("utf-8")
    metin = re.sub(r"[^\w\s-]", "", metin)
    metin = re.sub(r"\s+", "_", metin).strip()
    return metin

# Uzantı belirleme
def get_extension_from_response(resp, fallback_ext=".pdf"):
    content_type = resp.headers.get("Content-Type", "").lower()
    if "pdf" in content_type:
        return ".pdf"
    elif "msword" in content_type or "officedocument" in content_type:
        return ".docx"
    elif "text/plain" in content_type:
        return ".txt"
    elif "zip" in content_type:
        return ".zip"
    elif "rar" in content_type:
        return ".rar"
    
    cd = resp.headers.get("Content-Disposition")
    if cd and "filename=" in cd:
        filename = cd.split("filename=")[-1].strip('"; ')
        ext = os.path.splitext(filename)[-1].lower()
        if ext in [".pdf", ".docx", ".txt", ".zip", ".rar"]:
            return ext
        return fallback_ext

    parsed = urlparse(resp.url)
    ext = os.path.splitext(parsed.path)[1].lower()
    if ext in [".pdf", ".docx", ".txt", ".zip", ".rar"]:
        return ext
    return fallback_ext

# Doc to PDF dönüştürme (wkhtmltopdf yerine sistem varsayılanını kullanıyoruz)
def convert_doc_to_pdf(doc_path, pdf_path):
    try:
        print(f"📄 Dönüştürme: {doc_path} -> {pdf_path}")
        os.system(f"libreoffice --headless --convert-to pdf {doc_path} --outdir {pdf_path.parent}")
        if pdf_path.exists():
            os.remove(doc_path)
            print(f"✅ Dönüşüm başarılı: {pdf_path}")
            return pdf_path
        else:
            print(f"❌ PDF oluşturulmadı: {pdf_path}")
            return doc_path
    except Exception as e:
        print(f"❌ Dönüşüm hatası: {doc_path}: {e}")
        return doc_path

# Klasördeki .doc ve .docx dosyalarını PDF'ye çevirme
def convert_all_docs_to_pdf(directory):
    doc_found = False
    try:
        for root, _, files in os.walk(directory):
            for file in files:
                if file.endswith((".doc", ".docx")):
                    doc_found = True
                    doc_path = Path(root) / file
                    pdf_path = doc_path.with_suffix(".pdf")
                    print(f"📄 Tespit edilen dosya: {doc_path}")
                    convert_doc_to_pdf(doc_path, pdf_path)
        if not doc_found:
            print(f"ℹ️ Klasörde .doc/.docx dosyası yok: {directory}")
    except Exception as e:
        print(f"❌ Dönüştürme hatası: {directory}: {e}")

# Dosya kaydetme
def save_file(content, filepath, ext):
    final_path = filepath.with_suffix(ext)
    try:
        with open(final_path, "wb") as f:
            f.write(content)
        print(f"✅ Dosya kaydedildi: {final_path}")
        if ext in [".doc", ".docx"]:
            final_path = convert_doc_to_pdf(final_path, final_path.with_suffix(".pdf"))
        return final_path
    except Exception as e:
        print(f"❌ Dosya kaydetme hatası: {filepath}: {e}")
        return None

# Arşiv dosyalarını açma
def process_archive_files(archive_path, target_dir, no, mevzuat_adi):
    extract_dir = target_dir / f"{no}_{temizle_metin(mevzuat_adi)}"
    extract_dir.mkdir(exist_ok=True)
    
    try:
        print(f"📦 Arşiv açılıyor: {archive_path} -> {extract_dir}")
        if archive_path.suffix == ".zip":
            with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
        elif archive_path.suffix == ".rar":
            with rarfile.RarFile(archive_path, 'r') as rar_ref:
                rar_ref.extractall(extract_dir)
        
        print(f"📄 Açılan dosyalar ({extract_dir}):")
        for root, _, files in os.walk(extract_dir):
            for file in files:
                print(f"  - {file}")
        
        convert_all_docs_to_pdf(extract_dir)
        return extract_dir
    except Exception as e:
        print(f"❌ Arşiv işleme hatası: {archive_path}: {e}")
        return archive_path

# ───── Ana İşlem ─────
script_dir = Path(__file__).resolve().parent
excel_path = script_dir / "mevzuat.xlsx"
if not excel_path.exists():
    raise FileNotFoundError(f"Excel dosyası bulunamadı: {excel_path}")

today_str = date.today().isoformat()
base_output_dir = script_dir / today_str
base_output_dir.mkdir(parents=True, exist_ok=True)

# Excel'i oku
df = pd.read_excel(excel_path)
sonuclar = []

for _, row in df.iterrows():
    no = str(row.get("No", "")).strip()
    mevzuat_adi = str(row.get("Mevzuat_Adi", "")).strip()
    klasor_adi = str(row.get("Klasor_adi", "")).strip()
    link = str(row.get("Link", "")).strip()

    result = {
        "No": no,
        "Mevzuat_Adi": mevzuat_adi,
        "Klasor_adi": klasor_adi,
        "Link": link,
        "Durum": "❌ Hatalı",
        "İndirme": "❌",
        "Dosya Yolu": "-",
        "Hata Mesajı": "-"
    }

    if not (no and mevzuat_adi and klasor_adi and link):
        result["Hata Mesajı"] = "Eksik veri"
        sonuclar.append(result)
        continue

    try:
        print(f"🌐 İndiriliyor: {link}")
        resp = session.get(link, headers=HEADERS, timeout=30, allow_redirects=True, verify=False)
        if resp.status_code != 200:
            result["Hata Mesajı"] = f"HTTP {resp.status_code}"
            sonuclar.append(result)
            continue

        ext = get_extension_from_response(resp)
        if ext not in [".pdf", ".docx", ".txt", ".zip", ".rar"]:
            result["Hata Mesajı"] = f"Desteklenmeyen dosya türü: {ext}"
            sonuclar.append(result)
            continue

        hedef_klasor = base_output_dir / temizle_metin(klasor_adi)
        hedef_klasor.mkdir(parents=True, exist_ok=True)

        dosya_adi = f"{no}_{temizle_metin(mevzuat_adi)}"
        filepath = hedef_klasor / dosya_adi
        final_path = save_file(resp.content, filepath, ext)

        if not final_path:
            result["Hata Mesajı"] = "Dosya kaydetme başarısız"
            sonuclar.append(result)
            continue

        if ext in [".zip", ".rar"]:
            extract_path = process_archive_files(final_path, hedef_klasor, no, mevzuat_adi)
            result["Dosya Yolu"] = str(extract_path)
        else:
            result["Dosya Yolu"] = str(final_path)

        result["Durum"] = "✅ Aktif"
        result["İndirme"] = "✅ Başarılı"

    except Exception as e:
        result["Hata Mesajı"] = str(e)
        print(f"❌ Hata: {link}: {e}")

    sonuclar.append(result)

# Raporu yaz
rapor_df = pd.DataFrame(sonuclar)
rapor_path = script_dir / "indirme_raporu.xlsx"
rapor_df.to_excel(rapor_path, index=False)

print(f"\n✅ İndirme tamamlandı. Rapor: {rapor_path}")