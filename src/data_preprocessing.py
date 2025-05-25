import os
import zipfile
import tempfile
from pathlib import Path
import PyPDF2
from docx import Document
from bs4 import BeautifulSoup
import re
import json
from collections import defaultdict

def extract_text_from_pdf(file_path):
    """PDF dosyasından metin çıkarır, UTF-8 kodlamasını korur."""
    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            text = ''
            for page in reader.pages:
                page_text = page.extract_text() or ''
                text += page_text
        return text.encode('utf-8').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Hata: {file_path} işlenemedi. {e}")
        return ''

def extract_text_from_docx(file_path):
    """DOCX dosyasından metin çıkarır, UTF-8 kodlamasını korur."""
    try:
        doc = Document(file_path)
        text = '\n'.join([para.text for para in doc.paragraphs])
        return text.encode('utf-8').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Hata: {file_path} işlenemedi. {e}")
        return ''

def extract_text_from_html(file_path):
    """HTML dosyasından metin çıkarır, UTF-8 kodlamasını korur."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            soup = BeautifulSoup(file, 'html.parser')
            text = soup.get_text(separator='\n', strip=True)
        return text.encode('utf-8').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Hata: {file_path} işlenemedi. {e}")
        return ''

def extract_text_from_txt(file_path):
    """TXT dosyasından metin çıkarır, UTF-8 kodlamasını korur."""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            text = file.read()
        return text.encode('utf-8').decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"Hata: {file_path} işlenemedi. {e}")
        return ''

def extract_text_from_file(file_path):
    """Dosya uzantısına göre uygun metin çıkarma fonksiyonunu çağırır."""
    ext = Path(file_path).suffix.lower()
    if ext == '.pdf':
        return extract_text_from_pdf(file_path)
    elif ext == '.docx':
        return extract_text_from_docx(file_path)
    elif ext == '.html':
        return extract_text_from_html(file_path)
    elif ext == '.txt':
        return extract_text_from_txt(file_path)
    else:
        print(f"Desteklenmeyen dosya türü: {file_path}")
        return ''

def unzip_file(zip_path, extract_to):
    """ZIP dosyasını belirtilen klasöre çıkarır."""
    try:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_to)
        return extract_to
    except Exception as e:
        print(f"Hata: {zip_path} açılamadı. {e}")
        return None

def clean_text(text, is_kik=False):
    """Metni temizler: teknik şablonları, gereksiz bilgileri ve bozuk karakterleri kaldırır."""
    if not text:
        return ''
    
    # Bozuk karakterleri temizle, Türkçe karakterleri koru
    text = re.sub(r'[^\w\s.,;:-çğışöüÇĞİŞÖÜ]', ' ', text)
    
    # Yürütme/yürürlük maddelerinden sonrasını kaldır
    text = re.sub(r'(Yürütme|Yürürlük)\s+Madde.*?(?=\Z)', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Teknik şablonları ve gereksiz bilgileri kaldır
    patterns = [
        r'Telefon numarası:.*?(?=(Madde|\Z))',
        r'Faks numarası:.*?(?=(Madde|\Z))',
        r'\.{3,}\s*',
        r'\b(Mülga|Değişik ibare|yürürlük):?\s*\d{1,2}/\d{1,2}/\d{4}\s*RG\d*\.?\s*md\.?',
        r'İhale kayıt numarası:.*?(?=(Madde|\Z))',
        r'\b(Şartname|EK-\d+|Standart Form|Tutanağı|Tutanagi).*?(?=(Madde|\Z))',
        r'\|\s*\|+',  # Tablo benzeri yapılar
        r'\[.*?\]',   # Köşeli parantezler
    ]
    for pattern in patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # KİK kararları için gereksiz bilgileri kaldır
    if is_kik:
        text = re.sub(r'(Toplantı No|Gündem No|Katılan Üye Sayısı):.*?(?=(Gündem Konusu|\Z))', '', text, flags=re.IGNORECASE | re.DOTALL)
    
    # Fazla boşlukları temizle, Türkçe karakterleri koru
    text = re.sub(r'\s+', ' ', text.strip())
    text = re.sub(r'([a-zçğışöü])([A-ZÇĞİŞÖÜ])', r'\1 \2', text)
    if len(text) < 30 or text.isspace():
        return ''
    return text

def chunk_text(text, max_length=500):
    """Metni anlamlı parçalara böler, Türkçe karakterleri korur."""
    sentences = re.split(r'(?<!\w\.\w.)(?<![A-ZÇĞİŞÖÜ][a-zçğışöü]\.)(?<=\.|\?)\s', text)
    chunks = []
    current_chunk = ''
    
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_length:
            current_chunk += ' ' + sentence
        else:
            cleaned_chunk = clean_text(current_chunk)
            if cleaned_chunk:
                chunks.append(cleaned_chunk)
            current_chunk = sentence
    cleaned_chunk = clean_text(current_chunk)
    if cleaned_chunk:
        chunks.append(cleaned_chunk)
    
    return chunks

def get_category(file_path):
    """Dosyanın kategorisini belirler."""
    file_path = str(file_path).lower()
    if 'genel şartname' in file_path:
        return 'genel_sartname'
    elif 'kanun' in file_path:
        return 'kanun'
    elif 'yonetmelik' in file_path:
        return 'yonetmelik'
    elif 'teblig' in file_path:
        return 'teblig'
    elif 'esaslar' in file_path:
        return 'esaslar'
    elif 'kik_kararlari' in file_path:
        return 'kik_kararlari'
    return 'bilinmeyen'

def get_ihale_type(file_path):
    """Dosyanın ihale türünü belirler."""
    file_path = str(file_path).lower()
    if 'mal' in file_path:
        return 'Mal'
    elif 'hizmet' in file_path:
        return 'Hizmet'
    elif 'yapım' in file_path or 'yapim' in file_path:
        return 'Yapım'
    elif 'danışmanlık' in file_path or 'danismanlik' in file_path:
        return 'Danışmanlık'
    return 'Genel'

def get_mevzuat_name(file_path):
    """Dosyanın mevzuat ismini daha spesifik şekilde çıkarır."""
    file_path = str(file_path).lower()
    file_name = Path(file_path).stem.replace('_', ' ')
    
    keywords = {
        'kamu ihale kanunu': 'Kamu İhale Kanunu',
        'mal alımı ihaleleri uygulama yönetmeliği': 'Mal Alımı İhaleleri Uygulama Yönetmeliği',
        'hizmet alımı ihaleleri uygulama yönetmeliği': 'Hizmet Alımı İhaleleri Uygulama Yönetmeliği',
        'yapım işleri ihaleleri uygulama yönetmeliği': 'Yapım İşleri İhaleleri Uygulama Yönetmeliği',
        'danışmanlık hizmet alımları yönetmeliği': 'Danışmanlık Hizmet Alımları Yönetmeliği',
        'genel şartname': 'Genel Şartname',
        'tebliğ': 'Tebliğ',
        'esaslar': 'Esaslar',
        'kik karar': 'KİK Kararları'
    }
    for key, value in keywords.items():
        if key in file_name:
            return value
    return file_name.title()

def get_kik_decision_info(text):
    """KİK kararlarından tarih ve numara çıkarır."""
    date_pattern = r'(\d{1,2}\.\d{1,2}\.\d{4})'
    number_pattern = r'Karar No\s*:\s*(\d+/\d+|\d+-\w+\.\w+-\d+)'
    date_match = re.search(date_pattern, text)
    number_match = re.search(number_pattern, text)
    date = date_match.group(1) if date_match else 'Bilinmeyen Tarih'
    number = number_match.group(1) if number_match else 'Bilinmeyen Numara'
    return date, number

def process_files(raw_dir, processed_dir):
    """Tüm dosyaları tarar, metinleri çıkarır ve JSON olarak kaydeder."""
    data = []
    seen_texts = defaultdict(set)
    raw_path = Path(raw_dir)
    temp_dir = tempfile.mkdtemp()

    for root, _, files in os.walk(raw_path):
        for file in files:
            file_path = Path(root) / file
            file_name_lower = file.lower()
            if any(keyword in file_name_lower for keyword in ['ek-', 'standart form', 'tutanağı', 'tutanagi']):
                print(f"Atlandı: {file_path} (EK, Standart Form veya Tutanak)")
                continue
            category = get_category(file_path)
            ihale_type = get_ihale_type(file_path)
            mevzuat_name = get_mevzuat_name(file_path)
            is_kik = category == 'kik_kararlari'
            
            if file_path.suffix.lower() == '.zip':
                extract_path = unzip_file(file_path, Path(temp_dir) / file_path.stem)
                if extract_path:
                    for sub_root, _, sub_files in os.walk(extract_path):
                        for sub_file in sub_files:
                            sub_file_lower = sub_file.lower()
                            if any(keyword in sub_file_lower for keyword in ['ek-', 'standart form', 'tutanağı', 'tutanagi']):
                                print(f"Atlandı: {sub_file} (EK, Standart Form veya Tutanak)")
                                continue
                            sub_file_path = Path(sub_root) / sub_file
                            text = extract_text_from_file(sub_file_path)
                            if text:
                                chunks = chunk_text(clean_text(text, is_kik=is_kik))
                                for i, chunk in enumerate(chunks):
                                    if chunk not in seen_texts[sub_file_path.stem]:
                                        seen_texts[sub_file_path.stem].add(chunk)
                                        chunk_data = {
                                            'mevzuat_name': get_mevzuat_name(sub_file_path),
                                            'chunk_id': f"{sub_file_path.stem}_{i}",
                                            'text': chunk,
                                            'category': category,
                                            'ihale_type': ihale_type
                                        }
                                        if is_kik:
                                            date, number = get_kik_decision_info(text)
                                            chunk_data['kik_date'] = date
                                            chunk_data['kik_number'] = number
                                        data.append(chunk_data)
            else:
                text = extract_text_from_file(file_path)
                if text:
                    chunks = chunk_text(clean_text(text, is_kik=is_kik))
                    for i, chunk in enumerate(chunks):
                        if chunk not in seen_texts[file_path.stem]:
                            seen_texts[file_path.stem].add(chunk)
                            chunk_data = {
                                'mevzuat_name': mevzuat_name,
                                'chunk_id': f"{file_path.stem}_{i}",
                                'text': chunk,
                                'category': category,
                                'ihale_type': ihale_type
                            }
                            if is_kik:
                                date, number = get_kik_decision_info(text)
                                chunk_data['kik_date'] = date
                                chunk_data['kik_number'] = number
                            data.append(chunk_data)

    output_path = Path(processed_dir) / 'mevzuat_chunks.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"İşlenen veriler {output_path}'a kaydedildi. Toplam {len(data)} parça.")

if __name__ == '__main__':
    RAW_DIR = 'data/raw'
    PROCESSED_DIR = 'data/processed'
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    process_files(RAW_DIR, PROCESSED_DIR)