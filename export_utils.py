from flask import send_file
import pandas as pd
from io import BytesIO
from fpdf import FPDF
import tempfile
import os
from datetime import datetime
from models import DOFStatus, DOFType, DOFSource, Department, User, DOFAction

def get_dof_status_name(status_code):
    """Durum kodunu metne cevirir"""
    status_names = {
        DOFStatus.DRAFT: "Taslak",
        DOFStatus.SUBMITTED: "Gonderildi",
        DOFStatus.IN_REVIEW: "Incelemede",
        DOFStatus.ASSIGNED: "Atandi",
        DOFStatus.IN_PROGRESS: "Devam Ediyor",
        DOFStatus.RESOLVED: "Cozuldu",
        DOFStatus.CLOSED: "Kapatildi",
        DOFStatus.REJECTED: "Reddedildi",
        DOFStatus.PLANNING: "Aksiyon Plani Incelemede",
        DOFStatus.IMPLEMENTATION: "Uygulama Asamasinda",
        DOFStatus.COMPLETED: "Tamamlandi",
        DOFStatus.SOURCE_REVIEW: "Kaynak Incelemesinde"
    }
    return status_names.get(status_code, f"Bilinmeyen Durum ({status_code})")

def get_dof_type_name(type_code):
    """DOF tipini metne cevirir"""
    type_names = {
        DOFType.CORRECTIVE: "Duzeltici Faaliyet",
        DOFType.PREVENTIVE: "Onleyici Faaliyet"
    }
    return type_names.get(type_code, f"Bilinmeyen Tip ({type_code})")

def get_dof_source_name(source_code):
    """DOF kaynagini metne cevirir"""
    source_names = {
        DOFSource.INTERNAL_AUDIT: "Ic Denetim",
        DOFSource.EXTERNAL_AUDIT: "Dis Denetim",
        DOFSource.CUSTOMER_COMPLAINT: "Musteri Sikayeti",
        DOFSource.EMPLOYEE_SUGGESTION: "Calisan Onerisi",
        DOFSource.NONCONFORMITY: "Uygunsuzluk",
        DOFSource.OTHER: "Diger"
    }
    return source_names.get(source_code, f"Bilinmeyen Kaynak ({source_code})")

