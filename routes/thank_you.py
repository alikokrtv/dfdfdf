"""
Teşekkür Bildirimleri Routes
-----------------------
Müşteri İlişkileri departmanı yöneticilerinin dışarıdan gelen teşekkürleri 
kaydetmesi ve yönetmesi için gerekli route'ları içerir.
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, send_file
from flask_login import login_required, current_user
from datetime import datetime
from functools import wraps
from extensions import db
from models import ThankYou, User, Department, UserRole
from forms import ThankYouForm
from utils import create_notification, send_email
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import os

thank_you_bp = Blueprint('thank_you', __name__)

# Teşekkür bildirimi verilerini Excel'e aktarma fonksiyonu
def export_thank_you_to_excel(thank_yous):
    """Teşekkür bildirimlerini Excel formatında dışa aktarır"""
    # Excel için veri hazırla
    data = {
        'ID': [],
        'Başlık': [],
        'Açıklama': [],
        'Departman': [],
        'Oluşturan': [],
        'Tarih': []
    }
    
    for ty in thank_yous:
        # Departman adını al
        department = Department.query.get(ty.department_id)
        department_name = department.name if department else 'Bilinmiyor'
        
        # Oluşturan kullanıcı adını al
        creator = User.query.get(ty.created_by)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else 'Bilinmiyor'
        
        # Verileri ekle
        data['ID'].append(ty.id)
        data['Başlık'].append(ty.title)
        data['Açıklama'].append(ty.description)
        data['Departman'].append(department_name)
        data['Oluşturan'].append(creator_name)
        data['Tarih'].append(ty.created_at.strftime('%d.%m.%Y %H:%M'))
    
    # DataFrame oluştur
    df = pd.DataFrame(data)
    
    # Excel dosyasını oluştur
    output = BytesIO()
    try:
        # xlsxwriter kullanmayı dene
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df.to_excel(writer, sheet_name='Teşekkür Bildirimleri', index=False)
            workbook = writer.book
            worksheet = writer.sheets['Teşekkür Bildirimleri']
            
            # Başlık formatı
            header_format = workbook.add_format({
                'bold': True,
                'text_wrap': True,
                'valign': 'top',
                'fg_color': '#D7E4BC',
                'border': 1
            })
            
            # Sütun başlıklarını formatla
            for col_num, value in enumerate(df.columns.values):
                worksheet.write(0, col_num, value, header_format)
                # Sütun genişliklerini ayarla
                worksheet.set_column(col_num, col_num, 15)
            
            # Açıklama sütununu genişlet
            worksheet.set_column(df.columns.get_loc('Açıklama'), df.columns.get_loc('Açıklama'), 30)
    except ImportError:
        # xlsxwriter yoksa openpyxl kullan
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='Teşekkür Bildirimleri', index=False)
    
    output.seek(0)
    return output

# Teşekkür bildirimi verilerini PDF'e aktarma fonksiyonu
def export_thank_you_to_pdf(thank_yous):
    """Teşekkür bildirimlerini PDF formatında dışa aktarır"""
    # PDF oluştur
    pdf = FPDF()
    pdf.add_page()
    
    # Helvetica font kullan (Arial yerine)
    pdf.set_font('helvetica', size=10)
    
    # Başlık
    pdf.set_font('helvetica', size=16)
    pdf.cell(0, 10, 'Tesekkur Bildirimleri Raporu', 0, 1, 'C')
    pdf.ln(10)
    
    # Tablo başlıkları
    pdf.set_font('helvetica', size=10)
    pdf.set_fill_color(200, 220, 255)
    pdf.cell(15, 10, 'ID', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'Baslik', 1, 0, 'C', 1)
    pdf.cell(50, 10, 'Departman', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'Olusturan', 1, 0, 'C', 1)
    pdf.cell(40, 10, 'Tarih', 1, 1, 'C', 1)
    
    # Tablo içeriği
    for ty in thank_yous:
        # Departman adını al
        department = Department.query.get(ty.department_id)
        department_name = department.name if department else 'Bilinmiyor'
        
        # Oluşturan kullanıcı adını al
        creator = User.query.get(ty.created_by)
        creator_name = f"{creator.first_name} {creator.last_name}" if creator else 'Bilinmiyor'
        
        # Türkçe karakter sorununu önlemek için ASCII karakterlere dönüştür
        title = ''.join(c if ord(c) < 128 else '?' for c in ty.title[:20])
        dept_name = ''.join(c if ord(c) < 128 else '?' for c in department_name)
        creator_name = ''.join(c if ord(c) < 128 else '?' for c in creator_name)
        
        # Verileri ekle
        pdf.cell(15, 10, str(ty.id), 1, 0, 'C')
        pdf.cell(40, 10, title, 1, 0, 'L')
        pdf.cell(50, 10, dept_name, 1, 0, 'L')
        pdf.cell(40, 10, creator_name, 1, 0, 'L')
        pdf.cell(40, 10, ty.created_at.strftime('%d.%m.%Y %H:%M'), 1, 1, 'L')
    
    # Yeni sayfa ekle ve açıklamaları göster
    pdf.add_page()
    pdf.set_font('helvetica', size=12)
    pdf.cell(0, 10, 'Tesekkur Bildirimleri Detaylari', 0, 1, 'C')
    pdf.ln(5)
    
    for ty in thank_yous:
        # Türkçe karakter sorununu önlemek için ASCII karakterlere dönüştür
        title = ''.join(c if ord(c) < 128 else '?' for c in ty.title)
        description = ''.join(c if ord(c) < 128 else '?' for c in ty.description)
        
        pdf.set_font('helvetica', size=10, style='B')
        pdf.cell(0, 10, f"ID: {ty.id} - {title}", 0, 1, 'L')
        pdf.set_font('helvetica', size=8)
        pdf.multi_cell(0, 10, f"Aciklama: {description}", 0, 'L')
        pdf.ln(5)
    
    # PDF'i BytesIO nesnesine yaz (encode hatası düzeltmesi)
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest='S')
    if isinstance(pdf_bytes, str):
        pdf_output.write(pdf_bytes.encode('latin1'))
    else:
        pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output

# Yetki kontrolü için decorator
def customer_relations_manager_required(f):
    """Müşteri İlişkileri departmanı yöneticisi için yetki kontrolü"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Müşteri İlişkileri departmanı ID'si: 2
        customer_relations_dept_id = 2
        
        # Yetki kontrolü - Admin, departman yöneticisi ve departmanı 2 olanlar erişebilir
        if not (current_user.role == UserRole.ADMIN or 
                (current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == customer_relations_dept_id)):
            flash('Bu sayfaya erişim yetkiniz bulunmuyor.', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

@thank_you_bp.route('/list')
@login_required
def list_thank_you():
    """Teşekkür bildirimlerini listele"""
    # Admin ve kalite yöneticileri tüm teşekkürleri görebilir
    if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        thank_yous = ThankYou.query.order_by(ThankYou.created_at.desc()).all()
    # Müşteri İlişkileri departman yöneticileri tüm teşekkürleri görebilir
    elif current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == 2:
        thank_yous = ThankYou.query.order_by(ThankYou.created_at.desc()).all()
    # Diğer departman yöneticileri kendi departmanlarına gelen teşekkürleri görebilir
    elif current_user.role == UserRole.DEPARTMENT_MANAGER:
        thank_yous = ThankYou.query.filter_by(department_id=current_user.department_id).order_by(ThankYou.created_at.desc()).all()
    else:
        flash('Teşekkür bildirimlerini görüntüleme yetkiniz bulunmuyor.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('thank_you/list.html', thank_yous=thank_yous)

@thank_you_bp.route('/create', methods=['GET', 'POST'])
@login_required
@customer_relations_manager_required
def create_thank_you():
    """Yeni teşekkür bildirimi oluştur"""
    form = ThankYouForm()
    
    if form.validate_on_submit():
        try:
            # Yeni teşekkür bildirimi oluştur
            new_thank_you = ThankYou(
                title=form.title.data,
                description=form.description.data,
                department_id=form.department_id.data,
                created_by=current_user.id,
                created_at=datetime.now(),
                is_notified=False
            )
            
            db.session.add(new_thank_you)
            db.session.commit()
            
            # İlgili departmana bildirim gönder
            target_department = Department.query.get(form.department_id.data)
            if target_department:
                # Departman yöneticisine bildirim
                if target_department.manager_id:
                    dept_manager = User.query.get(target_department.manager_id)
                    if dept_manager:
                        # Uygulama içi bildirim
                        notification_text = f"Departmanınıza yeni bir teşekkür bildirimi gönderildi: {form.title.data}"
                        # Sadece kullanıcı id ve mesajı gönder, dof_id parametresi isteğe bağlı
                        create_notification(dept_manager.id, notification_text)
                        
                        # E-posta bildirimi
                        email_subject = f"Yeni Teşekkür Bildirimi: {form.title.data}"
                        view_url = url_for('thank_you.view_thank_you', id=new_thank_you.id, _external=True)
                        
                        # HTML formatlı e-posta gövdesi
                        html_email_body = f"""
                        <html>
                        <body>
                            <p>Sayın {dept_manager.first_name} {dept_manager.last_name},</p>
                            
                            <p>Departmanınıza yeni bir teşekkür bildirimi iletilmiştir.</p>
                            
                            <p><strong>Teşekkür Konusu:</strong> {form.title.data}</p>
                            
                            <p>Detayları görmek için <a href="{view_url}">buraya tıklayabilirsiniz</a>.</p>
                            
                            <p><small>Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.</small></p>
                        </body>
                        </html>
                        """
                        
                        # Düz metin sürümü (HTML desteklemeyen e-posta istemcileri için)
                        plain_email_body = f"""
                        Sayın {dept_manager.first_name} {dept_manager.last_name},
                        
                        Departmanınıza yeni bir teşekkür bildirimi iletilmiştir.
                        
                        Teşekkür Konusu: {form.title.data}
                        
                        Detayları görmek için aşağıdaki linke tıklayabilirsiniz:
                        {view_url}
                        
                        Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.
                        """
                        
                        # HTML formatlı e-posta gönderimi
                        send_email(email_subject, [dept_manager.email], html_email_body, body_text=plain_email_body)
                        
                        # Bildirim gönderildiğine dair durumu güncelle
                        new_thank_you.is_notified = True
                        db.session.commit()
            
            # Teşekkür bildirimini gönderdiğini kullanıcıya bildir
            flash('Teşekkür bildirimi başarıyla kaydedildi ve ilgili departmana bildirim gönderildi.', 'success')
            return redirect(url_for('thank_you.list_thank_you'))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Teşekkür bildirimi oluşturma hatası: {str(e)}")
            flash(f'Teşekkür bildirimi oluşturulurken bir hata oluştu: {str(e)}', 'danger')
    
    return render_template('thank_you/create.html', form=form)

@thank_you_bp.route('/view/<int:id>')
@login_required
def view_thank_you(id):
    """Teşekkür bildirimi detaylarını görüntüle"""
    thank_you = ThankYou.query.get_or_404(id)
    
    # Yetki kontrolü
    if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        # Admin ve kalite yöneticileri her şeyi görebilir
        pass
    elif current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == 2:
        # Müşteri İlişkileri departmanı yöneticileri tüm teşekkürleri görebilir
        pass
    elif current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == thank_you.department_id:
        # Departman yöneticileri kendi departmanlarına gelen teşekkürleri görebilir
        pass
    else:
        flash('Bu teşekkür bildirimini görüntüleme yetkiniz bulunmuyor.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    return render_template('thank_you/view.html', thank_you=thank_you)

@thank_you_bp.route('/send-notification/<int:id>', methods=['POST'])
@login_required
def send_notification(id):
    """Teşekkür bildirimini ilgili departmana tekrar gönderir"""
    # Yetki kontrolü
    if not (current_user.role == UserRole.ADMIN or 
            (current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == 2)):
        flash('Bu işlem için yetkiniz bulunmuyor.', 'danger')
        return redirect(url_for('main.dashboard'))
    
    thank_you = ThankYou.query.get_or_404(id)
    
    try:
        # İlgili departmana bildirim gönder
        dept_managers = User.query.filter_by(
            department_id=thank_you.department_id,
            role=UserRole.DEPARTMENT_MANAGER,
            active=True
        ).all()
        
        if dept_managers:
            for dept_manager in dept_managers:
                # Bildirim oluştur
                notification_text = f"Departmanınıza yeni bir teşekkür mesajı iletildi: {thank_you.title}"
                create_notification(dept_manager.id, notification_text)
                
                # E-posta gönder
                email_subject = f"Yeni Teşekkür Bildirimi: {thank_you.title}"
                email_body = f"""
                Sayın {dept_manager.first_name} {dept_manager.last_name},
                
                Departmanınıza yeni bir teşekkür bildirimi iletilmiştir.
                
                Teşekkür Konusu: {thank_you.title}
                
                Detayları görmek için lütfen sisteme giriş yapınız.
                
                Bu e-posta otomatik olarak gönderilmiştir, lütfen yanıtlamayınız.
                """
                send_email(email_subject, [dept_manager.email], email_body)
            
            # Teşekkür bildirim durumunu güncelle
            thank_you.is_notified = True
            db.session.commit()
            
            flash(f"Teşekkür bildirimi {len(dept_managers)} departman yöneticisine başarıyla gönderildi.", 'success')
        else:
            flash('Bu departman için aktif yönetici bulunamadı. Bildirim gönderilemedi.', 'warning')
    
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Teşekkür bildirimi gönderme hatası: {str(e)}")
        flash(f'Teşekkür bildirimi gönderilirken bir hata oluştu: {str(e)}', 'danger')
    
    return redirect(url_for('thank_you.view_thank_you', id=id))

@thank_you_bp.route('/my')
@login_required
def my_thank_you():
    """Kullanıcının departmanına gelen teşekkürleri göster"""
    # Kullanıcının departmanını al
    user_dept_id = current_user.department_id
    
    if not user_dept_id:
        flash('Departman bilginiz bulunamadı.', 'warning')
        return redirect(url_for('home'))
    
    # Kullanıcının departmanına gelen teşekkürleri getir
    thank_yous = ThankYou.query.filter_by(department_id=user_dept_id)\
                .order_by(ThankYou.created_at.desc()).all()
    
    # Her bir teşekkür için oluşturan kullanıcı bilgisini ekle
    for item in thank_yous:
        item.creator = User.query.get(item.created_by) if item.created_by else None
    
    return render_template('thank_you/my_thank_you.html', thank_yous=thank_yous)

@thank_you_bp.route('/report')
@login_required
def report_thank_you():
    """Teşekkür bildirimleri raporu"""
    # Sadece admin ve kalite yöneticileri raporu görebilir
    if not current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
        flash('Teşekkür raporlarını görüntüleme yetkiniz bulunmuyor.', 'warning')
        return redirect(url_for('main.dashboard'))
    
    # Departman bazında teşekkür bildirimi sayıları
    dept_counts = db.session.query(
        Department.name,
        db.func.count(ThankYou.id)
    ).outerjoin(ThankYou, Department.id == ThankYou.department_id)\
     .group_by(Department.name)\
     .order_by(db.func.count(ThankYou.id).desc())\
     .all()
    
    # Aylık teşekkür bildirimi sayıları
    month_counts = db.session.query(
        db.func.strftime('%Y-%m', ThankYou.created_at).label('month'),
        db.func.count(ThankYou.id)
    ).group_by('month')\
     .order_by('month')\
     .all()
    
    return render_template('thank_you/report.html', 
                           dept_counts=dept_counts, 
                           month_counts=month_counts)

@thank_you_bp.route('/export/excel')
@login_required
def export_thank_you_excel():
    """Teşekkür bildirimlerini Excel formatında dışa aktar"""
    try:
        # Yetki kontrolü
        if not (current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER] or 
                (current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == 2)):
            flash('Bu işlem için yetkiniz bulunmuyor.', 'danger')
            return redirect(url_for('thank_you.list_thank_you'))
        
        # Admin ve kalite yöneticileri tüm teşekkürleri görebilir
        if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
            thank_yous = ThankYou.query.order_by(ThankYou.created_at.desc()).all()
        # Departman yöneticileri kendi departmanlarına gelen teşekkürleri görebilir
        elif current_user.role == UserRole.DEPARTMENT_MANAGER:
            thank_yous = ThankYou.query.filter_by(department_id=current_user.department_id).order_by(ThankYou.created_at.desc()).all()
        else:
            thank_yous = []
        
        # Excel dosyasını oluştur
        output = export_thank_you_to_excel(thank_yous)
        
        # Dosyayı indir
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            download_name=f'tesekkur_bildirimleri_{datetime.now().strftime("%Y%m%d%H%M%S")}.xlsx',
            as_attachment=True
        )
    except Exception as e:
        current_app.logger.error(f"Excel dışa aktarma hatası: {str(e)}")
        flash('Excel dosyası oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('thank_you.list_thank_you'))

@thank_you_bp.route('/export/pdf')
@login_required
def export_thank_you_pdf():
    """Teşekkür bildirimlerini PDF formatında dışa aktar"""
    try:
        # Yetki kontrolü
        if not (current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER] or 
                (current_user.role == UserRole.DEPARTMENT_MANAGER and current_user.department_id == 2)):
            flash('Bu işlem için yetkiniz bulunmuyor.', 'danger')
            return redirect(url_for('thank_you.list_thank_you'))
        
        # Admin ve kalite yöneticileri tüm teşekkürleri görebilir
        if current_user.role in [UserRole.ADMIN, UserRole.QUALITY_MANAGER]:
            thank_yous = ThankYou.query.order_by(ThankYou.created_at.desc()).all()
        # Departman yöneticileri kendi departmanlarına gelen teşekkürleri görebilir
        elif current_user.role == UserRole.DEPARTMENT_MANAGER:
            thank_yous = ThankYou.query.filter_by(department_id=current_user.department_id).order_by(ThankYou.created_at.desc()).all()
        else:
            thank_yous = []
        
        # PDF dosyasını oluştur
        output = export_thank_you_to_pdf(thank_yous)
        
        # Dosyayı indir
        return send_file(
            output,
            mimetype='application/pdf',
            download_name=f'tesekkur_bildirimleri_{datetime.now().strftime("%Y%m%d%H%M%S")}.pdf',
            as_attachment=True
        )
    except Exception as e:
        current_app.logger.error(f"PDF dışa aktarma hatası: {str(e)}")
        flash('PDF dosyası oluşturulurken bir hata oluştu.', 'danger')
        return redirect(url_for('thank_you.list_thank_you'))
