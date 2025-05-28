import os

# Çıkış dosyası adı
output_file = "codes.txt"

# Taranacak klasörler
folders = ["src", "app"]

# Çıkış dosyasını sıfırlamak için aç
with open(output_file, "w", encoding="utf-8") as outfile:
    # Her bir klasörü tara
    for folder in folders:
        # Klasör mevcut mu kontrol et
        if not os.path.exists(folder):
            print(f"{folder} klasörü bulunamadı.")
            continue
        
        # Klasördeki tüm .py dosyalarını bul, __init__.py hariç
        for root, _, files in os.walk(folder):
            for file in files:
                if file.endswith(".py") and file != "__init__.py":
                    file_path = os.path.join(root, file)
                    try:
                        # Dosyayı oku
                        with open(file_path, "r", encoding="utf-8") as infile:
                            content = infile.read()
                        
                        # Çıkış dosyasına yaz
                        outfile.write(f"\n\n===== {file_path} =====\n")
                        outfile.write(content)
                    except Exception as e:
                        print(f"Hata: {file_path} okunamadı - {e}")

print(f"İşlem tamamlandı. Çıktı {output_file} dosyasına kaydedildi.")