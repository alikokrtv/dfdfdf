"""
SQLite'dan MySQL'e veri aktarma scripti
Bu script mevcut SQLite veritabanından verileri alıp MySQL'e aktarır.
"""
import os
import sys
from app import app, db
from models import *
import pymysql
import sqlite3
from sqlalchemy import create_engine
from flask_migrate import Migrate

# Önceki veritabanı (SQLite) bağlantı yolunu kaydet
SQLITE_DB_PATH = 'dof.db'

def create_mysql_db():
    """MySQL veritabanını oluştur"""
    try:
        # Root bağlantısı ile veritabanını oluştur
        conn = pymysql.connect(
            host='localhost',
            user='root',
            password='255223'
        )
        cursor = conn.cursor()
        
        # Veritabanını oluştur (eğer yoksa)
        cursor.execute('CREATE DATABASE IF NOT EXISTS dof_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        
        print("MySQL veritabanı başarıyla oluşturuldu.")
        conn.close()
        return True
    except Exception as e:
        print(f"MySQL veritabanı oluşturulurken hata: {e}")
        return False

def setup_migrations():
    """Flask-Migrate ile tabloları oluştur"""
    try:
        # Migrations nesnesini oluştur
        migrate = Migrate(app, db)
        
        # MySQL'de kullanılacak veritabanı URL'sini ayarla
        app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:255223@localhost/dof_db'
        
        # Şimdi modellere dayanarak veritabanı şemasını oluştur
        with app.app_context():
            db.create_all()
            
        print("MySQL tabloları başarıyla oluşturuldu.")
        return True
    except Exception as e:
        print(f"MySQL tabloları oluşturulurken hata: {e}")
        return False

def migrate_data():
    """SQLite'dan MySQL'e verileri aktar"""
    try:
        # SQLite bağlantısı
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # MySQL engine oluştur
        mysql_engine = create_engine('mysql+pymysql://root:255223@localhost/dof_db')
        
        # Tüm tabloları listele
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = sqlite_cursor.fetchall()
        
        for table in tables:
            table_name = table[0]
            if table_name.startswith('sqlite_') or table_name == 'alembic_version':
                continue  # SQLite sistem tablolarını atla
                
            print(f"'{table_name}' tablosu aktarılıyor...")
            
            # Tablodaki tüm verileri al
            sqlite_cursor.execute(f"SELECT * FROM {table_name}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  '{table_name}' tablosunda veri yok.")
                continue
                
            # Sütun isimlerini al
            sqlite_cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [column[1] for column in sqlite_cursor.fetchall()]
            
            # Her satırı MySQL'e ekle
            for row in rows:
                # Sütun isimleri ve değerleri birleştir
                column_str = ", ".join(columns)
                placeholders = ", ".join(["%s"] * len(columns))
                
                # SQL insert sorgusu oluştur
                insert_query = f"INSERT INTO {table_name} ({column_str}) VALUES ({placeholders})"
                
                # MySQL'e ekle
                with mysql_engine.connect() as conn:
                    conn.execute(insert_query, row)
            
            print(f"  '{table_name}' tablosundaki {len(rows)} satır başarıyla aktarıldı.")
        
        sqlite_conn.close()
        print("Tüm veriler başarıyla MySQL'e aktarıldı.")
        return True
        
    except Exception as e:
        print(f"Veri aktarımı sırasında hata: {e}")
        return False

def main():
    print("SQLite'dan MySQL'e veri aktarım aracı")
    print("-" * 40)
    
    # 1. MySQL veritabanı oluştur
    if not create_mysql_db():
        print("MySQL veritabanı oluşturulamadı. İşlem durduruluyor.")
        return
        
    # 2. MySQL tabloları oluştur
    if not setup_migrations():
        print("MySQL tabloları oluşturulamadı. İşlem durduruluyor.")
        return
        
    # 3. Verileri SQLite'dan MySQL'e aktar
    response = input("Verileri SQLite'dan MySQL'e aktarmak istiyor musunuz? (E/H): ")
    if response.lower() == 'e':
        if not migrate_data():
            print("Veri aktarımı başarısız oldu.")
            return
    
    print("\nİşlem tamamlandı! Artık uygulamanız MySQL ile çalışmaya hazır.")
    print("config.py dosyasındaki veritabanı bağlantısının MySQL'e ayarlandığından emin olun.")

if __name__ == "__main__":
    main()
