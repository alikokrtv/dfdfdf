#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Flask İçi E-posta Zamanlayıcısı
Flask uygulaması başladığında otomatik olarak başlar ve her gün 17:00'da çalışır
"""

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime, timedelta
import logging
import atexit

# Logger ayarları
logger = logging.getLogger(__name__)

def send_email_direct(to_email, subject, html_content, text_content):
    """Doğrudan SMTP ile e-posta gönder ve tracking'e kaydet"""
    # Lazy import to avoid circular import
    from models import EmailTrack
    from extensions import db
    
    # E-posta tracking kaydı oluştur
    track_id = EmailTrack.create_track(subject, to_email)
    
    try:
        import smtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        from flask import current_app
        
        # SMTP ayarları - Veritabanından güncel ayarları al
        from models import EmailSettings
        settings = EmailSettings.query.first()
        
        if settings:
            # Veritabanındaki güncel ayarları kullan
            smtp_server = settings.smtp_host
            smtp_port = settings.smtp_port
            smtp_user = settings.smtp_user
            smtp_password = settings.smtp_pass
            use_ssl = settings.smtp_use_ssl
            use_tls = settings.smtp_use_tls
        else:
            # Fallback - config'den al
            smtp_server = current_app.config.get('MAIL_SERVER', 'mail.kurumsaleposta.com')
            smtp_port = current_app.config.get('MAIL_PORT', 465)
            smtp_user = current_app.config.get('MAIL_USERNAME', 'web@beraber.com.tr')
            smtp_password = current_app.config.get('MAIL_PASSWORD', 'apV6Q69@-Ll@fS5=')
            use_ssl = current_app.config.get('MAIL_USE_SSL', True)
            use_tls = current_app.config.get('MAIL_USE_TLS', False)
        
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
        
        # SMTP ile gönder - Debug modunda
        logger.info(f"🔌 SMTP bağlantı kuruluyor: {smtp_server}:{smtp_port} (SSL:{use_ssl}, TLS:{use_tls})")
        logger.info(f"👤 Kullanıcı: {smtp_user}")
        
        if use_ssl:
            server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        else:
            server = smtplib.SMTP(smtp_server, smtp_port)
            if use_tls:
                server.starttls()
        
        logger.info(f"🔑 Giriş yapılıyor...")
        server.login(smtp_user, smtp_password)
        logger.info(f"📤 E-posta gönderiliyor: {smtp_user} -> {to_email}")
        
        # Debug için detaylı gönderim
        result = server.send_message(msg)
        logger.info(f"📬 SMTP gönderim sonucu: {result}")
        
        server.quit()
        logger.info(f"✅ SMTP bağlantı kapatıldı")
        
        # Başarılı gönderim - tracking güncelle
        EmailTrack.update_status(track_id, 'sent')
        logger.info(f"✅ E-posta gönderildi: {to_email}")
        return True
        
    except Exception as e:
        # Hatalı gönderim - tracking güncelle
        EmailTrack.update_status(track_id, 'failed', str(e))
        logger.error(f"❌ E-posta gönderim hatası ({to_email}): {str(e)}")
        return False

