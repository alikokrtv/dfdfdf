#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Günlük DÖF Raporu E-posta Sistemi
Her akşam 17:00'da departman yöneticilerine, bölge müdürlerine ve direktörlere 
kendi sorumluluklarındaki DÖF'lerle ilgili detaylı bilgilendirme maili gönderir.

Rapor İçeriği:
- Açık DÖF'ler (durumlarına göre)
- Kapalı DÖF'ler (son 7 gün)
- Devam eden DÖF'ler
- Son yapılan aksiyonlar
- Termin süreleri ve yaklaşan süreler
- Durum dağılımı
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# Logging ayarları
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/var/log/dof_daily_reports.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Mevcut dizini Python path'ine ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Flask app'ını import et
from app import app, db
from models import (
    DOF, User, Department, UserRole, DOFStatus, DOFAction, 
    UserDepartmentMapping, DirectorManagerMapping
)

def send_email_direct(to_email, subject, html_content, text_content):
    """Doğrudan SMTP ile e-posta gönder"""
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # SMTP ayarları - Flask app config'den al
        smtp_server = app.config.get('MAIL_SERVER', 'mail.kurumsaleposta.com')
        smtp_port = app.config.get('MAIL_PORT', 465)
        smtp_user = app.config.get('MAIL_USERNAME', 'df@beraber.com.tr')
        smtp_password = app.config.get('MAIL_PASSWORD', '=z5-5MNKn=ip5P4@')
        use_ssl = app.config.get('MAIL_USE_SSL', True)
        use_tls = app.config.get('MAIL_USE_TLS', False)
        
        # E-posta oluştur
        msg = MIMEMultipart('alternative')
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        
        # HTML ve text parçalarını ekle
        text_part = MIMEText(text_content, 'plain', 'utf-8')
        html_part = MIMEText(html_content, 'html', 'utf-8')
        
        msg.attach(text_part)
        msg.attach(html_part)
        
        # SMTP ile gönder - SSL/TLS ayarlarına göre
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ E-posta gönderildi: {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"❌ E-posta gönderim hatası ({to_email}): {str(e)}")
        return False

def get_user_managed_departments(user):
    """Kullanıcının yönettiği departmanları getir"""
    try:
        departments = []
        
        # Departman Yöneticisi
        if user.role == UserRole.DEPARTMENT_MANAGER and user.department_id:
            dept = Department.query.get(user.department_id)
            if dept and dept.is_active:
                departments.append(dept)
        
        # Bölge Müdürü (Group Manager)
        elif user.role == UserRole.GROUP_MANAGER:
            # UserDepartmentMapping tablosundan yönetilen departmanları al
            user_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=user.id).all()
            for mapping in user_dept_mappings:
                if mapping.department and mapping.department.is_active:
                    departments.append(mapping.department)
        
        # Direktör
        elif user.role == UserRole.DIRECTOR:
            # Önce yönettiği bölge müdürlerini bul
            director_mappings = DirectorManagerMapping.query.filter_by(director_id=user.id).all()
            
            for mapping in director_mappings:
                manager = mapping.manager
                if manager and manager.role == UserRole.GROUP_MANAGER:
                    # Bu bölge müdürünün yönettiği departmanları al
                    manager_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=manager.id).all()
                    for dept_mapping in manager_dept_mappings:
                        if dept_mapping.department and dept_mapping.department.is_active:
                            departments.append(dept_mapping.department)
        
        # Tekrar eden departmanları kaldır
        unique_departments = []
        seen_ids = set()
        for dept in departments:
            if dept.id not in seen_ids:
                unique_departments.append(dept)
                seen_ids.add(dept.id)
        
        return unique_departments
        
    except Exception as e:
        logger.error(f"❌ Departman getirme hatası ({user.username}): {str(e)}")
        return []

