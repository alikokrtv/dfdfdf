#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pymysql
from datetime import datetime, timedelta

def check_email_tracking():
    print('E-posta takip tablosu durum kontrolü (MySQL Sunucu):')
    print('=' * 60)
    
    try:
        # MySQL bağlantısı
        connection = pymysql.connect(
            host='mysql-2a6208e7-aliko-1a4a.f.aivencloud.com',
            port=28334,
            user='avnadmin',
            password='AVNS_YLaVZGE2nC_j4iX8lQ2',
            database='defaultdb',
            charset='utf8mb4'
        )
        
        print('✓ MySQL sunucuya bağlantı başarılı')
        print()
        
        cursor = connection.cursor()
        
        # E-posta tablosunun var olup olmadığını kontrol et
        cursor.execute("SHOW TABLES LIKE 'email_tracks'")
        table_exists = cursor.fetchone()
        
        if not table_exists:
            print('❌ email_tracks tablosu bulunamadı!')
            print('   Bu tablonun oluşturulması gerekiyor.')
            return
        
        print('✓ email_tracks tablosu bulundu')
        print()
        
        # Toplam istatistikler
        cursor.execute("SELECT COUNT(*) FROM email_tracks")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE status = 'sent'")
        sent = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE status = 'failed'")
        failed = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE status = 'queued'")
        queued = cursor.fetchone()[0]
        
        print(f'📊 E-posta İstatistikleri:')
        print(f'   Toplam e-posta kaydı: {total}')
        print(f'   ✅ Gönderilen: {sent}')
        print(f'   ❌ Başarısız: {failed}')  
        print(f'   ⏳ Sırada bekleyen: {queued}')
        print()
        
        if total > 0:
            # Son 15 e-posta kaydını göster
            print('📧 Son 15 e-posta kaydı:')
            print('-' * 120)
            print(f'{"Tarih":<17} | {"Konu":<45} | {"Alıcı":<35} | {"Durum":<10} | {"Hata"}')
            print('-' * 120)
            
            cursor.execute("""
                SELECT created_at, subject, recipients, status, error 
                FROM email_tracks 
                ORDER BY created_at DESC 
                LIMIT 15
            """)
            
            for row in cursor.fetchall():
                created_at, subject, recipients, status, error = row
                
                # Tarih formatı
                date_str = created_at.strftime("%d.%m.%Y %H:%M") if created_at else "N/A"
                
                # Kısaltmalar
                subject_short = (subject[:42] + '...') if subject and len(subject) > 42 else (subject or '')
                recipients_short = (recipients[:32] + '...') if recipients and len(recipients) > 32 else (recipients or '')
                error_short = (error[:30] + '...') if error and len(error) > 30 else (error or '')
                
                # Durum ikonu
                status_icon = {'sent': '✅', 'failed': '❌', 'queued': '⏳'}.get(status, '❓')
                
                print(f'{date_str:<17} | {subject_short:<45} | {recipients_short:<35} | {status_icon} {status:<8} | {error_short}')
            
            print('-' * 120)
            
            # DÖF ile ilgili e-postaları say
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%DÖF%'")
            dof_emails = cursor.fetchone()[0]
            print(f'\n🔍 DÖF ile ilgili e-postalar: {dof_emails}')
            
            # Bugün gönderilen e-postalar
            today = datetime.now().date()
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE DATE(created_at) = %s", (today,))
            today_emails = cursor.fetchone()[0]
            print(f'📅 Bugün gönderilen e-postalar: {today_emails}')
            
            # Son 7 gün
            week_ago = datetime.now() - timedelta(days=7)
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE created_at >= %s", (week_ago,))
            week_emails = cursor.fetchone()[0]
            print(f'📊 Son 7 günde gönderilen e-postalar: {week_emails}')
            
            # E-posta türleri
            print(f'\n📈 E-posta türleri:')
            
            # DÖF oluşturma e-postaları
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%Yeni DÖF%'")
            dof_create_emails = cursor.fetchone()[0]
            print(f'   🆕 DÖF oluşturma bildirimleri: {dof_create_emails}')
            
            # DÖF durum değişikliği e-postaları  
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%Durum Değişikliği%'")
            dof_status_emails = cursor.fetchone()[0]
            print(f'   🔄 DÖF durum değişikliği bildirimleri: {dof_status_emails}')
            
            # Şifre sıfırlama e-postaları
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%Şifre%'")
            password_emails = cursor.fetchone()[0]
            print(f'   🔑 Şifre sıfırlama e-postaları: {password_emails}')
            
            # Kullanıcı kaydı e-postaları
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%Hoş Geldiniz%'")
            register_emails = cursor.fetchone()[0]
            print(f'   👋 Kullanıcı kaydı e-postaları: {register_emails}')
            
            # Test e-postaları
            cursor.execute("SELECT COUNT(*) FROM email_tracks WHERE subject LIKE '%Test%'")
            test_emails = cursor.fetchone()[0]
            print(f'   🧪 Test e-postaları: {test_emails}')
            
        else:
            print('ℹ️  Henüz e-posta takip kaydı bulunmuyor.')
            print('   Bu durum şu anlama gelebilir:')
            print('   - E-posta takip sistemi henüz kullanılmamış')
            print('   - E-postalar eski sistemle gönderilmiş')
            print('   - Veritabanı tablosu boş')
        
        cursor.close()
        connection.close()
        
    except pymysql.Error as e:
        print(f'❌ MySQL Hatası: {e}')
    except Exception as e:
        print(f'❌ Genel Hata: {e}')
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    check_email_tracking() 