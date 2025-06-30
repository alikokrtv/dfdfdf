"""
Railway MySQL veritabanına veri aktarma scripti
SQLite veya yerel MySQL veritabanından Railway'deki MySQL veritabanına veri aktarımı yapar
"""
import os
import sys
import pymysql
import sqlite3
from datetime import datetime

# Railway MySQL bağlantı bilgileri
MYSQL_HOST = 'yamanote.proxy.rlwy.net'
MYSQL_PORT = 27282
MYSQL_USER = 'root'
MYSQL_PASSWORD = 'TYaiJjHWFzFpLjizmCzEUQtnSKxBttJe'
MYSQL_DB_NAME = 'railway'

# SQLite veritabanı (eğer SQLite'dan aktarım yapılacaksa)
SQLITE_DB_PATH = 'dof.db'

def create_tables_from_local_mysql():
    """Yerel MySQL'deki tabloları Railway MySQL'e aktarır"""
    try:
        print("\n=== Yerel MySQL'den Railway MySQL'e Veri Aktarımı ===\n")
        
        # Yerel MySQL bağlantısı
        local_conn = pymysql.connect(
            host='localhost',
            user='root',
            password='255223',
            database='dof_db'
        )
        local_cursor = local_conn.cursor()
        
        # Railway MySQL bağlantısı
        railway_conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        railway_cursor = railway_conn.cursor()
        
        # Railway'de veritabanını oluştur (eğer yoksa)
        railway_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        railway_conn.commit()
        
        # Veritabanını kullan
        railway_cursor.execute(f"USE {MYSQL_DB_NAME}")
        
        # Tüm tabloları listele
        local_cursor.execute("SHOW TABLES")
        tables = [table[0] for table in local_cursor.fetchall()]
        
        print(f"Bulunan tablolar: {', '.join(tables)}")
        
        for table in tables:
            print(f"\nTablo işleniyor: {table}")
            
            # Tablo yapısını al
            local_cursor.execute(f"SHOW CREATE TABLE {table}")
            create_table_sql = local_cursor.fetchone()[1]
            
            # Önce tabloyu sil (eğer varsa)
            railway_cursor.execute(f"DROP TABLE IF EXISTS {table}")
            railway_conn.commit()
            
            # Tabloyu oluştur
            print(f"  - Tablo oluşturuluyor: {table}")
            railway_cursor.execute(create_table_sql)
            railway_conn.commit()
            
            # Verileri al
            local_cursor.execute(f"SELECT * FROM {table}")
            rows = local_cursor.fetchall()
            
            if not rows:
                print(f"  - {table} tablosunda veri yok")
                continue
                
            # Sütun bilgilerini al
            local_cursor.execute(f"SHOW COLUMNS FROM {table}")
            columns = [column[0] for column in local_cursor.fetchall()]
            
            # Verileri aktarma
            print(f"  - {len(rows)} satır veri aktarılıyor: {table}")
            
            for row in rows:
                # Değerleri hazırla
                placeholders = ', '.join(['%s'] * len(columns))
                column_str = ', '.join([f"`{col}`" for col in columns])
                query = f"INSERT INTO {table} ({column_str}) VALUES ({placeholders})"
                
                # Veriyi ekle
                railway_cursor.execute(query, row)
            
            railway_conn.commit()
            print(f"  - {len(rows)} satır başarıyla aktarıldı: {table}")
        
        local_conn.close()
        railway_conn.close()
        
        print("\n=== Veri aktarımı başarıyla tamamlandı ===")
        return True
        
    except Exception as e:
        print(f"Hata: {e}")
        return False