def get_dof_statistics(department_ids):
    """Belirtilen departmanlar için DÖF istatistiklerini getir"""
    try:
        if not department_ids:
            return {}
        
        # Bugün
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        # Açık DÖF'ler (tüm durumlar - kapalı hariç)
        open_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED
        ).all()
        
        # Kapalı DÖF'ler (son 7 gün)
        closed_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status == DOFStatus.CLOSED,
            DOF.closed_at >= week_ago
        ).all()
        
        # Durum dağılımı
        status_distribution = {}
        for dof in open_dofs:
            status_name = DOFStatus.get_label(dof.status)
            status_distribution[status_name] = status_distribution.get(status_name, 0) + 1
        
        # Yaklaşan termin tarihleri (gelecek 7 gün)
        next_week = today + timedelta(days=7)
        upcoming_deadlines = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED,
            DOF.deadline.isnot(None),
            DOF.deadline <= next_week,
            DOF.deadline >= today
        ).all()
        
        # Geçmiş termin tarihleri
        overdue_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED,
            DOF.deadline.isnot(None),
            DOF.deadline < today
        ).all()
        
        # Son aksiyonlar (son 7 gün)
        recent_actions = db.session.query(DOFAction).join(DOF).filter(
            DOF.department_id.in_(department_ids),
            DOFAction.created_at >= week_ago
        ).order_by(DOFAction.created_at.desc()).limit(10).all()
        
        return {
            'open_dofs': open_dofs,
            'closed_dofs': closed_dofs,
            'status_distribution': status_distribution,
            'upcoming_deadlines': upcoming_deadlines,
            'overdue_dofs': overdue_dofs,
            'recent_actions': recent_actions,
            'total_open': len(open_dofs),
            'total_closed_week': len(closed_dofs),
            'total_upcoming': len(upcoming_deadlines),
            'total_overdue': len(overdue_dofs)
        }
        
    except Exception as e:
        logger.error(f"❌ İstatistik getirme hatası: {str(e)}")
        return {}

