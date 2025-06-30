from flask import Blueprint, request, flash, redirect, url_for, current_app
from flask_login import current_user, login_required
from models import User
from flask_mail import Message
from app import mail
import datetime

feedback_bp = Blueprint('feedback', __name__, url_prefix='/feedback')

@feedback_bp.route('/submit', methods=['POST'])
@login_required
def submit_feedback():
    # Log form verilerini
    current_app.logger.info(f"Geri bildirim formu alındı: {request.form}")
    
    # Form verilerini al
    feedback_type = request.form.get('feedback_type', 'other')
    subject = request.form.get('subject', '')
    message = request.form.get('message', '')
    
    # Temel doğrulama
    if not subject or not message:
        flash('Konu ve mesaj alanları boş olamaz', 'danger')
        return redirect(request.referrer or url_for('dof.dashboard'))
    
    # Admin e-posta adreslerini bul
    all_users = User.query.all()
    admin_users = [user for user in all_users if user.is_admin()]
    admin_emails = [user.email for user in admin_users if user.email]
    
    if not admin_emails:
        flash('Sistem yöneticisine ulaşılamadı. Lütfen daha sonra tekrar deneyiniz.', 'warning')
        return redirect(request.referrer or url_for('dof.dashboard'))
    
    try:
        # E-posta içeriği oluştur
        email_subject = f"[Geri Bildirim] {subject}"
        email_text = f"""Geri Bildirim

Bildirim Türü: {feedback_type}
Konu: {subject}
Mesaj: {message}

Gönderen: {current_user.first_name} {current_user.last_name} ({current_user.email})
Tarih: {datetime.datetime.now().strftime('%d.%m.%Y %H:%M')}"""
        
        # E-posta ayarlarını logla
        current_app.logger.info(f"E-posta gönderimi başlıyor: Gönderen: {current_app.config.get('MAIL_DEFAULT_SENDER')}, Alıcılar: {admin_emails}")
        current_app.logger.info(f"SMTP Ayarları: {current_app.config.get('MAIL_SERVER')}:{current_app.config.get('MAIL_PORT')} (SSL: {current_app.config.get('MAIL_USE_SSL')}, TLS: {current_app.config.get('MAIL_USE_TLS')})")
        
        # E-posta göndermeyi dene
        # Admin sayfasında yapılandırılan e-posta ayarlarını kullan
        # Varsayılan gönderici ayarından al
        sender_email = current_app.config.get('MAIL_DEFAULT_SENDER')
        
        # Gönderici alanını biçimlendir
        if isinstance(sender_email, tuple):
            # Zaten (isim, email) formatındaysa kullan
            sender = sender_email
        else:
            # Sadece email ise "DÖF Bildirim Sistemi" adını ekle
            sender = ("DÖF Bildirim Sistemi", sender_email)
            
        msg = Message(
            subject=email_subject,
            recipients=admin_emails,
            body=email_text,
            sender=sender
        )
        
        # E-posta takip sistemi ile gönder
        from utils import send_email
        result = send_email(email_subject, admin_emails, email_text, email_text)
        
        if result:
            current_app.logger.info(f"E-posta başarıyla gönderildi: {email_subject} -> {admin_emails}")
            flash('Geri bildiriminiz başarıyla gönderildi. Teşekkürler!', 'success')
        else:
            current_app.logger.error(f"E-posta gönderilemedi: {email_subject} -> {admin_emails}")
            flash('Geri bildiriminiz kaydedildi ancak e-posta gönderilirken bir hata oluştu.', 'warning')
    
    except Exception as e:
        import traceback
        current_app.logger.error(f"E-posta gönderilirken hata: {str(e)}")
        current_app.logger.error(traceback.format_exc())
        flash('Geri bildiriminiz kaydedildi ancak e-posta gönderilirken bir hata oluştu.', 'warning')
    
    return redirect(request.referrer or url_for('dof.dashboard'))
