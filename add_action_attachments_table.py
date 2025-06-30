#!/usr/bin/env python3
"""
Yorum Ekleri (ActionAttachment) tablosu oluşturma migration scripti
"""

from app import app, db
from models import ActionAttachment

def create_action_attachments_table():
    """ActionAttachment tablosunu oluştur"""
    with app.app_context():
        try:
            # Tabloyu oluştur
            db.create_all()
            
            print("✅ ActionAttachment tablosu başarıyla oluşturuldu.")
            print("📋 Tablo yapısı:")
            print("   - id (Primary Key)")
            print("   - action_id (Foreign Key -> dof_actions.id)")
            print("   - filename (dosya adı)")
            print("   - file_path (dosya yolu)")
            print("   - uploaded_by (Foreign Key -> users.id)")
            print("   - uploaded_at (yükleme tarihi)")
            print("   - file_size (dosya boyutu)")
            print("   - file_type (dosya tipi)")
            
        except Exception as e:
            print(f"❌ Hata oluştu: {e}")
            return False
            
    return True

if __name__ == "__main__":
    print("🚀 ActionAttachment tablosu migration başlatılıyor...")
    
    if create_action_attachments_table():
        print("✅ Migration tamamlandı!")
        print("")
        print("📝 Artık kullanıcılar yorumlarına dosya ekleyebilir:")
        print("   • Resim dosyaları (PNG, JPG, JPEG)")  
        print("   • PDF dökümanları")
        print("   • Office dosyaları (DOC, DOCX, XLS, XLSX)")
        print("")
        print("🔧 Yeni özellikler:")
        print("   • Yorum formunda dosya seçme alanı")
        print("   • İşlem geçmişinde eklerin görünümü")
        print("   • Dosya indirme linkleri")
        print("   • Güvenli dosya erişim kontrolü")
    else:
        print("❌ Migration başarısız!") 