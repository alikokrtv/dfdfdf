"""
Railway'den yerel MySQL veritabanına veri aktarma scripti
"""
import os
import sys
import pymysql
import time

# Railway bağlantı bilgileri (mevcut ortam değişkeninden)
RAILWAY_URL = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:TYaiJjHWFzFpLjizmCzEUQtnSKxBttJe@yamanote.proxy.rlwy.net:27282/railway')

# Railway bilgilerini parçalara ayır
railway_parts = RAILWAY_URL.replace('mysql+pymysql://', '').split('@')
railway_user_pass = railway_parts[0].split(':')
railway_host_port_db = railway_parts[1].split('/')

RAILWAY_USER = railway_user_pass[0]
RAILWAY_PASSWORD = railway_user_pass[1]
RAILWAY_HOST_PORT = railway_host_port_db[0].split(':')
RAILWAY_HOST = RAILWAY_HOST_PORT[0]
RAILWAY_PORT = int(RAILWAY_HOST_PORT[1])
RAILWAY_DB = railway_host_port_db[1]

# Yerel MySQL bağlantı bilgileri
LOCAL_HOST = 'localhost'
LOCAL_USER = 'root'
LOCAL_PASSWORD = '255223'
LOCAL_DB_NAME = 'dof_db'
LOCAL_PORT = 3306

def connect_to_railway():
    """Railway veritabanına bağlan"""
    print("1. Railway veritabanına bağlanılıyor...")
    try:
        railway_conn = pymysql.connect(
            host=RAILWAY_HOST,
            port=RAILWAY_PORT,
            user=RAILWAY_USER,
            password=RAILWAY_PASSWORD,
            database=RAILWAY_DB
        )
        print("   ✓ Railway veritabanına başarıyla bağlanıldı.")
        return railway_conn
    except Exception as e:
        print(f"   ✗ Railway veritabanına bağlanırken hata: {e}")
        sys.exit(1)