def generate_report_html(user, departments, statistics):
    """HTML rapor oluştur"""
    try:
        # Sunucu URL'si - Uzak sunucu için güncellenmiş
        server_url = os.environ.get('SERVER_URL', 'http://your-server-ip:5000')  # Uzak sunucu URL'si
        
        # Departman listesi
        dept_names = [dept.name for dept in departments]
        dept_list = ", ".join(dept_names) if dept_names else "Hiç departman bulunamadı"
        
        html_content = f"""
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; }}
                .container {{ max-width: 800px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; }}
                .header p {{ margin: 5px 0 0 0; opacity: 0.9; }}
                .section {{ background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px; border-left: 4px solid #007bff; }}
                .section h2 {{ margin: 0 0 10px 0; color: #495057; font-size: 18px; }}
                .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 15px 0; }}
                .stat-box {{ background: white; padding: 15px; border-radius: 6px; border: 1px solid #dee2e6; text-align: center; }}
                .stat-number {{ font-size: 28px; font-weight: bold; color: #007bff; margin-bottom: 5px; }}
                .stat-label {{ color: #6c757d; font-size: 14px; }}
                .danger {{ color: #dc3545 !important; }}
                .warning {{ color: #ffc107 !important; }}
                .success {{ color: #28a745 !important; }}
                .table {{ width: 100%; border-collapse: collapse; margin: 10px 0; }}
                .table th, .table td {{ padding: 8px 12px; text-align: left; border-bottom: 1px solid #dee2e6; }}
                .table th {{ background-color: #e9ecef; font-weight: 600; }}
                .button {{ background-color: #007bff; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin: 5px; }}
                .footer {{ background-color: #f8f9fa; padding: 15px; border-top: 1px solid #dee2e6; margin-top: 20px; font-size: 12px; color: #6c757d; text-align: center; }}
                .urgent {{ background-color: #fff5f5; border-left-color: #dc3545; }}
                .warning-section {{ background-color: #fffbf0; border-left-color: #ffc107; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📊 Günlük DÖF Raporu</h1>
                    <p>Sayın {user.full_name} - {user.role_name}</p>
                    <p>📅 Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
                
                <div class="section">
                    <h2>🏢 Sorumlu Departmanlarınız</h2>
                    <p><strong>{dept_list}</strong></p>
                </div>
                
                <div class="section">
                    <h2>📈 Genel İstatistikler</h2>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-number">{statistics.get('total_open', 0)}</div>
                            <div class="stat-label">Açık DÖF</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number success">{statistics.get('total_closed_week', 0)}</div>
                            <div class="stat-label">Bu Hafta Kapatılan</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number warning">{statistics.get('total_upcoming', 0)}</div>
                            <div class="stat-label">Yaklaşan Termin</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-number danger">{statistics.get('total_overdue', 0)}</div>
                            <div class="stat-label">Gecikmiş DÖF</div>
                        </div>
                    </div>
                </div>
        """
        
        # Gecikmiş DÖF'ler - Acil durum
        if statistics.get('overdue_dofs'):
            html_content += f"""
                <div class="section urgent">
                    <h2>🚨 Gecikmiş DÖF'ler (Acil İlgilenilmesi Gerekiyor!)</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>DÖF #</th>
                                <th>Başlık</th>
                                <th>Durum</th>
                                <th>Termin</th>
                                <th>Gecikme (Gün)</th>
                                <th>Departman</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for dof in statistics['overdue_dofs']:
                overdue_days = (datetime.now().date() - dof.deadline.date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                html_content += f"""
                            <tr>
                                <td><a href="{server_url}/dof/{dof.id}">#{dof.id}</a></td>
                                <td>{dof.title[:50]}...</td>
                                <td>{DOFStatus.get_label(dof.status)}</td>
                                <td>{dof.deadline.strftime('%d.%m.%Y') if dof.deadline else '-'}</td>
                                <td class="danger">{overdue_days}</td>
                                <td>{dept_name}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Yaklaşan termin tarihleri
        if statistics.get('upcoming_deadlines'):
            html_content += f"""
                <div class="section warning-section">
                    <h2>⏰ Yaklaşan Termin Tarihleri (7 Gün İçinde)</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>DÖF #</th>
                                <th>Başlık</th>
                                <th>Durum</th>
                                <th>Termin</th>
                                <th>Kalan Gün</th>
                                <th>Departman</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for dof in statistics['upcoming_deadlines']:
                remaining_days = (dof.deadline.date() - datetime.now().date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                html_content += f"""
                            <tr>
                                <td><a href="{server_url}/dof/{dof.id}">#{dof.id}</a></td>
                                <td>{dof.title[:50]}...</td>
                                <td>{DOFStatus.get_label(dof.status)}</td>
                                <td>{dof.deadline.strftime('%d.%m.%Y') if dof.deadline else '-'}</td>
                                <td class="warning">{remaining_days}</td>
                                <td>{dept_name}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Durum dağılımı
        if statistics.get('status_distribution'):
            html_content += f"""
                <div class="section">
                    <h2>📊 DÖF Durum Dağılımı</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Durum</th>
                                <th>Adet</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for status, count in statistics['status_distribution'].items():
                html_content += f"""
                            <tr>
                                <td>{status}</td>
                                <td><strong>{count}</strong></td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Son aksiyonlar
        if statistics.get('recent_actions'):
            html_content += f"""
                <div class="section">
                    <h2>🔄 Son Aksiyonlar (Son 7 Gün)</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Tarih</th>
                                <th>DÖF #</th>
                                <th>Kullanıcı</th>
                                <th>Aksiyon</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for action in statistics['recent_actions']:
                user_name = action.user.full_name if action.user else "Bilinmiyor"
                comment_preview = action.comment[:80] + "..." if action.comment and len(action.comment) > 80 else (action.comment or "Yorum yok")
                html_content += f"""
                            <tr>
                                <td>{action.created_at.strftime('%d.%m.%Y %H:%M')}</td>
                                <td><a href="{server_url}/dof/{action.dof_id}">#{action.dof_id}</a></td>
                                <td>{user_name}</td>
                                <td>{comment_preview}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Bu hafta kapatılan DÖF'ler
        if statistics.get('closed_dofs'):
            html_content += f"""
                <div class="section">
                    <h2>✅ Bu Hafta Kapatılan DÖF'ler</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>DÖF #</th>
                                <th>Başlık</th>
                                <th>Kapatılma Tarihi</th>
                                <th>Departman</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            for dof in statistics['closed_dofs']:
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                html_content += f"""
                            <tr>
                                <td><a href="{server_url}/dof/{dof.id}">#{dof.id}</a></td>
                                <td>{dof.title[:50]}...</td>
                                <td>{dof.closed_at.strftime('%d.%m.%Y %H:%M') if dof.closed_at else '-'}</td>
                                <td>{dept_name}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Hızlı linkler
        html_content += f"""
                <div class="section">
                    <h2>🔗 Hızlı Linkler</h2>
                    <p>
                        <a href="{server_url}/dof/list" class="button">Tüm DÖF'leri Görüntüle</a>
                        <a href="{server_url}/dof/create" class="button">Yeni DÖF Oluştur</a>
                        <a href="{server_url}/dashboard" class="button">Dashboard</a>
                    </p>
                </div>
                
                <div class="footer">
                    <p>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</p>
                    <p>DÖF Yönetim Sistemi - {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        logger.error(f"❌ HTML rapor oluşturma hatası: {str(e)}")
        return None

def generate_report_text(user, departments, statistics):
    """Text rapor oluştur"""
    try:
        # Departman listesi
        dept_names = [dept.name for dept in departments]
        dept_list = ", ".join(dept_names) if dept_names else "Hiç departman bulunamadı"
        
        text_content = f"""
