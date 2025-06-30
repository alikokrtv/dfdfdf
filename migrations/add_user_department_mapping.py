"""
Çoklu departman yönetimi için UserDepartmentMapping tablosunun eklenmesi
"""
from flask import current_app
import sys
import os

# Proje ana dizinini sys.path'e ekle
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import UserDepartmentMapping
from datetime import datetime

def create_user_department_mapping_table():
    """Çoklu departman yönetimi için ara tabloyu oluştur"""
    with app.app_context():
        # Tablo zaten var mı kontrol et
        table_exists = False
        try:
            UserDepartmentMapping.query.limit(1).all()
            table_exists = True
            current_app.logger.info("UserDepartmentMapping tablosu zaten mevcut.")
        except Exception as e:
            current_app.logger.info(f"UserDepartmentMapping tablosu oluşturulacak: {str(e)}")
            
        if not table_exists:
            # Tablo yoksa oluştur
            current_app.logger.info("UserDepartmentMapping tablosu oluşturuluyor...")
            
            try:
                # SQLAlchemy model bilgisine göre tabloyu oluştur
                db.create_all()
                current_app.logger.info("UserDepartmentMapping tablosu başarıyla oluşturuldu.")
                return True
            except Exception as e:
                current_app.logger.error(f"UserDepartmentMapping tablosu oluşturma hatası: {str(e)}")
                return False
        return True

# Migration'u uygula
if __name__ == "__main__":
    create_user_department_mapping_table()