def get_department_name(department_id):
    """Departman ID'sini departman adina cevirir"""
    if not department_id:
        return "Atanmadi"
    
    department = Department.query.get(department_id)
    if department:
        # Türkçe karakterleri ASCII karakterlere dönüştür
        dept_name = department.name
        
        # Karakter dönüşümleri
        tr_chars = {'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 
                   'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
        
        for tr_char, eng_char in tr_chars.items():
            dept_name = dept_name.replace(tr_char, eng_char)
            
        return dept_name
    else:
        return f"Bilinmeyen Departman ({department_id})"

def get_user_name(user_id):
    """Kullanici ID'sini kullanici adina cevirir"""
    if not user_id:
        return "Atanmadi"
    
    user = User.query.get(user_id)
    if user:
        # Türkçe karakterleri ASCII karakterlere dönüştür
        first_name = user.first_name
        last_name = user.last_name
        
        # Karakter dönüşümleri
        tr_chars = {'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 
                   'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
        
        for tr_char, eng_char in tr_chars.items():
            first_name = first_name.replace(tr_char, eng_char)
            last_name = last_name.replace(tr_char, eng_char)
            
        return f"{first_name} {last_name}"
    else:
        return f"Bilinmeyen Kullanici ({user_id})"

def export_dofs_to_excel(dofs):
    """DOF listesini Excel dosyasına dönüştürür"""
    # Ana liste için veri hazırla
    main_data = []
    action_data = []  # Aksiyonlar için ayrı bir tablo
    
    for dof in dofs:
        # Ana DOF bilgileri
        row = {
            'ID': dof.id,
            'Kod': dof.code if dof.code else f"DOF-{dof.id}",
            'Baslik': dof.title,
            'Aciklama': dof.description,
            'Durum': get_dof_status_name(dof.status),
            'Tip': get_dof_type_name(dof.dof_type),
            'Kaynak': get_dof_source_name(dof.dof_source),
            'Departman': get_department_name(dof.department_id),
            'Olusturan': get_user_name(dof.created_by),
            'Atanan Kisi': get_user_name(dof.assigned_to),
            'Olusturma Tarihi': dof.created_at.strftime("%d.%m.%Y %H:%M") if dof.created_at else "",
            'Son Guncelleme': dof.updated_at.strftime("%d.%m.%Y %H:%M") if dof.updated_at else "",
            'Termin Tarihi': dof.due_date.strftime("%d.%m.%Y") if dof.due_date else "",
            'Kapanis Tarihi': dof.closed_at.strftime("%d.%m.%Y") if dof.closed_at else "",
            # Kök neden analizi
            'Kok Neden 1': dof.root_cause1 if dof.root_cause1 else "",
            'Kok Neden 2': dof.root_cause2 if dof.root_cause2 else "",
            'Kok Neden 3': dof.root_cause3 if dof.root_cause3 else "",
            'Kok Neden 4': dof.root_cause4 if dof.root_cause4 else "",
            'Kok Neden 5': dof.root_cause5 if dof.root_cause5 else "",
            # Aksiyon planı ve tarihler
            'Aksiyon Plani': dof.action_plan if dof.action_plan else "",
            'Son Tarih': dof.deadline.strftime("%d.%m.%Y") if dof.deadline else "",
            'Tamamlanma Tarihi': dof.completion_date.strftime("%d.%m.%Y") if dof.completion_date else (dof.closed_at.strftime("%d.%m.%Y") if dof.closed_at else "")
        }
        main_data.append(row)
        
        # DOF'a ait aksiyonları ekle
        actions = DOFAction.query.filter_by(dof_id=dof.id).order_by(DOFAction.created_at.desc()).all()
        for action in actions:
            action_row = {
                'DOF ID': dof.id,
                'DOF Kodu': dof.code if dof.code else f"DOF-{dof.id}",
                'Aksiyon ID': action.id,
    
                'Aciklama': action.comment,
                'Olusturan': get_user_name(action.user_id),
                'Olusturma Tarihi': action.created_at.strftime("%d.%m.%Y %H:%M") if action.created_at else "",
                'Durum': action.old_status if action.old_status is not None else 'N/A',
                'Yeni Durum': action.new_status if action.new_status is not None else 'N/A'
            }
            action_data.append(action_row)
    
    # DataFrames oluştur
    df_main = pd.DataFrame(main_data)
    df_actions = pd.DataFrame(action_data) if action_data else pd.DataFrame()
    
    # Excel dosyası oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_main.to_excel(writer, sheet_name='DOF_Listesi', index=False)
        
        # Sütun genişliklerini ayarla (Ana liste)
        worksheet = writer.sheets['DOF_Listesi']
        for idx, col in enumerate(df_main.columns):
            max_len = max(df_main[col].astype(str).apply(len).max(), len(col)) + 2
            worksheet.column_dimensions[chr(65 + idx)].width = max_len
        
        # Aksiyonlar tablosunu ekle (varsa)
        if not df_actions.empty:
            df_actions.to_excel(writer, sheet_name='Aksiyonlar', index=False)
            
            # Sütun genişliklerini ayarla (Aksiyonlar)
            worksheet = writer.sheets['Aksiyonlar']
            for idx, col in enumerate(df_actions.columns):
                max_len = max(df_actions[col].astype(str).apply(len).max(), len(col)) + 2
                worksheet.column_dimensions[chr(65 + idx)].width = max_len
    
    output.seek(0)
    return output

def replace_turkish_chars(text):
    """Türkçe karakterleri ASCII eşdeğerlerine dönüştürür"""
    if not text:
        return ""
    tr_chars = {'ş': 's', 'Ş': 'S', 'ı': 'i', 'İ': 'I', 'ğ': 'g', 'Ğ': 'G', 
               'ü': 'u', 'Ü': 'U', 'ö': 'o', 'Ö': 'O', 'ç': 'c', 'Ç': 'C'}
    result = text
    for tr_char, eng_char in tr_chars.items():
        result = result.replace(tr_char, eng_char)
    return result

def export_dofs_to_pdf(dofs):
    """DÖF listesini reports sayfası görünümünde güzel PDF olarak oluşturur"""
    try:
        import weasyprint
        from jinja2 import Template
        from collections import Counter
        from datetime import datetime
        import logging
        
        # WeasyPrint log seviyesini düşür (çok verbose olmasın)
        logging.getLogger('weasyprint').setLevel(logging.ERROR)
        
        # İstatistikleri hesapla
        total_dofs = len(dofs)
        status_counts = Counter()
        type_counts = Counter()
        source_counts = Counter()
        dept_counts = Counter()
        
        for dof in dofs:
            if dof.status is not None:
                status_counts[dof.status] += 1
            if dof.dof_type is not None:
                type_counts[dof.dof_type] += 1
            if dof.dof_source is not None:
                source_counts[dof.dof_source] += 1
            if dof.department_id is not None:
                dept_counts[dof.department_id] += 1
        
        # HTML template oluştur - reports sayfası benzeri
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>DÖF Raporu</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 20px; 
                    font-size: 12px; 
                    color: #333;
                    line-height: 1.4;
                }
                .header { 
                    text-align: center; 
                    border-bottom: 3px solid #007bff; 
                    padding-bottom: 20px; 
                    margin-bottom: 30px; 
                }
                .header h1 { 
                    color: #007bff; 
                    margin: 0; 
                    font-size: 24px; 
                    font-weight: bold;
                }
                .header p { 
                    margin: 8px 0 0 0; 
                    color: #6c757d; 
                    font-size: 14px; 
                }
                .stats-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 20px;
                    margin-bottom: 30px;
                }
                .stat-card { 
                    flex: 1;
                    min-width: 200px;
                    border: 1px solid #dee2e6; 
                    border-radius: 8px; 
                    padding: 20px;
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    text-align: center;
                }
                .stat-number {
                    font-size: 28px;
                    font-weight: bold;
                    color: #007bff;
                    margin-bottom: 5px;
                }
                .stat-label {
                    font-size: 12px;
                    color: #6c757d;
                    font-weight: 500;
                }
                .section-title {
                    font-size: 18px;
                    font-weight: bold;
                    color: #495057;
                    border-bottom: 2px solid #007bff;
                    padding-bottom: 8px;
                    margin: 30px 0 20px 0;
                }
                .charts-container {
                    display: flex;
                    flex-wrap: wrap;
                    gap: 30px;
                    margin-bottom: 30px;
                }
                .chart-card {
                    flex: 1;
                    min-width: 300px;
                    border: 1px solid #dee2e6;
                    border-radius: 8px;
                    padding: 20px;
                    background-color: #fff;
                }
                .chart-title {
                    font-size: 16px;
                    font-weight: bold;
                    color: #495057;
                    margin-bottom: 15px;
                    text-align: center;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 8px;
                }
                .chart-item {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    padding: 8px 0;
                    border-bottom: 1px solid #f8f9fa;
                }
                .chart-label {
                    font-size: 11px;
                    color: #495057;
                }
                .chart-value {
                    font-weight: bold;
                    color: #007bff;
                    font-size: 12px;
                }
                .chart-bar {
                    height: 4px;
                    background-color: #007bff;
                    border-radius: 2px;
                    margin-top: 4px;
                }
                .table-container {
                    margin-top: 30px;
                }
                .table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 20px 0;
                    font-size: 10px;
                    background-color: #fff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                }
                .table th { 
                    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
                    color: white;
                    padding: 12px 8px; 
                    text-align: left;
                    font-weight: bold;
                    font-size: 11px;
                }
                .table td { 
                    border-bottom: 1px solid #dee2e6; 
                    padding: 10px 8px; 
                    vertical-align: top;
                }
                .table tr:nth-child(even) {
                    background-color: #f8f9fa;
                }
                .table tr:hover {
                    background-color: #e3f2fd;
                }
                .badge { 
                    display: inline-block;
                    padding: 3px 8px; 
                    border-radius: 12px; 
                    font-size: 9px;
                    font-weight: bold;
                    text-align: center;
                    min-width: 60px;
                }
                .badge-primary { background-color: #007bff; color: white; }
                .badge-success { background-color: #28a745; color: white; }
                .badge-warning { background-color: #ffc107; color: #212529; }
                .badge-info { background-color: #17a2b8; color: white; }
                .badge-danger { background-color: #dc3545; color: white; }
                .badge-secondary { background-color: #6c757d; color: white; }
                .badge-light { background-color: #f8f9fa; color: #495057; border: 1px solid #dee2e6; }
                .footer {
                    margin-top: 40px;
                    text-align: center;
                    font-size: 10px;
                    color: #6c757d;
                    border-top: 1px solid #dee2e6;
                    padding-top: 15px;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>📊 DÖF Raporu</h1>
                <p>{{ filter_info }}</p>
                <p>Rapor Tarihi: {{ report_date }}</p>
            </div>

            <!-- Genel İstatistikler -->
            <div class="stats-container">
                <div class="stat-card">
                    <div class="stat-number">{{ total_dofs }}</div>
                    <div class="stat-label">Toplam DÖF</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ active_dofs }}</div>
                    <div class="stat-label">Devam Eden</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ closed_dofs }}</div>
                    <div class="stat-label">Kapatılan</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">{{ this_month_dofs }}</div>
                    <div class="stat-label">Bu Ay</div>
                </div>
            </div>

            <!-- Dağılım Grafikleri -->
            <div class="charts-container">
                <div class="chart-card">
                    <div class="chart-title">🎯 Durum Dağılımı</div>
                    {% for status_code, count in status_distribution %}
                    <div class="chart-item">
                        <div class="chart-label">{{ get_dof_status_name(status_code) }}</div>
                        <div class="chart-value">{{ count }}</div>
                    </div>
                    <div class="chart-bar" style="width: {{ (count * 100 / max_status_count)|round(1) }}%;"></div>
                    {% endfor %}
                </div>

                <div class="chart-card">
                    <div class="chart-title">🏢 Departman Dağılımı</div>
                    {% for dept_id, count in dept_distribution %}
                    <div class="chart-item">
                        <div class="chart-label">{{ get_department_name(dept_id) }}</div>
                        <div class="chart-value">{{ count }}</div>
                    </div>
                    <div class="chart-bar" style="width: {{ (count * 100 / max_dept_count)|round(1) }}%;"></div>
                    {% endfor %}
                </div>
            </div>

            <div class="charts-container">
                <div class="chart-card">
                    <div class="chart-title">📋 Tür Dağılımı</div>
                    {% for type_code, count in type_distribution %}
                    <div class="chart-item">
                        <div class="chart-label">{{ get_dof_type_name(type_code) }}</div>
                        <div class="chart-value">{{ count }}</div>
                    </div>
                    <div class="chart-bar" style="width: {{ (count * 100 / max_type_count)|round(1) }}%;"></div>
                    {% endfor %}
                </div>

                <div class="chart-card">
                    <div class="chart-title">🔍 Kaynak Dağılımı</div>
                    {% for source_code, count in source_distribution %}
                    <div class="chart-item">
                        <div class="chart-label">{{ get_dof_source_name(source_code) }}</div>
                        <div class="chart-value">{{ count }}</div>
                    </div>
                    <div class="chart-bar" style="width: {{ (count * 100 / max_source_count)|round(1) }}%;"></div>
                    {% endfor %}
                </div>
            </div>

            <!-- DÖF Listesi -->
            <div class="section-title">📋 DÖF Listesi</div>
            <div class="table-container">
                <table class="table">
                    <thead>
                        <tr>
                            <th style="width: 8%;">ID</th>
                            <th style="width: 35%;">Başlık</th>
                            <th style="width: 15%;">Oluşturan</th>
                            <th style="width: 15%;">Departman</th>
                            <th style="width: 12%;">Durum</th>
                            <th style="width: 15%;">Tarih</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for dof in dofs %}
                        <tr>
                            <td><strong>#{{ dof.id }}</strong></td>
                            <td style="font-weight: 500;">{{ dof.title }}</td>
                            <td>{{ get_user_name(dof.created_by) }}</td>
                            <td>{{ get_department_name(dof.department_id) }}</td>
                            <td>
                                <span class="badge {{ get_status_badge_class(dof.status) }}">
                                    {{ get_dof_status_name(dof.status) }}
                                </span>
                            </td>
                            <td>{{ dof.created_at.strftime('%d.%m.%Y') if dof.created_at else '-' }}</td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <div class="footer">
                <p>Bu rapor sistem tarafından otomatik olarak oluşturulmuştur.</p>
                <p>Toplam {{ total_dofs }} DÖF kaydı listelendi.</p>
            </div>
        </body>
        </html>
        """)
        
        # İstatistikleri hesapla
        active_dofs = len([dof for dof in dofs if dof.status not in [6, 7]])  # Kapalı ve reddedilen hariç
        closed_dofs = len([dof for dof in dofs if dof.status == 6])  # Kapalı
        this_month_dofs = len([dof for dof in dofs if dof.created_at and dof.created_at.month == datetime.now().month])
        
        # Dağılımları hazırla
        status_distribution = list(status_counts.most_common())
        dept_distribution = list(dept_counts.most_common())
        type_distribution = list(type_counts.most_common())
        source_distribution = list(source_counts.most_common())
        
        # Maksimum değerleri hesapla (grafik çubukları için)
        max_status_count = max([count for _, count in status_distribution], default=1)
        max_dept_count = max([count for _, count in dept_distribution], default=1)
        max_type_count = max([count for _, count in type_distribution], default=1)
        max_source_count = max([count for _, count in source_distribution], default=1)
        
        # Status badge class fonksiyonu
        def get_status_badge_class(status):
            status_classes = {
                0: 'badge-secondary',  # Taslak
                1: 'badge-info',       # Gönderildi
                2: 'badge-warning',    # İnceleniyor
                3: 'badge-primary',    # Atanmış
                4: 'badge-warning',    # Devam ediyor
                5: 'badge-info',       # Çözülmüş
                6: 'badge-success',    # Kapalı
                7: 'badge-danger',     # Reddedildi
                8: 'badge-info',       # Planlama
                9: 'badge-warning',    # Uygulama
                10: 'badge-success',   # Tamamlandı
                11: 'badge-primary'    # Kaynak İncelemesi
            }
            return status_classes.get(status, 'badge-secondary')
        
        # Template için context hazırla
        context = {
            'total_dofs': total_dofs,
            'active_dofs': active_dofs,
            'closed_dofs': closed_dofs,
            'this_month_dofs': this_month_dofs,
            'dofs': dofs,
            'report_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'filter_info': f"Filtrelenmiş Sonuçlar (Toplam: {total_dofs} DÖF)",
            'status_distribution': status_distribution,
            'dept_distribution': dept_distribution,
            'type_distribution': type_distribution,
            'source_distribution': source_distribution,
            'max_status_count': max_status_count,
            'max_dept_count': max_dept_count,
            'max_type_count': max_type_count,
            'max_source_count': max_source_count,
            'get_dof_status_name': get_dof_status_name,
            'get_dof_type_name': get_dof_type_name,
            'get_dof_source_name': get_dof_source_name,
            'get_department_name': get_department_name,
            'get_user_name': get_user_name,
            'get_status_badge_class': get_status_badge_class
        }
        
        # HTML'i render et
        html_content = html_template.render(**context)
        
        # PDF oluştur
        pdf = weasyprint.HTML(string=html_content).write_pdf()
        
        # BytesIO'ya yaz
        from io import BytesIO
        output = BytesIO()
        output.write(pdf)
        output.seek(0)
        
        return output
        
    except ImportError as e:
        # WeasyPrint yoksa basit PDF'e geri dön
        import logging
        logging.error(f"WeasyPrint import hatası: {str(e)}")
        return create_simple_reports_pdf_fallback(dofs)
    except Exception as e:
        # Başka bir hata durumunda basit PDF'e geç
        import logging
        logging.error(f"WeasyPrint PDF oluşturma hatası: {str(e)}")
        return create_simple_reports_pdf_fallback(dofs)

def create_simple_reports_pdf_fallback(dofs):
    """WeasyPrint yoksa Reports sayfası benzeri güzel PDF oluşturur"""
    from io import BytesIO
    from fpdf import FPDF
    from datetime import datetime
    from collections import Counter
    import os
    
    # PDF oluştur
    pdf = FPDF('P', 'mm', 'A4')  # Portrait orientation
    pdf.add_page()
    
    # Unicode karakterler için font ayarla
    font_path = os.path.join(os.path.dirname(__file__), 'fonts', 'arial.ttf')
    if os.path.exists(font_path):
        pdf.add_font('Arial', '', font_path, uni=True)
        pdf.set_font('Arial', '', 10)
    else:
        pdf.set_font('Arial', '', 10)
    
    # === BAŞLIK SEKSİYONU ===
    pdf.set_font_size(18)
    pdf.set_text_color(0, 123, 255)  # Mavi renk
    pdf.cell(0, 12, f'DOF RAPORU', 0, 1, 'C')
    
    pdf.set_font_size(12)
    pdf.set_text_color(108, 117, 125)  # Gri renk
    pdf.cell(0, 8, f'Filtrelenmis Sonuclar (Toplam: {len(dofs)} DOF)', 0, 1, 'C')
    pdf.cell(0, 6, f'Rapor Tarihi: {datetime.now().strftime("%d.%m.%Y %H:%M")}', 0, 1, 'C')
    pdf.ln(8)
    
    # Çizgi çiz
    pdf.set_draw_color(0, 123, 255)
    pdf.line(20, pdf.get_y(), 190, pdf.get_y())
    pdf.ln(10)
    
    # === İSTATİSTİK KARTLARI ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(14)
    pdf.cell(0, 8, 'GENEL ISTATISTIKLER', 0, 1, 'L')
    pdf.ln(5)
    
    # İstatistikleri hesapla
    total_dofs = len(dofs)
    active_dofs = len([dof for dof in dofs if dof.status not in [6, 7]])
    closed_dofs = len([dof for dof in dofs if dof.status == 6])
    this_month_dofs = len([dof for dof in dofs if dof.created_at and dof.created_at.month == datetime.now().month])
    
    # 4 istatistik kartı
    stats = [
        (f'{total_dofs}', 'Toplam DOF'),
        (f'{active_dofs}', 'Devam Eden'),
        (f'{closed_dofs}', 'Kapatilan'),
        (f'{this_month_dofs}', 'Bu Ay')
    ]
    
    pdf.set_font_size(10)
    x_start = 20
    card_width = 42
    
    for i, (number, label) in enumerate(stats):
        x = x_start + (i * (card_width + 5))
        y = pdf.get_y()
        
        # Kart çerçevesi
        pdf.set_draw_color(222, 226, 230)
        pdf.rect(x, y, card_width, 20)
        
        # Sayı (büyük)
        pdf.set_xy(x + 2, y + 3)
        pdf.set_font_size(16)
        pdf.set_text_color(0, 123, 255)
        pdf.cell(card_width - 4, 8, number, 0, 0, 'C')
        
        # Label (küçük)
        pdf.set_xy(x + 2, y + 12)
        pdf.set_font_size(8)
        pdf.set_text_color(108, 117, 125)
        pdf.cell(card_width - 4, 6, label, 0, 0, 'C')
    
    pdf.ln(25)
    
    # === DURUM DAĞILIMI ===
    pdf.set_text_color(0, 0, 0)
    pdf.set_font_size(12)
    pdf.cell(0, 8, 'DURUM DAGILIMI', 0, 1, 'L')
    pdf.ln(3)
    
    # Durum sayılarını hesapla
    status_counts = Counter()
    for dof in dofs:
        if dof.status is not None:
            status_counts[dof.status] += 1
    
    pdf.set_font_size(9)
    for status_code, count in status_counts.most_common():
        status_name = get_dof_status_name(status_code)
        pdf.cell(60, 6, f'{status_name}:', 0, 0, 'L')
        pdf.cell(20, 6, str(count), 0, 1, 'R')
    
    pdf.ln(5)
    
    # Tablo başlıkları
    pdf.set_font_size(9)
    col_widths = [15, 60, 25, 25, 30, 25, 25, 25]  # Sütun genişlikleri
    headers = ['ID', 'Baslik', 'Olusturan', 'Departman', 'Durum', 'Tur', 'Kaynak', 'Tarih']
    
    # Başlık satırı
    pdf.set_fill_color(230, 230, 230)
    for i, header in enumerate(headers):
        pdf.cell(col_widths[i], 8, header, 1, 0, 'C', True)
    pdf.ln()
    
    # DÖF verileri
    pdf.set_fill_color(255, 255, 255)
    pdf.set_font_size(8)
    
    for i, dof in enumerate(dofs):
        # Zebra striping
        if i % 2 == 0:
            pdf.set_fill_color(255, 255, 255)  # Beyaz
        else:
            pdf.set_fill_color(248, 249, 250)  # Açık gri
        
        # Satır verileri hazırla
        row_data = [
            str(dof.id) if dof.id else 'N/A',
            str(dof.title)[:25] + '...' if len(str(dof.title)) > 25 else str(dof.title) if dof.title else 'N/A',
            get_user_name(dof.created_by)[:12] if dof.created_by else 'N/A',
            get_department_name(dof.department_id)[:12] if dof.department_id else 'N/A',
            get_dof_status_name(dof.status)[:15] if dof.status is not None else 'N/A',
            get_dof_type_name(dof.dof_type)[:12] if dof.dof_type is not None else 'N/A',
            get_dof_source_name(dof.dof_source)[:12] if dof.dof_source is not None else 'N/A',
            dof.created_at.strftime('%d.%m.%Y') if dof.created_at else 'N/A'
        ]
        
        # Satırı yaz
        for j, data in enumerate(row_data):
            pdf.cell(col_widths[j], 6, data, 1, 0, 'L', True)
        pdf.ln()
        
        # Sayfa sonu kontrolü
        if pdf.get_y() > 270:
            pdf.add_page()
            pdf.ln(10)
    
    # === FOOTER ===
    pdf.ln(10)
    pdf.set_font_size(8)
    pdf.set_text_color(108, 117, 125)
    pdf.cell(0, 6, f'Bu rapor {datetime.now().strftime("%d.%m.%Y %H:%M")} tarihinde olusturulmustur.', 0, 1, 'C')
    pdf.cell(0, 6, f'DOF Kalite Yonetim Sistemi - Toplam {len(dofs)} kayit listelenmistir.', 0, 1, 'C')
    
    # PDF'i bytes olarak döndür
    buffer = BytesIO()
    pdf_content = pdf.output()
    
    if isinstance(pdf_content, str):
        buffer.write(pdf_content.encode('latin-1'))
    else:
        buffer.write(pdf_content)
    
    buffer.seek(0)
    return buffer

def create_dof_detail_excel(dof):
    """Tek bir DÖF'ün detayını Excel olarak oluşturur"""
    # DÖF temel bilgileri
    basic_data = [
        ['DÖF ID', dof.id],
        ['DÖF Kodu', dof.code if dof.code else f'DOF-{dof.id}'],
        ['Başlık', dof.title],
        ['Durum', get_dof_status_name(dof.status)],
        ['Tür', get_dof_type_name(dof.dof_type)],
        ['Kaynak', get_dof_source_name(dof.dof_source)],
        ['Oluşturan', get_user_name(dof.created_by)],
        ['Kaynak Departman', get_department_name(dof.creator.department_id if dof.creator and dof.creator.department_id else None)],
        ['Atanan Departman', get_department_name(dof.department_id)],
        ['Atanan Kişi', get_user_name(dof.assigned_to)],
        ['Oluşturma Tarihi', dof.created_at.strftime('%d.%m.%Y %H:%M') if dof.created_at else ''],
        ['Son Güncelleme', dof.updated_at.strftime('%d.%m.%Y %H:%M') if dof.updated_at else ''],
        ['Son Tarih', dof.due_date.strftime('%d.%m.%Y') if dof.due_date else ''],
        ['Termin', dof.deadline.strftime('%d.%m.%Y') if dof.deadline else ''],
        ['Kapanış Tarihi', dof.closed_at.strftime('%d.%m.%Y') if dof.closed_at else ''],
        ['', ''],
        ['Açıklama', dof.description]
    ]
    
    # Müşteri şikayeti ise ek bilgiler
    if dof.dof_source == DOFSource.CUSTOMER_COMPLAINT:
        if hasattr(dof, 'channel') and dof.channel:
            basic_data.insert(-2, ['Şikayet Kanalı', dof.channel])
        if hasattr(dof, 'complaint_date') and dof.complaint_date:
            basic_data.insert(-2, ['Şikayet Tarihi', dof.complaint_date.strftime('%d.%m.%Y')])
    
    # Kök neden analizi
    if any([dof.root_cause1, dof.root_cause2, dof.root_cause3, dof.root_cause4, dof.root_cause5]):
        basic_data.extend([
            ['', ''],
            ['KÖK NEDEN ANALİZİ', '']
        ])
        
        if dof.root_cause1:
            basic_data.append(['1. Neden', dof.root_cause1])
        if dof.root_cause2:
            basic_data.append(['2. Neden', dof.root_cause2])
        if dof.root_cause3:
            basic_data.append(['3. Neden', dof.root_cause3])
        if dof.root_cause4:
            basic_data.append(['4. Neden', dof.root_cause4])
        if dof.root_cause5:
            basic_data.append(['5. Neden (Kök Neden)', dof.root_cause5])
    
    # Aksiyon planı
    if dof.action_plan:
        basic_data.extend([
            ['', ''],
            ['Aksiyon Planı', dof.action_plan]
        ])
    
    # Çözüm
    if dof.resolution:
        basic_data.extend([
            ['', ''],
            ['Çözüm', dof.resolution]
        ])
    
    # İşlem geçmişi
    actions_data = [['Tarih', 'Kullanıcı', 'İşlem Tipi', 'Açıklama']]
    
    actions = DOFAction.query.filter_by(dof_id=dof.id).order_by(DOFAction.created_at.desc()).all()
    for action in actions:
        action_type = ''
        if action.old_status is not None and action.new_status is not None:
            if action.new_status == 10:  # Tamamlandı
                action_type = 'Tamamlandı'
            else:
                action_type = 'Durum Değişikliği'
        else:
            action_type = 'İşlem'
        
        actions_data.append([
            action.created_at.strftime('%d.%m.%Y %H:%M'),
            get_user_name(action.user_id),
            action_type,
            action.comment if action.comment else '-'
        ])
    
    # Excel dosyası oluştur
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        # DÖF detayları sayfası
        df_details = pd.DataFrame(basic_data, columns=['Alan', 'Değer'])
        df_details.to_excel(writer, sheet_name='DÖF_Detayları', index=False)
        
        # Sütun genişliklerini ayarla
        worksheet = writer.sheets['DÖF_Detayları']
        worksheet.column_dimensions['A'].width = 25
        worksheet.column_dimensions['B'].width = 80
        
        # İşlem geçmişi sayfası
        df_actions = pd.DataFrame(actions_data[1:], columns=actions_data[0])
        df_actions.to_excel(writer, sheet_name='İşlem_Geçmişi', index=False)
        
        # İşlem geçmişi sütun genişlikleri
        worksheet = writer.sheets['İşlem_Geçmişi']
        worksheet.column_dimensions['A'].width = 18
        worksheet.column_dimensions['B'].width = 25
        worksheet.column_dimensions['C'].width = 20
        worksheet.column_dimensions['D'].width = 60
    
    output.seek(0)
    return output

def create_dof_detail_pdf(dof):
    """Tek bir DÖF'ün detayını ekran görünümüne benzer PDF olarak oluşturur"""
    try:
        import weasyprint
        from jinja2 import Template
        
        # Status name'i al
        status_name = get_dof_status_name(dof.status)
        
        # Progress bar için adımları hesapla
        def get_progress_status(step_status, current_status):
            if current_status == 6:  # Kapatıldı
                return "active"
            elif step_status <= current_status or (current_status in [5, 10, 11] and step_status <= 11):
                return "active"
            elif step_status == current_status:
                return "current"
            else:
                return ""
        
        # HTML template oluştur - detay sayfasının sadeleştirilmiş hali
        html_template = Template("""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>DÖF #{{ dof.id }} - {{ dof.title }}</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 15px; 
                    font-size: 11px; 
                    color: #333;
                    line-height: 1.4;
                }
                .header { 
                    text-align: center; 
                    border-bottom: 3px solid #007bff; 
                    padding-bottom: 15px; 
                    margin-bottom: 25px; 
                }
                .header h1 { 
                    color: #007bff; 
                    margin: 0; 
                    font-size: 20px; 
                }
                .header p { 
                    margin: 5px 0 0 0; 
                    color: #6c757d; 
                    font-size: 10px; 
                }
                .card { 
                    border: 1px solid #dee2e6; 
                    border-radius: 6px; 
                    margin-bottom: 15px; 
                    background-color: #fff;
                    page-break-inside: avoid;
                }
                .card-header { 
                    background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
                    padding: 12px 15px; 
                    border-bottom: 1px solid #dee2e6;
                    font-weight: bold;
                    font-size: 12px;
                    border-radius: 6px 6px 0 0;
                    color: #495057;
                }
                .card-body { 
                    padding: 15px; 
                }
                .badge { 
                    display: inline-block;
                    padding: 4px 8px; 
                    border-radius: 4px; 
                    font-size: 9px;
                    font-weight: bold;
                }
                .badge-primary { background-color: #007bff; color: white; }
                .badge-success { background-color: #28a745; color: white; }
                .badge-warning { background-color: #ffc107; color: #212529; }
                .badge-info { background-color: #17a2b8; color: white; }
                .badge-danger { background-color: #dc3545; color: white; }
                .badge-secondary { background-color: #6c757d; color: white; }
                
                .info-row { 
                    display: flex; 
                    margin-bottom: 8px; 
                }
                .info-label { 
                    flex: 0 0 25%; 
                    font-weight: bold; 
                    color: #495057; 
                    font-size: 10px;
                }
                .info-value { 
                    flex: 1; 
                    color: #212529; 
                    font-size: 10px;
                }
                .section-title {
                    font-size: 12px;
                    font-weight: bold;
                    color: #495057;
                    border-bottom: 1px solid #dee2e6;
                    padding-bottom: 5px;
                    margin: 15px 0 10px 0;
                }
                .progress-container { 
                    margin: 15px 0; 
                }
                .progressbar { 
                    display: flex; 
                    list-style: none; 
                    padding: 0; 
                    margin: 0;
                    border: 1px solid #dee2e6;
                    border-radius: 4px;
                    overflow: hidden;
                }
                .progressbar li { 
                    flex: 1; 
                    text-align: center; 
                    padding: 8px 2px; 
                    font-size: 8px;
                    background-color: #f8f9fa;
                    border-right: 1px solid #dee2e6;
                    font-weight: 500;
                }
                .progressbar li:last-child { border-right: none; }
                .progressbar li.active { background-color: #28a745; color: white; }
                .progressbar li.current { background-color: #007bff; color: white; font-weight: bold; }
                .description-box {
                    background-color: #f8f9fa;
                    border: 1px solid #e9ecef;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 10px 0;
                    font-size: 10px;
                    line-height: 1.5;
                }
                .table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin: 10px 0;
                    font-size: 9px;
                }
                .table th, .table td { 
                    border: 1px solid #dee2e6; 
                    padding: 6px 8px; 
                    text-align: left;
                }
                .table th { 
                    background-color: #f8f9fa; 
                    font-weight: bold; 
                    color: #495057;
                }
                .table td {
                    vertical-align: top;
                }
                .root-cause-item {
                    margin: 8px 0;
                    padding: 8px;
                    background-color: #fff3cd;
                    border-left: 4px solid #ffc107;
                    border-radius: 0 4px 4px 0;
                    font-size: 10px;
                }
                .root-cause-label {
                    font-weight: bold;
                    color: #856404;
                    margin-bottom: 3px;
                }
                .action-plan-box {
                    background-color: #d4edda;
                    border: 1px solid #c3e6cb;
                    border-radius: 4px;
                    padding: 10px;
                    margin: 10px 0;
                    font-size: 10px;
                    line-height: 1.5;
                }
            </style>
        </head>
        <body>
            <div class="header">
                <h1>DÖF #{{ dof.id }} - Detay Raporu</h1>
                <p>{{ dof.title }}</p>
                <p>Rapor Tarihi: {{ report_date }}</p>
            </div>

            <!-- DÖF Süreç Rehberi -->
            <div class="card">
                <div class="card-header">🔄 DÖF Süreç Rehberi</div>
                <div class="card-body">
                    <div class="progress-container">
                        <ul class="progressbar">
                            <li class="{{ get_progress_class(0, dof.status) }}">1. Taslak</li>
                            <li class="{{ get_progress_class(1, dof.status) }}">2. İnceleme</li>
                            <li class="{{ get_progress_class(3, dof.status) }}">3. Atanmış</li>
                            <li class="{{ get_progress_class(8, dof.status) }}">4. Aksiyon Planı</li>
                            <li class="{{ get_progress_class(9, dof.status) }}">5. Uygulama</li>
                            <li class="{{ get_progress_class(10, dof.status) }}">6. Tamamlandı</li>
                            <li class="{{ get_progress_class(11, dof.status) }}">7. Kaynak Değ.</li>
                            <li class="{{ get_progress_class(5, dof.status) }}">8. Çözüldü</li>
                            <li class="{{ get_progress_class(6, dof.status) }}">9. Kapatıldı</li>
                        </ul>
                    </div>
                    <div style="text-align: center; margin-top: 10px;">
                        <strong>Şu An:</strong> <span class="badge {{ get_status_badge_class(dof.status) }}">{{ status_name }}</span>
                    </div>
                </div>
            </div>

            <!-- Kaynak Bilgileri -->
            <div class="card">
                <div class="card-header">📋 Kaynak Bilgileri</div>
                <div class="card-body">
                    <div class="info-row">
                        <div class="info-label">Oluşturan:</div>
                        <div class="info-value">{{ dof.creator.full_name if dof.creator else 'Belirtilmemiş' }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Kaynak Departman:</div>
                        <div class="info-value">{{ dof.creator.department.name if dof.creator and dof.creator.department else 'Belirtilmemiş' }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">DÖF Türü:</div>
                        <div class="info-value">{{ get_dof_type_name(dof.dof_type) }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">DÖF Kaynağı:</div>
                        <div class="info-value">{{ get_dof_source_name(dof.dof_source) }}</div>
                    </div>
                </div>
            </div>

            <!-- Atama Bilgileri -->
            <div class="card">
                <div class="card-header">👥 Atama Bilgileri</div>
                <div class="card-body">
                    <div class="info-row">
                        <div class="info-label">Atanan Departman:</div>
                        <div class="info-value">{{ dof.department.name if dof.department else 'Henüz atanmadı' }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Oluşturma Tarihi:</div>
                        <div class="info-value">{{ dof.created_at.strftime('%d.%m.%Y %H:%M') if dof.created_at else 'Belirtilmemiş' }}</div>
                    </div>
                    {% if dof.updated_at and dof.updated_at != dof.created_at %}
                    <div class="info-row">
                        <div class="info-label">Son Güncelleme:</div>
                        <div class="info-value">{{ dof.updated_at.strftime('%d.%m.%Y %H:%M') }}</div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Zaman Bilgileri -->
            <div class="card">
                <div class="card-header">⏰ Zaman Bilgileri</div>
                <div class="card-body">
                    <div class="info-row">
                        <div class="info-label">Son Tarih:</div>
                        <div class="info-value">{{ dof.due_date.strftime('%d.%m.%Y') if dof.due_date else 'Belirtilmemiş' }}</div>
                    </div>
                    <div class="info-row">
                        <div class="info-label">Termin:</div>
                        <div class="info-value">{{ dof.deadline.strftime('%d.%m.%Y') if dof.deadline else 'Belirtilmemiş' }}</div>
                    </div>
                    {% if dof.closed_at %}
                    <div class="info-row">
                        <div class="info-label">Kapanış Tarihi:</div>
                        <div class="info-value">{{ dof.closed_at.strftime('%d.%m.%Y') }}</div>
                    </div>
                    {% endif %}
                </div>
            </div>

            <!-- Uygunsuzluk Açıklaması -->
            <div class="card">
                <div class="card-header">📝 Uygunsuzluk Açıklaması</div>
                <div class="card-body">
                    <div class="description-box">
                        {{ dof.description if dof.description else 'Açıklama bulunmuyor.' }}
                    </div>
                </div>
            </div>

            <!-- Kök Neden Analizi -->
            {% if dof.root_cause1 or dof.root_cause2 or dof.root_cause3 or dof.root_cause4 or dof.root_cause5 %}
            <div class="card">
                <div class="card-header">🔍 Kök Neden Analizi (5 Neden Tekniği)</div>
                <div class="card-body">
                    {% if dof.root_cause1 %}
                    <div class="root-cause-item">
                        <div class="root-cause-label">1. Neden:</div>
                        {{ dof.root_cause1 }}
                    </div>
                    {% endif %}
                    {% if dof.root_cause2 %}
                    <div class="root-cause-item">
                        <div class="root-cause-label">2. Neden:</div>
                        {{ dof.root_cause2 }}
                    </div>
                    {% endif %}
                    {% if dof.root_cause3 %}
                    <div class="root-cause-item">
                        <div class="root-cause-label">3. Neden:</div>
                        {{ dof.root_cause3 }}
                    </div>
                    {% endif %}
                    {% if dof.root_cause4 %}
                    <div class="root-cause-item">
                        <div class="root-cause-label">4. Neden:</div>
                        {{ dof.root_cause4 }}
                    </div>
                    {% endif %}
                    {% if dof.root_cause5 %}
                    <div class="root-cause-item" style="background-color: #fff3cd; border-left-color: #fd7e14; border-left-width: 6px;">
                        <div class="root-cause-label" style="color: #dc3545;">5. Neden (Kök Neden):</div>
                        {{ dof.root_cause5 }}
                    </div>
                    {% endif %}
                </div>
            </div>
            {% endif %}

            <!-- Aksiyon Planı -->
            {% if dof.action_plan %}
            <div class="card">
                <div class="card-header">✅ Aksiyon Planı</div>
                <div class="card-body">
                    <div class="action-plan-box">
                        {{ dof.action_plan }}
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- Çözüm -->
            {% if dof.resolution %}
            <div class="card">
                <div class="card-header">🎯 Çözüm</div>
                <div class="card-body">
                    <div class="description-box" style="background-color: #d1ecf1; border-color: #bee5eb;">
                        {{ dof.resolution }}
                    </div>
                </div>
            </div>
            {% endif %}

            <!-- İşlem Geçmişi -->
            <div class="card">
                <div class="card-header">📊 İşlem Geçmişi</div>
                <div class="card-body">
                    <table class="table">
                        <thead>
                            <tr>
                                <th>Tarih</th>
                                <th>Kullanıcı</th>
                                <th>İşlem</th>
                                <th>Açıklama</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for action in actions %}
                            <tr>
                                <td>{{ action.created_at.strftime('%d.%m.%Y %H:%M') if action.created_at else '-' }}</td>
                                <td>{{ get_user_name(action.user_id) }}</td>
                                <td>
                                    {% if action.new_status == 10 %}
                                        Tamamlandı
                                    {% elif action.old_status != action.new_status %}
                                        Durum Değişikliği
                                    {% else %}
                                        İşlem
                                    {% endif %}
                                </td>
                                <td>{{ action.comment if action.comment else '-' }}</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
        </body>
        </html>
        """)
        
        # Template için context hazırla
        context = {
            'dof': dof,
            'status_name': status_name,
            'report_date': datetime.now().strftime('%d.%m.%Y %H:%M'),
            'get_dof_type_name': get_dof_type_name,
            'get_dof_source_name': get_dof_source_name,
            'get_user_name': get_user_name,
            'actions': DOFAction.query.filter_by(dof_id=dof.id).order_by(DOFAction.created_at.desc()).all(),
            'get_progress_class': lambda step_status, current_status: (
                'active' if (current_status == 6) or 
                          (step_status <= current_status) or 
                          (current_status in [5, 10, 11] and step_status <= 11) 
                else 'current' if step_status == current_status 
                else ''
            ),
            'get_status_badge_class': lambda status: (
                'badge-success' if status in [5, 6, 10] 
                else 'badge-danger' if status == 7 
                else 'badge-warning' if status in [8, 9] 
                else 'badge-info'
            )
        }
        
        # HTML render et
        html_content = html_template.render(**context)
        
        # PDF oluştur
        pdf_bytes = weasyprint.HTML(string=html_content).write_pdf()
        
        return pdf_bytes
        
    except ImportError:
        # WeasyPrint yoksa basit PDF oluştur
        return create_simple_pdf_fallback(dof)
    except Exception as e:
        # Başka bir hata durumunda basit PDF'e geç
        import logging
        logging.error(f"WeasyPrint detay PDF hatası: {str(e)}")
        return create_simple_pdf_fallback(dof)

def create_simple_pdf_fallback(dof):
    """WeasyPrint olmadığında basit PDF oluştur"""
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    
    # Başlık
    pdf.set_font("helvetica", "B", 16)
    pdf.cell(0, 10, f"DOF #{dof.id} - Detay Raporu", ln=True, align="C")
    pdf.ln(5)
    
    # Oluşturma tarihi
    pdf.set_font("helvetica", "I", 8)
    pdf.cell(0, 5, f"Rapor Tarihi: {datetime.now().strftime('%d.%m.%Y %H:%M')}", ln=True, align="R")
    pdf.ln(10)
    
    # DÖF Temel Bilgileri
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "DOF Temel Bilgileri", ln=True)
    pdf.ln(2)
    
    pdf.set_font("helvetica", "", 10)
    
    # Tablo formatında bilgileri yazdır
    info_items = [
        ('DOF Kodu:', dof.code if dof.code else f'DOF-{dof.id}'),
        ('Baslik:', replace_turkish_chars(dof.title)),
        ('Durum:', replace_turkish_chars(get_dof_status_name(dof.status))),
        ('Tur:', replace_turkish_chars(get_dof_type_name(dof.dof_type))),
        ('Kaynak:', replace_turkish_chars(get_dof_source_name(dof.dof_source))),
        ('Olusturan:', replace_turkish_chars(get_user_name(dof.created_by))),
        ('Atanan Departman:', replace_turkish_chars(get_department_name(dof.department_id))),
        ('Olusturma Tarihi:', dof.created_at.strftime('%d.%m.%Y %H:%M') if dof.created_at else ''),
        ('Termin:', dof.deadline.strftime('%d.%m.%Y') if dof.deadline else 'Belirlenmemis')
    ]
    
    for label, value in info_items:
        pdf.set_font("helvetica", "B", 9)
        pdf.cell(45, 6, label, 0, 0, "L")
        pdf.set_font("helvetica", "", 9)
        pdf.cell(0, 6, value, 0, 1, "L")
    
    pdf.ln(5)
    
    # Açıklama
    pdf.set_font("helvetica", "B", 11)
    pdf.cell(0, 8, "Aciklama", ln=True)
    pdf.set_font("helvetica", "", 9)
    
    # Açıklamayı satırlara böl
    description = replace_turkish_chars(dof.description)
    lines = description.split('\n')
    for line in lines:
        if len(line) > 90:
            # Uzun satırları böl
            words = line.split(' ')
            current_line = ''
            for word in words:
                if len(current_line + ' ' + word) <= 90:
                    current_line += ' ' + word if current_line else word
                else:
                    if current_line:
                        pdf.cell(0, 5, current_line, ln=True)
                    current_line = word
            if current_line:
                pdf.cell(0, 5, current_line, ln=True)
        else:
            pdf.cell(0, 5, line, ln=True)
    
    # PDF'i BytesIO'ya yazdır
    output = BytesIO()
    pdf.output(output)
    output.seek(0)
    
    return output
