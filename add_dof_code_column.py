import pymysql
import os

# MySQL bağlantı bilgileri
db_host = 'localhost'
db_user = 'root'
db_password = '255223'
db_name = 'dof_db'

try:
    # MySQL bağlantısı oluştur
    conn = pymysql.connect(
        host=db_host,
        user=db_user,
        password=db_password,
        database=db_name
    )
    cursor = conn.cursor()
    
    # Önce sütunun olup olmadığını kontrol et
    cursor.execute("SHOW COLUMNS FROM dofs LIKE 'code'")
    result = cursor.fetchone()
    
    if not result:
        # Sütun yoksa ekle
        cursor.execute("ALTER TABLE dofs ADD COLUMN code VARCHAR(20) UNIQUE NULL")
        conn.commit()
        print("'code' sütunu 'dofs' tablosuna başarıyla eklendi!")
    else:
        print("'code' sütunu zaten mevcut.")
        
    # Bağlantıyı kapat
    cursor.close()
    conn.close()
    
except Exception as e:
    print(f"Hata oluştu: {str(e)}")
    print("Lütfen MySQL servisinin çalıştığından ve bağlantı bilgilerinin doğru olduğundan emin olun.")

