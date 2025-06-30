from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text
import sys
import os

# Uygulama bağlamını oluştur
app = Flask(__name__)
app.config.from_pyfile('config.py')
db = SQLAlchemy(app)

def run_migration():
    """Dofs tablosuna code alanını ekleyen migrasyon betiği"""
    print("DOF tablosuna 'code' sütunu ekleme migrasyonu başlatılıyor...")
    
    try:
        # Veritabanı motorunu al
        dialect = db.engine.dialect.name
        
        # Uygun SQL komutunu oluştur (SQLite ve MySQL için farklı)
        if dialect == 'sqlite':
            sql = text("ALTER TABLE dofs ADD COLUMN code VARCHAR(20) UNIQUE")
            print("SQLite veritabanı tespit edildi. SQLite için ALTER TABLE komutu hazırlanıyor.")
        else:
            # MySQL veya diğer SQL motorları için
            sql = text("ALTER TABLE dofs ADD COLUMN code VARCHAR(20) UNIQUE NULL")
            print(f"{dialect} veritabanı tespit edildi. Uygun ALTER TABLE komutu hazırlanıyor.")
        
        # Komutu çalıştır
        with db.engine.connect() as connection:
            connection.execute(sql)
            connection.commit()
            print("Migrasyon başarıyla tamamlandı! 'code' sütunu 'dofs' tablosuna eklendi.")
            
        return True
    except Exception as e:
        print(f"Migrasyon sırasında hata oluştu: {str(e)}")
        return False

if __name__ == "__main__":
    with app.app_context():
        success = run_migration()
        sys.exit(0 if success else 1)
