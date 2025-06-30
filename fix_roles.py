"""
DÖF sistemindeki rol karmaşasını düzeltmek için basit bir script.
Bu script:
1. Template üzerindeki role == 3 kontrollerini role == 4 olarak değiştirir
2. Sayfayı yeniden yükler
"""

import os
import sys

# Template dosyasının yolunu belirle
template_path = "templates/dof/detail.html"
full_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), template_path)

def fix_template_roles():
    """Template içindeki rol kontrollerini düzeltir"""
    print(f"Template dosyası kontrol ediliyor: {full_path}")
    
    if not os.path.exists(full_path):
        print(f"Hata: {full_path} dosyası bulunamadı!")
        return False
    
    # Dosyayı oku
    with open(full_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Rol kontrollerini düzelt: 3 -> 4 
    old_content = content
    content = content.replace("current_user.role == 3", "current_user.role == 4")
    
    # Değişiklik var mı kontrol et
    if content != old_content:
        print("Rol kontrolleri düzeltildi: current_user.role == 3 -> current_user.role == 4")
        # Değişiklikleri kaydet
        with open(full_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Değişiklikler kaydedildi!")
        return True
    else:
        print("Zaten tüm kontroller doğru görünüyor.")
        return False

if __name__ == "__main__":
    print("DÖF rol düzeltme aracı başlatılıyor...")
    try:
        success = fix_template_roles()
        if success:
            print("İşlem başarıyla tamamlandı! Template üzerindeki rol kontrolleri güncellendi.")
        else:
            print("Değişiklik yapılmadı.")
    except Exception as e:
        print(f"Bir hata oluştu: {e}")