def get_user_managed_departments(user):
    """Kullanıcının yönettiği departmanları getir"""
    try:
        # Lazy import to avoid circular import
        from models import Department, UserRole, UserDepartmentMapping, DirectorManagerMapping
        
        departments = []
        
        # Kalite Yöneticisi: TÜM departmanlar (genel rapor)
        if user.role == UserRole.QUALITY_MANAGER:
            all_departments = Department.query.filter_by(is_active=True).all()
            departments.extend(all_departments)
            logger.info(f"✅ Kalite Yöneticisi {user.full_name} - {len(all_departments)} departman eklendi")
        
        # Departman Yöneticisi
        elif user.role == UserRole.DEPARTMENT_MANAGER and user.department_id:
            dept = Department.query.get(user.department_id)
            if dept and dept.is_active:
                departments.append(dept)
        
        # Çoklu Departman Yöneticileri (Group Manager, Projects Quality Tracking, Branches Quality Tracking)
        elif user.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
            user_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=user.id).all()
            for mapping in user_dept_mappings:
                if mapping.department and mapping.department.is_active:
                    departments.append(mapping.department)
        
        # Direktör
        elif user.role == UserRole.DIRECTOR:
            director_mappings = DirectorManagerMapping.query.filter_by(director_id=user.id).all()
            for mapping in director_mappings:
                manager = mapping.manager
                if manager and manager.role in [UserRole.GROUP_MANAGER, UserRole.PROJECTS_QUALITY_TRACKING, UserRole.BRANCHES_QUALITY_TRACKING]:
                    manager_dept_mappings = UserDepartmentMapping.query.filter_by(user_id=manager.id).all()
                    for dept_mapping in manager_dept_mappings:
                        if dept_mapping.department and dept_mapping.department.is_active:
                            departments.append(dept_mapping.department)
            
            logger.info(f"✅ Direktör {user.full_name} - {len(departments)} departman eklendi")
        
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
        # Lazy import to avoid circular import
        from models import DOF, DOFStatus, DOFAction
        from extensions import db
        
        if not department_ids:
            return {}
        
        today = datetime.now()
        week_ago = today - timedelta(days=7)
        
        # İlişkili DÖF'leri filtrele (başlığında "[İlişkili #" olan)
        related_dof_filter = ~DOF.title.like("[İlişkili #%")
        
        # Açık DÖF'ler
        open_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED,
            related_dof_filter
        ).all()
        
        # Kapalı DÖF'ler (son 7 gün) - updated_at ile kontrol et
        closed_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status == DOFStatus.CLOSED,
            DOF.updated_at >= week_ago,
            related_dof_filter
        ).all()
        
        # Durum dağılımı
        status_distribution = {}
        for dof in open_dofs:
            status_name = DOFStatus.get_label(dof.status)
            status_distribution[status_name] = status_distribution.get(status_name, 0) + 1
        
        # Yaklaşan termin tarihleri (gelecek 7 gün) - due_date kullan
        next_week = today + timedelta(days=7)
        upcoming_deadlines = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED,
            DOF.due_date.isnot(None),
            DOF.due_date <= next_week,
            DOF.due_date >= today,
            related_dof_filter
        ).all()
        
        # Geçmiş termin tarihleri - due_date kullan
        overdue_dofs = DOF.query.filter(
            DOF.department_id.in_(department_ids),
            DOF.status != DOFStatus.CLOSED,
            DOF.due_date.isnot(None),
            DOF.due_date < today,
            related_dof_filter
        ).all()
        
        # Son aksiyonlar (son 7 gün)
        recent_actions = db.session.query(DOFAction).join(DOF).filter(
            DOF.department_id.in_(department_ids),
            DOFAction.created_at >= week_ago,
            related_dof_filter
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
        # Lazy import to avoid circular import
        from app import app
        from flask import url_for
        
        # Diğer e-posta şablonlarıyla uyumlu olarak BASE_URL kullan
        server_url = app.config.get('BASE_URL', 'http://localhost:5000')
        # URL'in / ile bitmesini sağla
        if not server_url.endswith('/'):
            server_url += '/'
        # Son / karakterini kaldır çünkü path'lerde / ile başlayacağız
        server_url = server_url.rstrip('/')
        
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
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white !important; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
                .header h1 {{ margin: 0; font-size: 24px; color: white !important; }}
                .header p {{ margin: 5px 0 0 0; color: white !important; opacity: 0.9; }}
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
                .badge {{ display: inline-block; padding: 4px 8px; font-size: 11px; font-weight: 600; border-radius: 4px; color: white; }}
                .bg-secondary {{ background-color: #6c757d; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header" style="background-color: #f8f9fa; color: black; padding: 20px; border-radius: 8px; margin-bottom: 20px; border: 2px solid #007bff;">
                    <h1 style="margin: 0; font-size: 24px; color: black;">📊 Günlük DÖF Raporu</h1>
                    <p style="margin: 5px 0 0 0; color: black;">Sayın {user.full_name} - {user.role_name}</p>
                    <p style="margin: 5px 0 0 0; color: black;">📅 Tarih: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
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
                
                <div class="section">
                    <h2>🏢 Departman Bazında Detay</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Departman</th>
                                <th>Açık</th>
                                <th>Kapatılan</th>
                                <th>Yaklaşan</th>
                                <th>Gecikmiş</th>
                            </tr>
                        </thead>
                        <tbody>
        """
        
        # Her departman için ayrı istatistik
        for dept in departments:
            dept_statistics = get_dof_statistics([dept.id])
            html_content += f"""
                            <tr>
                                <td><strong>{dept.name}</strong></td>
                                <td>{dept_statistics.get('total_open', 0)}</td>
                                <td class="success">{dept_statistics.get('total_closed_week', 0)}</td>
                                <td class="warning">{dept_statistics.get('total_upcoming', 0)}</td>
                                <td class="danger">{dept_statistics.get('total_overdue', 0)}</td>
                            </tr>
            """
        
        html_content += """
                        </tbody>
                    </table>
                </div>
        """
        
        # Durum dağılımı bölümü
        if statistics.get('status_distribution'):
            html_content += """
                <div class="section">
                    <h2>📊 DÖF Durum Dağılımı (Açık DÖF'ler)</h2>
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Durum</th>
                                <th>Sayı</th>
                                <th>Açıklama</th>
                            </tr>
                        </thead>
                        <tbody>
            """
            
            # Durum açıklamaları
            status_descriptions = {
                'Taslak': 'Henüz gönderilmemiş DÖF\'ler',
                'Gönderildi': 'Kalite incelemesi bekleyen',
                'İncelemede': 'Kalite tarafından değerlendiriliyor',
                'Atandı': 'Departmana atandı, kök neden analizi bekleniyor',
                'Aksiyon Planı İncelemede': 'Kalite onayı bekleyen planlar',
                'Uygulama Aşamasında': 'Onaylanan planlar uygulanıyor',
                'Aksiyonlar Tamamlandı': 'Kalite kontrolü bekleyen',
                'Kaynak İncelemesinde': 'Kaynak departman onayı bekleyen',
                'Devam Ediyor': 'Süreç devam ediyor',
                'Reddedildi': 'Reddedilen DÖF\'ler'
            }
            
            for status_name, count in statistics['status_distribution'].items():
                description = status_descriptions.get(status_name, 'Durum açıklaması mevcut değil')
                
                # Durum rengi belirleme
                if status_name in ['Aksiyonlar Tamamlandı', 'Kaynak İncelemesinde']:
                    status_class = 'success'
                elif status_name in ['Aksiyon Planı İncelemede', 'Uygulama Aşamasında']:
                    status_class = 'warning'
                elif status_name in ['Atandı', 'İncelemede']:
                    status_class = 'info'
                else:
                    status_class = ''
                    
                html_content += f"""
                            <tr>
                                <td><strong>{status_name}</strong></td>
                                <td><span class="stat-number {status_class}" style="font-size: 18px;">{count}</span></td>
                                <td style="font-size: 13px; color: #6c757d;">{description}</td>
                            </tr>
                """
            
            html_content += """
                        </tbody>
                    </table>
                </div>
            """
        
        # Gecikmiş DÖF'ler
        if statistics.get('overdue_dofs'):
            html_content += """
                <div class="section urgent">
                    <h2>🚨 Gecikmiş DÖF'ler (Acil!)</h2>
                    <table class="table">
                        <thead><tr><th>DÖF #</th><th>Departman</th><th>Başlık</th><th>Durum</th><th>Gecikme</th></tr></thead>
                        <tbody>
            """
            for dof in statistics['overdue_dofs'][:5]:  # İlk 5 tanesi
                overdue_days = (datetime.now().date() - dof.deadline.date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                html_content += f"""
                            <tr>
                                <td><a href="{url_for('dof.detail', dof_id=dof.id, _external=True)}">#{dof.id}</a></td>
                                <td><span class="badge bg-secondary">{dept_name}</span></td>
                                <td>{dof.title[:40]}...</td>
                                <td>{DOFStatus.get_label(dof.status)}</td>
                                <td class="danger">{overdue_days} gün</td>
                            </tr>
                """
            html_content += "</tbody></table></div>"
        
        # Yaklaşan termin tarihleri
        if statistics.get('upcoming_deadlines'):
            html_content += """
                <div class="section warning-section">
                    <h2>⏰ Yaklaşan Termin Tarihleri</h2>
                    <table class="table">
                        <thead><tr><th>DÖF #</th><th>Departman</th><th>Başlık</th><th>Durum</th><th>Kalan</th></tr></thead>
                        <tbody>
            """
            for dof in statistics['upcoming_deadlines'][:5]:
                remaining_days = (dof.deadline.date() - datetime.now().date()).days if dof.deadline else 0
                dept_name = dof.department.name if dof.department else "Bilinmiyor"
                html_content += f"""
                            <tr>
                                <td><a href="{url_for('dof.detail', dof_id=dof.id, _external=True)}">#{dof.id}</a></td>
                                <td><span class="badge bg-secondary">{dept_name}</span></td>
                                <td>{dof.title[:40]}...</td>
                                <td>{DOFStatus.get_label(dof.status)}</td>
                                <td class="warning">{remaining_days} gün</td>
                            </tr>
                """
            html_content += "</tbody></table></div>"
        
        # Hızlı linkler
        html_content += f"""
                <div class="section">
                    <h2>🔗 Hızlı Linkler</h2>
                    <p>
                        <a href="{url_for('dof.list_dofs', _external=True)}" class="button">Tüm DÖF'leri Görüntüle</a>
                        <a href="{url_for('dof.create_dof', _external=True)}" class="button">Yeni DÖF Oluştur</a>
                        <a href="{url_for('dof.dashboard', _external=True)}" class="button">Dashboard</a>
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

def scheduled_daily_report_job():
    """Zamanlayıcı tarafından çağrılan ana fonksiyon"""
    try:
        logger.info("🚀 Scheduled günlük DÖF raporları başlıyor...")
        
        # Lazy import to avoid circular import
        from app import app
        from models import User, UserRole
        
        with app.app_context():
            # Server URL'ini tanımla
            server_url = app.config.get('BASE_URL', 'http://localhost:5000')
            if not server_url.endswith('/'):
                server_url += '/'
            server_url = server_url.rstrip('/')
            # E-posta alacak kullanıcıları getir
            report_recipients = User.query.filter(
                User.role.in_([
                    UserRole.DEPARTMENT_MANAGER,
                    UserRole.GROUP_MANAGER,
                    UserRole.DIRECTOR,
                    UserRole.QUALITY_MANAGER
                ]),
                User.active == True,
                User.email.isnot(None),
                User.email != ''
            ).all()
            
            logger.info(f"📧 Potansiyel alıcı sayısı: {len(report_recipients)}")
            
            if not report_recipients:
                logger.warning("📭 Rapor gönderilecek kullanıcı bulunamadı.")
                return
            
            total_emails_sent = 0
            total_errors = 0
            filtered_recipients = 0
            
            for user in report_recipients:
                try:
                    logger.info(f"📧 Rapor hazırlanıyor: {user.full_name}")
                    
                    # Kullanıcının yönettiği departmanları getir
                    departments = get_user_managed_departments(user)
                    
                    if not departments:
                        logger.warning(f"⚠️ {user.full_name} için departman bulunamadı")
                        continue
                    
                    department_ids = [dept.id for dept in departments]
                    
                    # İstatistikleri getir
                    statistics = get_dof_statistics(department_ids)
                    
                    if not statistics:
                        logger.warning(f"⚠️ {user.full_name} için istatistik alınamadı")
                        continue
                    
                    # ÖNEMLI: Sadece hiçbir aktif DÖF yoksa e-posta gönderme
                    # Kapalı DÖF'ler de önemli (haftalık özet için)
                    total_open = statistics.get('total_open', 0)
                    total_closed_week = statistics.get('total_closed_week', 0)
                    total_upcoming = statistics.get('total_upcoming', 0)
                    total_overdue = statistics.get('total_overdue', 0)
                    
                    # Eğer hiçbir aktivite yoksa e-posta gönderme
                    if total_open == 0 and total_closed_week == 0 and total_upcoming == 0 and total_overdue == 0:
                        logger.info(f"⏭️ {user.full_name} - Hiçbir DÖF aktivitesi yok, e-posta gönderilmiyor")
                        filtered_recipients += 1
                        continue
                    
                    # E-posta içeriğini oluştur
                    subject = f"Günlük DÖF Raporu - {datetime.now().strftime('%d.%m.%Y')}"
                    html_content = generate_report_html(user, departments, statistics)
                    
                    # Kısa text versiyonu
                    text_content = f"""
DÖF Günlük Raporu - {datetime.now().strftime('%d.%m.%Y')}

Sayın {user.full_name},

Sorumlu departmanlarınızdaki DÖF durumu:
• Açık DÖF: {total_open}
• Bu hafta kapatılan: {total_closed_week}
• Yaklaşan termin: {total_upcoming}
• Gecikmiş DÖF: {total_overdue}

Detaylar için: {url_for('dof.dashboard', _external=True)}

Bu e-posta otomatik olarak gönderilmiştir.
                    """
                    
                    if not html_content:
                        logger.error(f"❌ {user.full_name} için rapor oluşturulamadı")
                        total_errors += 1
                        continue
                    
                    # E-posta gönder - Normal sistemle (utils.py send_email kullan)
                    from utils import send_email
                    try:
                        result = send_email(subject, [user.email], html_content, text_content)
                        if result:
                            total_emails_sent += 1
                            logger.info(f"✅ {user.full_name} - Başarıyla gönderildi")
                        else:
                            total_errors += 1
                            logger.error(f"❌ {user.full_name} - Gönderim başarısız")
                    except Exception as email_error:
                        total_errors += 1
                        logger.error(f"❌ {user.full_name} - E-posta hatası: {str(email_error)}")
                        
                except Exception as e:
                    total_errors += 1
                    logger.error(f"❌ {user.full_name} için hata: {str(e)}")
            
            logger.info("=" * 50)
            logger.info(f"🎉 Günlük rapor tamamlandı!")
            logger.info(f"✅ Başarılı gönderim: {total_emails_sent} e-posta")
            logger.info(f"❌ Başarısız gönderim: {total_errors} e-posta")
            logger.info(f"⏭️ Filtrelenen (DÖF yok): {filtered_recipients} kullanıcı")
            logger.info(f"📊 Toplam işlenen: {total_emails_sent + total_errors + filtered_recipients} kullanıcı")
            
    except Exception as e:
        logger.error(f"❌ Scheduled job hatası: {str(e)}")

# Global scheduler
scheduler = None

def init_scheduler():
    """Zamanlayıcıyı başlat"""
    global scheduler
    
    if scheduler is not None:
        return scheduler
    
    try:
        # APScheduler konfigürasyonu
        scheduler = BackgroundScheduler(
            timezone='Europe/Istanbul',  # Türkiye saati
            daemon=True
        )
        
        # Her gün saat 17:00'da çalıştır
        scheduler.add_job(
            func=scheduled_daily_report_job,
            trigger=CronTrigger(hour=17, minute=0),  # 17:00
            id='daily_dof_reports',
            name='Günlük DÖF Raporları',
            replace_existing=True,
            max_instances=1
        )
        
        # Test için - her 5 dakikada çalıştırmak (geliştirme için)
        scheduler.add_job(
            func=scheduled_daily_report_job,
            trigger=CronTrigger(minute='*/5'),  # Her 5 dakika
            id='daily_dof_reports_test',
            name='Test DÖF Raporları (5dk)',
            replace_existing=True,
            max_instances=1
        )
        
        scheduler.start()
        logger.info("✅ E-posta zamanlayıcısı başlatıldı - Her gün 17:00'da ve test için her 5 dakikada çalışacak")
        
        # Uygulama kapandığında scheduler'ı kapat
        atexit.register(lambda: scheduler.shutdown())
        
        return scheduler
        
    except Exception as e:
        logger.error(f"❌ Scheduler başlatma hatası: {str(e)}")
        return None

def stop_scheduler():
    """Zamanlayıcıyı durdur"""
    global scheduler
    if scheduler is not None:
        scheduler.shutdown()
        scheduler = None
        logger.info("🛑 E-posta zamanlayıcısı durduruldu")

def get_scheduler_status():
    """Zamanlayıcı durumunu getir"""
    global scheduler
    if scheduler is None:
        return {
            'status': 'stopped',
            'jobs': [],
            'running': False
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        next_run = job.next_run_time.strftime('%d.%m.%Y %H:%M:%S') if job.next_run_time else 'Bilinmiyor'
        jobs.append({
            'id': job.id,
            'name': job.name,
            'next_run': next_run,
            'trigger': str(job.trigger)
        })
    
    return {
        'status': 'running' if scheduler.running else 'stopped',
        'jobs': jobs,
        'running': scheduler.running
    }

# Test fonksiyonu
def test_daily_report():
    """Manuel test için"""
    logger.info("🧪 Test modunda günlük rapor çalıştırılıyor...")
    scheduled_daily_report_job() 