def create_tables_from_sqlite():
    """SQLite veritabanındaki tabloları Railway MySQL'e aktarır"""
    try:
        print("\n=== SQLite'dan Railway MySQL'e Veri Aktarımı ===\n")
        
        # SQLite bağlantısı
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Railway MySQL bağlantısı
        railway_conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        railway_cursor = railway_conn.cursor()
        
        # Railway'de veritabanını oluştur (eğer yoksa)
        railway_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        railway_conn.commit()
        
        # Veritabanını kullan
        railway_cursor.execute(f"USE {MYSQL_DB_NAME}")
        
        # Tüm tabloları listele
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [table[0] for table in sqlite_cursor.fetchall()]
        
        print(f"Bulunan tablolar: {', '.join(tables)}")
        
        for table in tables:
            print(f"\nTablo işleniyor: {table}")
            
            # Tablo yapısını al
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns_info = sqlite_cursor.fetchall()
            
            # MySQL için sütun tanımlarını oluştur
            columns = []
            primary_keys = []
            
            for col in columns_info:
                col_id, col_name, col_type, not_null, default_value, is_pk = col
                
                # Veri tipi dönüşümleri
                if col_type.upper() in ('INTEGER', 'INT'):
                    mysql_type = 'INT'
                elif col_type.upper() == 'REAL':
                    mysql_type = 'FLOAT'
                elif col_type.upper() in ('TEXT', 'CLOB'):
                    mysql_type = 'TEXT'
                elif 'CHAR' in col_type.upper():
                    mysql_type = 'VARCHAR(255)'
                elif 'BLOB' in col_type.upper():
                    mysql_type = 'BLOB'
                elif 'BOOLEAN' in col_type.upper():
                    mysql_type = 'BOOLEAN'
                elif 'TIMESTAMP' in col_type.upper() or 'DATETIME' in col_type.upper():
                    mysql_type = 'DATETIME'
                elif 'DATE' in col_type.upper():
                    mysql_type = 'DATE'
                else:
                    mysql_type = 'TEXT'
                
                # Sütun tanımını oluştur
                column_def = f"`{col_name}` {mysql_type}"
                
                if not_null:
                    column_def += " NOT NULL"
                    
                # Default değeri ekle
                if default_value is not None:
                    if isinstance(default_value, str):
                        column_def += f" DEFAULT '{default_value}'".replace("'NULL'", "NULL")
                    else:
                        column_def += f" DEFAULT {default_value}"
                
                columns.append(column_def)
                
                # Primary key ise listeye ekle
                if is_pk:
                    primary_keys.append(f"`{col_name}`")
            
            # Primary key tanımını ekle
            if primary_keys:
                columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
            
            # Tablo oluşturma SQL'ini oluştur
            create_table_sql = f"CREATE TABLE `{table}` (\n  {',\n  '.join(columns)}\n)"
            
            # Önce tabloyu sil (eğer varsa)
            railway_cursor.execute(f"DROP TABLE IF EXISTS {table}")
            railway_conn.commit()
            
            # Tabloyu oluştur
            print(f"  - Tablo oluşturuluyor: {table}")
            railway_cursor.execute(create_table_sql)
            railway_conn.commit()
            
            # Verileri al
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"  - {table} tablosunda veri yok")
                continue
                
            # Sütun isimlerini al
            column_names = [column[1] for column in columns_info]
            
            # Verileri aktarma
            print(f"  - {len(rows)} satır veri aktarılıyor: {table}")
            
            for row in rows:
                # NULL değerleri için None ekle
                row = [None if val == 'NULL' else val for val in row]
                
                # Değerleri hazırla
                placeholders = ', '.join(['%s'] * len(column_names))
                column_str = ', '.join([f"`{col}`" for col in column_names])
                query = f"INSERT INTO {table} ({column_str}) VALUES ({placeholders})"
                
                # Veriyi ekle
                try:
                    railway_cursor.execute(query, row)
                except Exception as e:
                    print(f"    Veri eklenirken hata: {e}")
                    continue
            
            railway_conn.commit()
            print(f"  - Veriler başarıyla aktarıldı: {table}")
        
        sqlite_conn.close()
        railway_conn.close()
        
        print("\n=== Veri aktarımı başarıyla tamamlandı ===")
        return True
        
    except Exception as e:
        print(f"Hata: {e}")
        return False

