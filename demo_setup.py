#!/usr/bin/env python3
"""
Demo Environment Setup Script
Bu script, yeni subdomain'ler için demo ortamı hazırlar
"""

import os
import shutil
import sqlite3
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash
import json

class DemoSetup:
    def __init__(self, subdomain_name, base_path="/home/domains"):
        self.subdomain_name = subdomain_name
        self.demo_path = os.path.join(base_path, subdomain_name)
        self.db_path = os.path.join(self.demo_path, "demo.db")
        
    def create_demo_environment(self):
        """Demo ortamını oluştur"""
        try:
            # 1. Demo dizinini oluştur
            os.makedirs(self.demo_path, exist_ok=True)
            
            # 2. Uygulama dosyalarını kopyala
            self.copy_application_files()
            
            # 3. Demo veritabanını oluştur
            self.create_demo_database()
            
            # 4. Demo verilerini ekle
            self.populate_demo_data()
            
            # 5. Demo konfigürasyonu oluştur
            self.create_demo_config()
            
            print(f"✅ Demo ortamı başarıyla oluşturuldu: {self.subdomain_name}")
            return True
            
        except Exception as e:
            print(f"❌ Demo ortamı oluşturulurken hata: {str(e)}")
            return False
    
    def copy_application_files(self):
        """Uygulama dosyalarını demo dizinine kopyala"""
        source_files = [
            "app.py", "config.py", "models.py", "forms.py",
            "routes/", "templates/", "static/", "utils.py"
        ]
        
        for file_or_dir in source_files:
            source = os.path.join(os.getcwd(), file_or_dir)
            dest = os.path.join(self.demo_path, file_or_dir)
            
            if os.path.isdir(source):
                shutil.copytree(source, dest, dirs_exist_ok=True)
            elif os.path.isfile(source):
                shutil.copy2(source, dest)
    
    def create_demo_database(self):
        """Demo için SQLite veritabanı oluştur"""
        # SQLite kullanarak basit demo DB oluştur
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Temel tabloları oluştur
        demo_tables = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(80) UNIQUE NOT NULL,
            email VARCHAR(120) UNIQUE NOT NULL,
            password_hash VARCHAR(128),
            first_name VARCHAR(50),
            last_name VARCHAR(50),
            role INTEGER DEFAULT 5,
            active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            manager_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        
        CREATE TABLE IF NOT EXISTS dofs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            status INTEGER DEFAULT 1,
            created_by INTEGER,
            department_id INTEGER,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        cursor.executescript(demo_tables)
        conn.commit()
        conn.close()
    
    def populate_demo_data(self):
        """Demo verilerini ekle"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Demo kullanıcıları
        demo_users = [
            ("demo_admin", "admin@demo.com", generate_password_hash("demo123"), "Demo", "Admin", 1),
            ("kalite_mgr", "kalite@demo.com", generate_password_hash("demo123"), "Kalite", "Yöneticisi", 2),
            ("dept_mgr", "departman@demo.com", generate_password_hash("demo123"), "Departman", "Yöneticisi", 4),
            ("kullanici", "kullanici@demo.com", generate_password_hash("demo123"), "Demo", "Kullanıcı", 5)
        ]
        
        cursor.executemany("""
            INSERT INTO users (username, email, password_hash, first_name, last_name, role)
            VALUES (?, ?, ?, ?, ?, ?)
        """, demo_users)
        
        # Demo departmanları
        demo_departments = [
            ("Kalite Departmanı", "Kalite kontrol ve iyileştirme", 2),
            ("Üretim Departmanı", "Üretim süreçleri", 3),
            ("Satış Departmanı", "Satış ve pazarlama", 3)
        ]
        
        cursor.executemany("""
            INSERT INTO departments (name, description, manager_id)
            VALUES (?, ?, ?)
        """, demo_departments)
        
        # Demo DÖF'ler
        demo_dofs = [
            ("Ürün Kalite Sorunu", "Müşteri şikayeti sonucu tespit edilen kalite sorunu", 2, 1, 2),
            ("Üretim Hattı Arızası", "Makine arızası nedeniyle üretim durması", 3, 2, 3),
            ("Müşteri Memnuniyetsizliği", "Teslimat gecikmesi şikayeti", 1, 3, 1)
        ]
        
        cursor.executemany("""
            INSERT INTO dofs (title, description, status, created_by, department_id)
            VALUES (?, ?, ?, ?, ?)
        """, demo_dofs)
        
        conn.commit()
        conn.close()
    
    def create_demo_config(self):
        """Demo konfigürasyon dosyası oluştur"""
        demo_config = f"""
import os

class DemoConfig:
    SECRET_KEY = 'demo-secret-key-{self.subdomain_name}'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///{self.db_path}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Demo modunu etkinleştir
    DEMO_MODE = True
    DEMO_SUBDOMAIN = '{self.subdomain_name}'
    
    # E-posta ayarları (demo için devre dışı)
    MAIL_SERVER = None
    MAIL_PORT = 587
    MAIL_USE_TLS = False
    MAIL_USERNAME = None
    MAIL_PASSWORD = None
    
    # Demo sınırlamaları
    MAX_USERS = 10
    MAX_DOFS = 50
    DEMO_DURATION_HOURS = 24
"""
        
        config_path = os.path.join(self.demo_path, "demo_config.py")
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write(demo_config)
    
    def create_demo_info_file(self):
        """Demo bilgi dosyası oluştur"""
        demo_info = {
            "subdomain": self.subdomain_name,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(hours=24)).isoformat(),
            "demo_users": [
                {"username": "demo_admin", "password": "demo123", "role": "Admin"},
                {"username": "kalite_mgr", "password": "demo123", "role": "Kalite Yöneticisi"},
                {"username": "dept_mgr", "password": "demo123", "role": "Departman Yöneticisi"},
                {"username": "kullanici", "password": "demo123", "role": "Kullanıcı"}
            ],
            "features": [
                "DÖF oluşturma ve yönetimi",
                "Departman yönetimi",
                "Kullanıcı rolleri",
                "Raporlama",
                "E-posta bildirimleri (demo için devre dışı)"
            ]
        }
        
        info_path = os.path.join(self.demo_path, "demo_info.json")
        with open(info_path, 'w', encoding='utf-8') as f:
            json.dump(demo_info, f, indent=2, ensure_ascii=False)

def main():
    """Ana fonksiyon - komut satırından kullanım için"""
    import sys
    
    if len(sys.argv) != 2:
        print("Kullanım: python demo_setup.py <subdomain_name>")
        print("Örnek: python demo_setup.py demo")
        sys.exit(1)
    
    subdomain_name = sys.argv[1]
    demo_setup = DemoSetup(subdomain_name)
    
    if demo_setup.create_demo_environment():
        print(f"\n🎉 Demo ortamı hazır!")
        print(f"📍 Subdomain: {subdomain_name}.dofyonetimi.pro")
        print(f"👤 Demo kullanıcıları:")
        print(f"   - admin: demo_admin / demo123")
        print(f"   - kalite: kalite_mgr / demo123")
        print(f"   - departman: dept_mgr / demo123")
        print(f"   - kullanıcı: kullanici / demo123")
        print(f"⏰ Demo süresi: 24 saat")
    else:
        print("❌ Demo ortamı oluşturulamadı!")
        sys.exit(1)

if __name__ == "__main__":
    main()
