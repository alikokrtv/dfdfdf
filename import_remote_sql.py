import os
import sys
from pathlib import Path
import pymysql
from pymysql.constants import CLIENT

PWD_PRIMARY = os.environ.get('DB_PASS_PRIMARY', '255223Rtv')
PWD_FALLBACK = os.environ.get('DB_PASS_FALLBACK', '255223')
USER = os.environ.get('DB_USER', 'root')
HOST = os.environ.get('DB_HOST', '127.0.0.1')
PORT = int(os.environ.get('DB_PORT', '3306'))
DB_NAME = os.environ.get('DB_NAME', 'dof_db')
RESET_DB = os.environ.get('RESET_DB', '0') == '1'

SQL_FILE = sys.argv[1] if len(sys.argv) > 1 else r"C:\Users\aliko\Desktop\uzaksunucusql.sql"

if not Path(SQL_FILE).exists():
    print(f"SQL dosyası bulunamadı: {SQL_FILE}")
    sys.exit(1)


def try_connect(password: str):
    try:
        conn = pymysql.connect(
            host=HOST,
            port=PORT,
            user=USER,
            password=password,
            autocommit=True,
            charset='utf8mb4',
            client_flag=CLIENT.MULTI_STATEMENTS,
        )
        return conn
    except Exception:
        return None


# Connect with primary, else fallback
conn = try_connect(PWD_PRIMARY)
used_password = PWD_PRIMARY
if conn is None:
    conn = try_connect(PWD_FALLBACK)
    used_password = PWD_FALLBACK

if conn is None:
    print("MySQL bağlantısı kurulamadı. Lütfen MySQL servisinin çalıştığından emin olun.")
    sys.exit(2)

print(f"MySQL'e bağlandı. Kullanılan şifre: {'PRIMARY' if used_password == PWD_PRIMARY else 'FALLBACK'}")

with conn.cursor() as cur, open(SQL_FILE, 'r', encoding='utf-8', errors='ignore') as f:
    if RESET_DB:
        try:
            cur.execute(f"DROP DATABASE IF EXISTS `{DB_NAME}`;")
        except Exception:
            pass

    # Create database fresh and use it
    cur.execute(f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
    cur.execute(f"USE `{DB_NAME}`;")

    # Disable FK checks globally for import
    try:
        cur.execute("SET FOREIGN_KEY_CHECKS=0;")
    except Exception:
        pass

    # Preprocess lines: remove control/metadata lines we don't need
    filtered_lines = []
    for raw in f:
        line = raw.rstrip('\r\n')
        if not line or line.startswith('-- '):
            continue
        if line.startswith('/*') or line.startswith('*/'):
            continue
        if line.startswith('/*!') and line.endswith('*/;'):
            # skip versioned MySQL commands
            continue
        if line.startswith('LOCK TABLES') or line.startswith('UNLOCK TABLES'):
            continue
        if 'ALTER TABLE' in line and ('DISABLE KEYS' in line or 'ENABLE KEYS' in line):
            continue
        filtered_lines.append(line)

    # Split into statements using current delimiter logic
    delimiter = ';'
    stmts = []
    buf = []
    for line in filtered_lines:
        if line.startswith('DELIMITER '):
            delimiter = line.split('DELIMITER ', 1)[1].strip()
            continue
        buf.append(line)
        current = '\n'.join(buf)
        if current.endswith(delimiter):
            stmt = current[: -len(delimiter)].strip()
            if stmt:
                stmts.append(stmt)
            buf = []
    # Add remaining
    if buf:
        stmts.append('\n'.join(buf).strip())

    # Separate by type
    drop_stmts = [s for s in stmts if s.upper().startswith('DROP TABLE')]
    create_stmts = [s for s in stmts if s.upper().startswith('CREATE TABLE')]
    other_stmts = [s for s in stmts if s not in drop_stmts + create_stmts]

    applied = 0
    total = len(stmts)

    # Execute DROPs (ignore errors)
    for s in drop_stmts:
        try:
            cur.execute(s)
            applied += 1
        except Exception:
            continue

    # Try CREATEs with retries to resolve FK order
    pending = create_stmts[:]
    for _ in range(5):  # up to 5 passes
        if not pending:
            break
        next_pending = []
        for s in pending:
            try:
                cur.execute(s)
                applied += 1
            except Exception as e:
                next_pending.append(s)
        if len(next_pending) == len(pending):
            # no progress
            break
        pending = next_pending

    # Execute remaining statements
    for s in other_stmts:
        try:
            cur.execute(s)
            applied += 1
        except Exception as e:
            # print and continue
            print(f"Hata: {str(e)[:200]}")
            continue

    try:
        cur.execute("SET FOREIGN_KEY_CHECKS=1;")
    except Exception:
        pass

print(f"İşlem tamamlandı. Uygulanan komut sayısı: {applied}/{total}. Veritabanı: {DB_NAME}")
