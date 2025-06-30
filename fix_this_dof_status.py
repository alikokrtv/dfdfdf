#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tek DÖF için durum düzeltme scripti
DÖF'ü COMPLETED durumundan SOURCE_REVIEW durumuna geçirir
"""

from app import app, db
from models import DOF, DOFAction, DOFStatus
from datetime import datetime
import sys

def fix_single_dof(dof_id):
    """Belirtilen DÖF'ü kaynak değerlendirmesi aşamasına geçir"""
    
    with app.app_context():
        # DÖF'ü getir
        dof = DOF.query.get(dof_id)
        if not dof:
            print(f"❌ DÖF #{dof_id} bulunamadı!")
            return False
            
        print(f"📋 DÖF #{dof_id} mevcut durum: {DOFStatus.get_label(dof.status)} ({dof.status})")
        
        # Sadece COMPLETED durumundaki DÖF'leri düzelt
        if dof.status != DOFStatus.COMPLETED:
            print(f"⚠️ DÖF #{dof_id} COMPLETED durumunda değil, işlem yapılmıyor")
            return False
        
        try:
            # Durumu SOURCE_REVIEW olarak güncelle
            old_status = dof.status
            dof.status = DOFStatus.SOURCE_REVIEW
            
            # Yeni action kaydı oluştur
            action = DOFAction(
                dof_id=dof.id,
                user_id=1,  # Admin kullanıcısı
                action_type=2,  # Durum değişikliği
                comment="DÖF kaynak değerlendirmesi aşamasına manuel olarak taşındı",
                old_status=old_status,
                new_status=DOFStatus.SOURCE_REVIEW,
                created_at=datetime.now()
            )
            db.session.add(action)
            
            # Kaydet
            db.session.commit()
            
            print(f"✅ DÖF #{dof_id} durumu güncellendi: {DOFStatus.get_label(old_status)} → {DOFStatus.get_label(DOFStatus.SOURCE_REVIEW)}")
            return True
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Hata: {str(e)}")
            return False

if __name__ == "__main__":
    # DÖF ID'sini komut satırından al
    if len(sys.argv) > 1:
        dof_id = int(sys.argv[1])
    else:
        dof_id = int(input("DÖF ID girin: "))
    
    print(f"🔧 DÖF #{dof_id} için durum düzeltmesi başlıyor...")
    
    if fix_single_dof(dof_id):
        print("🎉 İşlem başarıyla tamamlandı!")
    else:
        print("�� İşlem başarısız!") 