DÖF Sistemi - Günlük Rapor
{'=' * 50}

Sayın {user.full_name} - {user.role_name}
Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}

SORUMLU DEPARTMANLARINIZ
{'-' * 30}
{dept_list}

GENEL İSTATİSTİKLER
{'-' * 30}
• Açık DÖF: {statistics.get('total_open', 0)}
• Bu Hafta Kapatılan: {statistics.get('total_closed_week', 0)}
• Yaklaşan Termin: {statistics.get('total_upcoming', 0)}
• Gecikmiş DÖF: {statistics.get('total_overdue', 0)}
        """
        
        # Gecikmiş DÖF'ler
        if statistics.get('overdue_dofs'):
            text_content += f"""

⚠️  GECİKMİŞ DÖF'LER (ACİL!)
{'-' * 30}
"""
            for dof in statistics['overdue_dofs']:
                overdue_days = (datetime.now().date() - dof.deadline.date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                text_content += f"• DÖF #{dof.id} - {dof.title[:50]}... ({overdue_days} gün gecikmiş)\n"
        
        # Yaklaşan termin tarihleri
        if statistics.get('upcoming_deadlines'):
            text_content += f"""

⏰ YAKLAŞAN TERMİN TARİHLERİ
{'-' * 30}
"""
            for dof in statistics['upcoming_deadlines']:
                remaining_days = (dof.deadline.date() - datetime.now().date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                text_content += f"• DÖF #{dof.id} - {dof.title[:50]}... ({remaining_days} gün kaldı)\n"
        
        # Durum dağılımı
        if statistics.get('status_distribution'):
            text_content += f"""

📊 DURUM DAĞILIMI
{'-' * 30}
"""
            for status, count in statistics['status_distribution'].items():
                text_content += f"• {status}: {count}\n"
        
        # Son aksiyonlar
        if statistics.get('recent_actions'):
            text_content += f"""

🔄 SON AKSİYONLAR (Son 7 Gün)
{'-' * 30}
"""
            for action in statistics['recent_actions'][:5]:  # İlk 5 tanesini göster
                user_name = action.user.full_name if action.user else "Bilinmiyor"
                comment_preview = action.comment[:50] + "..." if action.comment and len(action.comment) > 50 else (action.comment or "Yorum yok")
                text_content += f"• {action.created_at.strftime('%d.%m %H:%M')} - DÖF #{action.dof_id} - {user_name}: {comment_preview}\n"
        
        text_content += f"""