def connect_to_local():
    """Yerel MySQL veritabanına bağlan"""
    print("2. Yerel MySQL veritabanına bağlanılıyor...")
    try:
        local_conn = pymysql.connect(
            host=LOCAL_HOST,
            port=LOCAL_PORT,
            user=LOCAL_USER,
            password=LOCAL_PASSWORD
        )
        
        local_cursor = local_conn.cursor()
        
        # Veritabanını oluştur (eğer yoksa)
        local_cursor.execute(f"CREATE DATABASE IF NOT EXISTS {LOCAL_DB_NAME} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        local_conn.commit()
        
        # Veritabanını kullan
        local_cursor.execute(f"USE {LOCAL_DB_NAME}")
        local_conn.commit()
        
        print("   ✓ Yerel MySQL veritabanına başarıyla bağlanıldı.")
        return local_conn
    except Exception as e:
        print(f"   ✗ Yerel MySQL veritabanına bağlanırken hata: {e}")
        sys.exit(1)

def get_tables(conn):
    """Veritabanındaki tüm tabloları al"""
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tables = [table[0] for table in cursor.fetchall()]
    cursor.close()
    return tables

def get_table_schema(conn, table):
    """Tablo şemasını al"""
    cursor = conn.cursor()
    cursor.execute(f"DESCRIBE `{table}`")
    schema = cursor.fetchall()
    cursor.close()
    return schema

def recreate_table(conn, table, schema):
    """Tabloyu yeniden oluştur"""
    cursor = conn.cursor()
    
    # Tabloyu sil
    cursor.execute(f"DROP TABLE IF EXISTS `{table}`")
    
    # Tablo oluştur
    columns = []
    primary_keys = []
    
    for col in schema:
        col_name = col[0]
        col_type = col[1]
        nullable = "NULL" if col[2] == "YES" else "NOT NULL"
        key = col[3]
        default = f"DEFAULT {col[4]}" if col[4] is not None else ""
        extra = col[5]
        
        column_def = f"`{col_name}` {col_type} {nullable}"
        if default:
            column_def += f" {default}"
        if extra:
            column_def += f" {extra}"
            
        columns.append(column_def)
        
        if key == "PRI":
            primary_keys.append(f"`{col_name}`")
    
    # Primary key tanımı
    if primary_keys:
        columns.append(f"PRIMARY KEY ({', '.join(primary_keys)})")
    
    # Tablo oluştur
    create_query = f"CREATE TABLE `{table}` (\n  {',\n  '.join(columns)}\n) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci"
    cursor.execute(create_query)
    
    cursor.close()
    conn.commit()

def transfer_data(src_conn, dest_conn, table):
    """Tablodan veri aktar"""
    src_cursor = src_conn.cursor()
    dest_cursor = dest_conn.cursor()
    
    # Tablo verilerini al
    src_cursor.execute(f"SELECT * FROM `{table}`")
    rows = src_cursor.fetchall()
    
    if not rows:
        print(f"     - '{table}' tablosunda veri yok.")
        src_cursor.close()
        dest_cursor.close()
        return 0
    
    # Sütun bilgilerini al
    src_cursor.execute(f"DESCRIBE `{table}`")
    columns = [col[0] for col in src_cursor.fetchall()]
    column_str = ", ".join([f"`{col}`" for col in columns])
    
    # Mevcut verileri temizle
    dest_cursor.execute(f"TRUNCATE TABLE `{table}`")
    dest_conn.commit()
    
    # Her satırı aktar
    for row in rows:
        # Yer tutucu listesi
        placeholders = ", ".join(["%s"] * len(columns))
        
        # SQL sorgusu
        insert_query = f"INSERT INTO `{table}` ({column_str}) VALUES ({placeholders})"
        
        # Sorguyu çalıştır
        dest_cursor.execute(insert_query, row)
    
    # Değişiklikleri kaydet
    dest_conn.commit()
    
    row_count = len(rows)
    src_cursor.close()
    dest_cursor.close()
    return row_count

def update_config_py():
    """config.py dosyasını güncelle (eğer zaten yerel yapılandırma aktif değilse)"""
    print("5. config.py dosyası kontrol ediliyor...")
    
    try:
        config_path = 'config.py'
        
        # Dosyayı oku
        with open(config_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        # Dosya içeriğinde aktif yerel bağlantı kontrolü
        if "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:255223@localhost/dof_db')" in content:
            print("   ✓ config.py dosyası zaten yerel MySQL yapılandırmasını kullanıyor.")
            return True
        
        # Railway yapılandırmasından yerel yapılandırmaya geçiş
        content = content.replace(
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:TYaiJjHWFzFpLjizmCzEUQtnSKxBttJe@yamanote.proxy.rlwy.net:27282/railway')",
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:TYaiJjHWFzFpLjizmCzEUQtnSKxBttJe@yamanote.proxy.rlwy.net:27282/railway')"
        )
        
        # SQLite yapılandırmasını kapat
        content = content.replace(
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')",
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///dof.db')"
        )
        
        # Yerel MySQL yapılandırmasını etkinleştir
        content = content.replace(
            "# SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:255223@localhost/dof_db')",
            "SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'mysql+pymysql://root:255223@localhost/dof_db')"
        )
        
        # Dosyayı yaz
        with open(config_path, 'w', encoding='utf-8') as file:
            file.write(content)
        
        print("   ✓ config.py dosyası yerel MySQL yapılandırmasını kullanacak şekilde güncellendi.")
        return True
    except Exception as e:
        print(f"   ✗ config.py güncellenirken hata: {e}")
        return False

def main():
    print("\n==== Railway'den Yerel MySQL'e Veri Aktarma Aracı ====\n")
    
    try:
        # Adım 1: Railway veritabanına bağlan
        railway_conn = connect_to_railway()
        
        # Adım 2: Yerel MySQL veritabanına bağlan
        local_conn = connect_to_local()
        
        # Adım 3: Railway tablolarını al
        print("3. Railway tabloları alınıyor...")
        railway_tables = get_tables(railway_conn)
        print(f"   ℹ Bulunan tablolar: {', '.join(railway_tables)}")
        
        total_tables = len(railway_tables)
        total_rows = 0
        
        # Adım 4: Her tablo için şema ve veri aktarımı yap
        print("4. Tablolar ve veriler aktarılıyor...")
        for i, table in enumerate(railway_tables, 1):
            print(f"   ℹ [{i}/{total_tables}] '{table}' tablosu işleniyor...")
            
            # Şemayı al
            schema = get_table_schema(railway_conn, table)
            
            # Tabloyu yerel veritabanında oluştur
            print(f"     - '{table}' tablosu yeniden oluşturuluyor...")
            recreate_table(local_conn, table, schema)
            
            # Verileri aktar
            print(f"     - '{table}' tablosu verileri aktarılıyor...")
            row_count = transfer_data(railway_conn, local_conn, table)
            total_rows += row_count
            
            print(f"     ✓ {row_count} satır '{table}' tablosuna aktarıldı.")
        
        # Adım 5: config.py dosyasını güncelle
        update_config_py()
        
        print(f"\n   ✅ Toplam {total_tables} tablo ve {total_rows} satır başarıyla aktarıldı.")
        
        print("\n==== İşlem Başarıyla Tamamlandı! ====\n")
        print("Uygulamanız artık yerel MySQL veritabanını kullanmaya hazır.")
        print("Ortam değişkenini temizleyip uygulamayı yeniden başlatın:")
        print("1. Komut satırında: set DATABASE_URL=")
        print("2. Uygulamayı başlatın: python main.py")
        
    except Exception as e:
        print(f"Beklenmeyen bir hata oluştu: {e}")
    finally:
        # Bağlantıları kapat
        if 'railway_conn' in locals():
            railway_conn.close()
        if 'local_conn' in locals():
            local_conn.close()

if __name__ == "__main__":
    main()