def create_basic_tables():
    """Railway MySQL'de temel tabloları oluştur"""
    try:
        print("\n=== Railway MySQL'de Temel Tabloları Oluşturma ===\n")
        
        # Railway MySQL bağlantısı
        railway_conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        railway_cursor = railway_conn.cursor()
        
        # Railway'de veritabanını oluştur (eğer yoksa)
        railway_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        railway_conn.commit()
        
        # Veritabanını kullan
        railway_cursor.execute(f"USE {MYSQL_DB_NAME}")
        
        # Temel tabloları oluştur
        tables = [
            """
            CREATE TABLE IF NOT EXISTS `users` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `username` VARCHAR(50) NOT NULL,
              `password` VARCHAR(255) NOT NULL,
              `email` VARCHAR(100) NOT NULL,
              `first_name` VARCHAR(50),
              `last_name` VARCHAR(50),
              `role` INT NOT NULL DEFAULT 0,
              `department_id` INT,
              `phone` VARCHAR(20),
              `is_active` BOOLEAN NOT NULL DEFAULT TRUE,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`),
              UNIQUE KEY `username` (`username`),
              UNIQUE KEY `email` (`email`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS `departments` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `name` VARCHAR(100) NOT NULL,
              `description` TEXT,
              `manager_id` INT,
              `parent_id` INT,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS `dofs` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `title` VARCHAR(255) NOT NULL,
              `description` TEXT,
              `status` INT NOT NULL DEFAULT 0,
              `created_by` INT NOT NULL,
              `assigned_to` INT,
              `department_id` INT,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
              `closed_at` DATETIME,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """,
            """
            CREATE TABLE IF NOT EXISTS `system_logs` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `user_id` INT,
              `action` VARCHAR(100) NOT NULL,
              `details` TEXT,
              `ip_address` VARCHAR(45),
              `user_agent` TEXT,
              `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP,
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
            """
        ]
        
        for table_sql in tables:
            print("Tablo oluşturuluyor...")
            railway_cursor.execute(table_sql)
            railway_conn.commit()
        
        # Admin kullanıcısını oluştur
        admin_exists = railway_cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        
        if not admin_exists:
            print("Admin kullanıcısı oluşturuluyor...")
            railway_cursor.execute(
                "INSERT INTO users (username, password, email, first_name, last_name, role) VALUES (%s, %s, %s, %s, %s, %s)",
                ('admin', '$2b$12$lBC9V1XRKFU7o5xjsM05/OS0vOtIPhgkZH4brTjjLMGPVGX3OXqyG', 'alikokrtv@gmail.com', 'Admin', 'User', 2)  # Admin123
            )
            railway_conn.commit()
        
        # Kalite departmanını oluştur
        quality_exists = railway_cursor.execute("SELECT id FROM departments WHERE name = 'Kalite Yönetimi'")
        
        if not quality_exists:
            print("Kalite departmanı oluşturuluyor...")
            railway_cursor.execute(
                "INSERT INTO departments (name, description) VALUES (%s, %s)",
                ('Kalite Yönetimi', 'Kalite kontrol ve yönetimi')
            )
            railway_conn.commit()
        
        railway_conn.close()
        
        print("\n=== Temel tablolar başarıyla oluşturuldu ===")
        return True
        
    except Exception as e:
        print(f"Hata: {e}")
        return False

def main():
    print("\n===== Railway MySQL Deploy Aracı =====\n")
    print("1. SQLite'dan Railway MySQL'e veri aktarımı")
    print("2. Yerel MySQL'den Railway MySQL'e veri aktarımı")
    print("3. Railway MySQL'de temel tabloları oluştur")
    print("4. Çıkış")
    
    choice = input("\nSeçiminizi yapın (1-4): ")
    
    if choice == '1':
        create_tables_from_sqlite()
    elif choice == '2':
        create_tables_from_local_mysql()
    elif choice == '3':
        create_basic_tables()
    elif choice == '4':
        print("Çıkış yapılıyor...")
        return
    else:
        print("Geçersiz seçim. Lütfen 1-4 arasında bir değer girin.")
    
    print("\nİşlem tamamlandı!")

if __name__ == "__main__":
    main()
