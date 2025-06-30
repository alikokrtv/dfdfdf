"""
Mail Service - Merkezi Mail Gönderme Servisi
--------------------------------------------
Tüm e-posta gönderme işlemleri için kullanılacak merkezi servis modülü.
Bu modül, Flask-Mail kullanarak e-posta gönderme işlemlerini yönetir ve hataları merkezi olarak ele alır.

Kullanım:
    from mail_service import MailService
    
    # Tekil e-posta gönderimi
    MailService.send_email(subject="Konu", recipients=["user@example.com"], html_body="<p>Merhaba</p>")
    
    # Asenkron e-posta gönderimi
    MailService.send_email_async(subject="Konu", recipients=["user@example.com"], html_body="<p>Merhaba</p>")
"""

from flask import current_app
from flask_mail import Message
import smtplib
import time
import re
import traceback
import threading
from typing import List, Optional, Dict, Union, Any

class MailService:
    """Merkezi e-posta gönderme servisi"""

    @staticmethod
    def _validate_recipients(recipients: List[str]) -> List[str]:
        """Alıcı e-posta adreslerini doğrula ve temizle"""
        if not recipients or len(recipients) == 0:
            current_app.logger.warning("E-posta gönderimi iptal: Alıcı listesi boş")
            return []
        
        # Boş e-posta adresi veya geçersiz formatta olanları temizle
        valid_recipients = [r.strip() for r in recipients if r and '@' in r]
        if not valid_recipients:
            current_app.logger.warning("E-posta gönderimi iptal: Geçerli alıcı yok")
        
        return valid_recipients

    @staticmethod
    def _create_message(subject: str, recipients: List[str], 
                       html_body: Optional[str] = None,
                       text_body: Optional[str] = None) -> Message:
        """Flask-Mail Message nesnesi oluştur"""
        # E-posta nesnesi oluştur
        msg = Message(subject=subject, recipients=recipients)
        
        # Göndereni ayarla
        sender = current_app.config.get('MAIL_DEFAULT_SENDER')
        if not sender:
            sender = current_app.config.get('MAIL_USERNAME')
        msg.sender = sender
        
        # HTML içerik ekle
        if html_body:
            msg.html = html_body
        
        # Düz metin içerik ekle
        if text_body:
            msg.body = text_body
        elif html_body:
            # HTML'den düz metin oluştur (basit bir şekilde)
            msg.body = re.sub('<[^<]+?>', '', html_body)
        
        return msg

    @staticmethod
    def _log_mail_settings() -> None:
        """SMTP bağlantı ayarlarını logla"""
        try:
            mail_server = current_app.config.get('MAIL_SERVER', 'N/A')
            mail_port = current_app.config.get('MAIL_PORT', 'N/A')
            mail_use_tls = current_app.config.get('MAIL_USE_TLS', False)
            mail_use_ssl = current_app.config.get('MAIL_USE_SSL', False)
            mail_username = current_app.config.get('MAIL_USERNAME', 'N/A')
            
            # Kullanıcı adını maskele
            if mail_username and '@' in mail_username:
                parts = mail_username.split('@')
                if len(parts[0]) > 2:
                    masked_username = parts[0][:2] + '*****' + '@' + parts[1]
                else:
                    masked_username = '*****@' + parts[1]
            else:
                masked_username = '***maskelenmiş***'
            
            current_app.logger.debug(
                f"Mail ayarları: Server={mail_server}, Port={mail_port}, "
                f"TLS={mail_use_tls}, SSL={mail_use_ssl}, Kullanıcı={masked_username}"
            )
        except Exception as e:
            current_app.logger.error(f"Mail ayarlarını loglama hatası: {str(e)}")

    @staticmethod
    def send_email(subject: str, recipients: List[str], 
                   html_body: Optional[str] = None, 
                   text_body: Optional[str] = None, 
                   max_retries: int = 1,
                   attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        E-posta gönder
        
        Args:
            subject: E-posta konusu
            recipients: Alıcı e-posta adresleri listesi
            html_body: HTML içerik
            text_body: Düz metin içerik
            max_retries: Başarısız olursa kaç kez yeniden denenecek
            attachments: Eklenti listesi [{'filename': 'x.pdf', 'data': binary_data, 'content_type': 'application/pdf'}]
            
        Returns:
            bool: Gönderim başarılı ise True, değilse False
        """
        from app import mail
        
        # Alıcıları doğrula
        valid_recipients = MailService._validate_recipients(recipients)
        if not valid_recipients:
            return False
        
        # E-posta ayarlarını logla
        MailService._log_mail_settings()
        
        # Deneme sayacı
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # E-posta gönderimi başlangıç logları
                retry_log = f" (Deneme {retry_count+1}/{max_retries+1})" if retry_count > 0 else ""
                current_app.logger.info(f"E-posta gönderimi başlıyor{retry_log}: Konu: {subject}, Alıcılar: {valid_recipients}")
                
                # Message nesnesi oluştur
                msg = MailService._create_message(subject, valid_recipients, html_body, text_body)
                
                # Eklentileri ekle
                if attachments:
                    for attachment in attachments:
                        msg.attach(
                            attachment.get('filename', 'attachment'),
                            attachment.get('content_type', 'application/octet-stream'),
                            attachment.get('data')
                        )
                
                # E-posta gönder
                mail.send(msg)
                
                # Başarılı gönderim
                current_app.logger.info(f"E-posta gönderimi BAŞARILI{retry_log}: {subject} - Alıcılar: {valid_recipients}")
                return True
                
            except smtplib.SMTPServerDisconnected as disconnect_error:
                # Bağlantı kopması durumunda
                current_app.logger.error(f"SMTP Bağlantı Hatası{retry_log}: {str(disconnect_error)}")
                if retry_count < max_retries:
                    time.sleep(2)
                    retry_count += 1
                    continue
                return False
                    
            except smtplib.SMTPException as smtp_error:
                # SMTP özel hatalarını yakala
                current_app.logger.error(f"SMTP Hatası{retry_log}: {str(smtp_error)}")
                
                if retry_count < max_retries:
                    time.sleep(3)
                    retry_count += 1
                    continue
                return False
                
            except Exception as e:
                # Diğer tüm hatalar
                current_app.logger.error(f"E-posta gönderim hatası{retry_log}: {str(e)}")
                error_details = traceback.format_exc()
                current_app.logger.error(f"Hata detayları: {error_details}")
                
                if retry_count < max_retries:
                    time.sleep(2)
                    retry_count += 1
                    continue
                return False
                
        # Tüm denemeler başarısız oldu
        return False

    @staticmethod
    def send_email_async(subject: str, recipients: List[str], 
                        html_body: Optional[str] = None, 
                        text_body: Optional[str] = None,
                        track_id: Optional[str] = None,
                        max_retries: int = 2,
                        attachments: Optional[List[Dict[str, Any]]] = None) -> bool:
        """
        E-postayı asenkron olarak gönder (arkaplanda)
        
        Args:
            subject: E-posta konusu
            recipients: Alıcı e-posta adresleri listesi
            html_body: HTML içerik
            text_body: Düz metin içerik
            track_id: İzleme ID'si (opsiyonel)
            max_retries: Başarısız olursa kaç kez yeniden denenecek
            attachments: Eklenti listesi
            
        Returns:
            bool: İşlem başarıyla kuyruklandıysa True
        """
        # Alıcıları doğrula
        valid_recipients = MailService._validate_recipients(recipients)
        if not valid_recipients:
            return False

        def send_with_app_context():
            """Uygulama bağlamında e-posta gönder"""
            try:
                # Flask uygulaması bağlamı oluştur
                from app import app
                with app.app_context():
                    # E-posta gönder
                    result = MailService.send_email(
                        subject=subject, 
                        recipients=valid_recipients, 
                        html_body=html_body, 
                        text_body=text_body,
                        max_retries=max_retries,
                        attachments=attachments
                    )
                    
                    # Sonucu logla
                    if track_id:
                        if result:
                            current_app.logger.info(f"Asenkron e-posta gönderimi başarılı (Track ID: {track_id})")
                        else:
                            current_app.logger.error(f"Asenkron e-posta gönderimi başarısız (Track ID: {track_id})")
                    
                    return result
            except Exception as e:
                # Thread içindeki hatalar yutulabilir, bu yüzden açıkça logla
                current_app.logger.error(f"Asenkron e-posta thread hatası: {str(e)}")
                error_details = traceback.format_exc()
                current_app.logger.error(f"Thread hata detayları: {error_details}")
                return False

        try:
            # Arkaplanda çalışacak thread oluştur
            if track_id:
                current_app.logger.info(f"Asenkron e-posta gönderimi başlatılıyor (Track ID: {track_id})")
            
            mail_thread = threading.Thread(target=send_with_app_context)
            mail_thread.daemon = True  # Ana uygulama kapandığında thread de kapanır
            mail_thread.start()
            
            return True
        except Exception as e:
            current_app.logger.error(f"Asenkron e-posta thread oluşturma hatası: {str(e)}")
            return False