HIZLI LİNKLER
{'-' * 30}
• Tüm DÖF'leri Görüntüle: {os.environ.get('SERVER_URL', 'http://your-server-ip:5000')}/dof/list
• Yeni DÖF Oluştur: {os.environ.get('SERVER_URL', 'http://your-server-ip:5000')}/dof/create
• Dashboard: {os.environ.get('SERVER_URL', 'http://your-server-ip:5000')}/dashboard

Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.
DÖF Yönetim Sistemi - {datetime.now().strftime('%d.%m.%Y %H:%M')}
        """
        
        return text_content
        
    except Exception as e:
        logger.error(f"❌ Text rapor oluşturma hatası: {str(e)}")
        return None

def send_daily_reports():
    """Ana fonksiyon - günlük raporları gönder"""
    logger.info("🚀 Günlük DÖF raporları gönderimi başlıyor...")
    logger.info("=" * 70)
    
    # Flask app context'i oluştur
    with app.app_context():
        # Veritabanı bağlantısını test et
        try:
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            logger.info("✅ Veritabanı bağlantısı başarılı")
        except Exception as e:
            logger.error(f"❌ Veritabanı bağlantı hatası: {str(e)}")
            return
        
        # E-posta alacak kullanıcıları getir
        report_recipients = User.query.filter(
            User.role.in_([
                UserRole.DEPARTMENT_MANAGER,  # Departman Yöneticileri
                UserRole.GROUP_MANAGER,       # Bölge Müdürleri  
                UserRole.DIRECTOR             # Direktörler
            ]),
            User.active == True,
            User.email.isnot(None),
            User.email != ''
        ).all()
        
        logger.info(f"📧 Rapor gönderilecek kullanıcı sayısı: {len(report_recipients)}")
        
        if not report_recipients:
            logger.warning("📭 Rapor gönderilecek kullanıcı bulunamadı.")
            return
        
        # Otomatik çalışma modu kontrolü (çevre değişkeni)
        auto_mode = os.environ.get('AUTO_SEND_REPORTS', 'false').lower() == 'true'
        
        if not auto_mode:
            # Manuel mod - önce kimlere gönderileceğini göster
            print(f"\n📋 RAPOR GÖNDERİM ÖZETİ:")
            print("=" * 70)
            
            for user in report_recipients:
                departments = get_user_managed_departments(user)
                dept_count = len(departments)
                print(f"👤 {user.full_name} ({user.role_name}) - {dept_count} departman")
            
            # Onay iste
            print(f"\n❓ Bu {len(report_recipients)} kullanıcıya günlük rapor göndermek istiyor musunuz?")
            confirmation = input("   Devam etmek için 'EVET' yazın (diğer herhangi bir tuş = iptal): ").strip().upper()
            
            if confirmation != 'EVET':
                logger.info("❌ İşlem kullanıcı tarafından iptal edildi.")
                return
        else:
            # Otomatik mod - onay isteme
            logger.info(f"📋 Otomatik mod: {len(report_recipients)} kullanıcıya rapor gönderimi başlıyor...")
        
        logger.info("🚀 Rapor gönderimi başlıyor...")
        logger.info("=" * 70)
        
        total_emails_sent = 0
        total_errors = 0
        
        for user in report_recipients:
            try:
                logger.info(f"📧 Rapor hazırlanıyor: {user.full_name} ({user.role_name})")
                
                # Kullanıcının yönettiği departmanları getir
                departments = get_user_managed_departments(user)
                
                if not departments:
                    logger.warning(f"   ⚠️  Yönetilen departman bulunamadı, e-posta gönderilmiyor")
                    continue
                
                department_ids = [dept.id for dept in departments]
                dept_names = [dept.name for dept in departments]
                
                logger.info(f"   🏢 Departmanlar: {', '.join(dept_names)}")
                
                # İstatistikleri getir
                statistics = get_dof_statistics(department_ids)
                
                if not statistics:
                    logger.warning(f"   ⚠️  İstatistik verisi alınamadı, e-posta gönderilmiyor")
                    continue
                
                logger.info(f"   📊 Açık: {statistics.get('total_open', 0)}, Gecikmiş: {statistics.get('total_overdue', 0)}")
                
                # E-posta içeriğini oluştur
                subject = f"Günlük DÖF Raporu - {datetime.now().strftime('%d.%m.%Y')}"
                html_content = generate_report_html(user, departments, statistics)
                text_content = generate_report_text(user, departments, statistics)
                
                if not html_content or not text_content:
                    logger.error(f"   ❌ Rapor içeriği oluşturulamadı")
                    total_errors += 1
                    continue
                
                # E-posta gönder
                if send_email_direct(user.email, subject, html_content, text_content):
                    total_emails_sent += 1
                    logger.info(f"   ✅ Başarıyla gönderildi")
                else:
                    total_errors += 1
                    logger.error(f"   ❌ Gönderim başarısız")
                    
            except Exception as e:
                total_errors += 1
                logger.error(f"   ❌ Hata: {str(e)}")
        
        logger.info("=" * 70)
        logger.info(f"🎉 Tamamlandı!")
        logger.info(f"✅ Başarılı: {total_emails_sent} e-posta")
        logger.info(f"❌ Hatalı: {total_errors} e-posta")
        logger.info(f"📊 Toplam: {len(report_recipients)} kullanıcı")

if __name__ == "__main__":
    send_daily_reports() 