"""
SQLite'dan MySQL'e veri aktarma scripti - Adım adım
Bu script mevcut SQLite veritabanından verileri alıp MySQL'e aktarır.
"""
import os
import sys
import pymysql
import sqlite3
import time

# Bağlantı bilgileri
MYSQL_HOST = 'localhost'
MYSQL_USER = 'root'
MYSQL_PASSWORD = '255223'
MYSQL_DB_NAME = 'dof_db'

# SQLite veritabanı
SQLITE_DB_PATH = 'dof.db'

def create_mysql_db():
    """MySQL veritabanını oluştur"""
    print("1. MySQL veritabanı oluşturuluyor...")
    
    try:
        # Root bağlantısı ile veritabanı oluştur
        conn = pymysql.connect(
            host=MYSQL_HOST,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD
        )
        cursor = conn.cursor()
        
        # Eğer varsa veritabanını sil
        cursor.execute(f'DROP DATABASE IF EXISTS {MYSQL_DB_NAME}')
        conn.commit()
        
        # Veritabanını oluştur
        cursor.execute(f'CREATE DATABASE {MYSQL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci')
        conn.commit()
        
        print("   ✓ MySQL veritabanı başarıyla oluşturuldu.")
        
        # Veritabanını kullan
        cursor.execute(f'USE {MYSQL_DB_NAME}')
        conn.commit()
        
        cursor.close()
        # Bağlantıyı kapatma - devam eden işlemler için açık kalması gerekiyor
        return conn
    except Exception as e:
        print(f"   ✗ MySQL veritabanı oluşturulurken hata: {e}")
        sys.exit(1)

def extract_sqlite_schema():
    """SQLite şemasını analiz et ve MySQL için tablo oluşturma scriptlerini hazırla"""
    print("2. SQLite şeması analiz ediliyor...")
    
    try:
        # SQLite bağlantısı
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Tüm tabloları al
        sqlite_cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';")
        tables = [table[0] for table in sqlite_cursor.fetchall()]
        print(f"   ℹ Bulunan tablolar: {', '.join(tables)}")
        
        # Her tablo için şemayı ve verileri al
        schemas = {}
        for table in tables:
            # Tablo yapısını al
            sqlite_cursor.execute(f"PRAGMA table_info({table})")
            columns = sqlite_cursor.fetchall()
            
            # MySQL için CREATE TABLE ifadesini oluştur
            mysql_columns = []
            primary_keys = []
            for col in columns:
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
                
                mysql_columns.append(column_def)
                
                # Primary key ise listeye ekle
                if is_pk:
                    primary_keys.append(f"`{col_name}`")
            
            # Primary key tanımını ekle
            if primary_keys:
                mysql_columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
            
            # Tablo oluşturma SQL'ini kaydet
            create_table_sql = f"CREATE TABLE `{table}` (\n  {',\n  '.join(mysql_columns)}\n)"
            schemas[table] = {
                'create_sql': create_table_sql,
                'columns': [col[1] for col in columns]
            }
        
        sqlite_conn.close()
        print("   ✓ SQLite şeması başarıyla analiz edildi.")
        return schemas
    except Exception as e:
        print(f"   ✗ SQLite şeması analiz edilirken hata: {e}")
        sys.exit(1)

def create_mysql_tables(conn, schemas):
    """MySQL tablolarını oluştur"""
    print("3. MySQL tabloları oluşturuluyor...")
    
    try:
        cursor = conn.cursor()
        
        for table, schema in schemas.items():
            print(f"   ℹ '{table}' tablosu oluşturuluyor...")
            cursor.execute(schema['create_sql'])
            conn.commit()
        
        cursor.close()
        print("   ✓ MySQL tabloları başarıyla oluşturuldu.")
        return True
    except Exception as e:
        print(f"   ✗ MySQL tabloları oluşturulurken hata: {e}")
        conn.rollback()
        sys.exit(1)

def migrate_data(conn, schemas):
    """SQLite'dan MySQL'e verileri aktar"""
    print("4. Veriler aktarılıyor...")
    
    try:
        # SQLite bağlantısı
        sqlite_conn = sqlite3.connect(SQLITE_DB_PATH)
        sqlite_cursor = sqlite_conn.cursor()
        
        mysql_cursor = conn.cursor()
        
        for table, schema in schemas.items():
            print(f"   ℹ '{table}' tablosu verileri aktarılıyor...")
            
            # Tablo verilerini al
            sqlite_cursor.execute(f"SELECT * FROM {table}")
            rows = sqlite_cursor.fetchall()
            
            if not rows:
                print(f"     - '{table}' tablosunda veri yok.")
                continue
            
            # Sütun listesi
            columns = schema['columns']
            column_str = ", ".join([f"`{col}`" for col in columns])
            
            # Her satırı MySQL'e aktar
            for row in rows:
                # NULL değerleri için None ekle
                row = [None if val == 'NULL' else val for val in row]
                
                # Yer tutucu listesi
                placeholders = ", ".join(["%s"] * len(columns))
                
                # SQL sorgusu
                insert_query = f"INSERT INTO `{table}` ({column_str}) VALUES ({placeholders})"
                
                # Sorguyu çalıştır
                mysql_cursor.execute(insert_query, row)
            
            # Değişiklikleri kaydet
            conn.commit()
            print(f"     ✓ {len(rows)} satır '{table}' tablosuna aktarıldı.")
        
        sqlite_conn.close()
        mysql_cursor.close()
        
        print("   ✓ Tüm veriler başarıyla aktarıldı.")
        return True
    except Exception as e:
        print(f"   ✗ Veri aktarımı sırasında hata: {e}")
        conn.rollback()
        return False

def update_config_py():
    """config.py dosyasını MySQL kullanacak şekilde güncelle"""
    print("5. config.py dosyası güncelleniyor...")
    
    try:
        config_path = 'config.py'
        
        # Dosyayı oku
        with open(config_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # SQLite satırlarını yorum satırı yap
        content = content.replace(
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')", 
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')"
        )
        
        # MySQL satırlarını aktif hale getir
        content = content.replace(
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:255223@localhost/dof_db')",
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:255223@localhost/dof_db')"
        )
        
        # Dosyayı yaz
        with open(config_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("   ✓ config.py dosyası başarıyla güncellendi.")
        return True
    except Exception as e:
        print(f"   ✗ config.py güncellenirken hata: {e}")
        return False

def main():
    print("\n==== SQLite'dan MySQL'e Geçiş Aracı ====\n")
    
    conn = None
    try:
        # Adım 1: MySQL veritabanı oluştur
        conn = create_mysql_db()
        
        # Adım 2: SQLite şemasını analiz et
        schemas = extract_sqlite_schema()
        
        # Adım 3: MySQL tablolarını oluştur
        create_mysql_tables(conn, schemas)
        
        # Adım 4: Verileri aktar
        success = migrate_data(conn, schemas)
        
        if success:
            # Adım 5: config.py dosyasını güncelle
            update_config_py()
            
            print("\n==== İşlem Başarıyla Tamamlandı! ====\n")
            print("Uygulamanız artık MySQL veritabanını kullanmaya hazır.")
            print("Uygulamayı 'python main.py' komutuyla başlatabilirsiniz.")
        else:
            print("\n==== İşlem Kısmen Tamamlandı ====\n")
            print("Veri aktarımı sırasında sorun oluştu, lütfen hata mesajlarını kontrol edin.")
            
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    main()
