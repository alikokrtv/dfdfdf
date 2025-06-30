from models import DOF, DOFType, DOFSource, User, Department
import unicodedata
import re

def generate_dof_code(dof_type, dof_source, department_id, creator_id=None):
    """
    Kaynak departman, atanan departman, DOF tipi ve kaynak bilgilerine göre dinamik kod oluşturur.
    Örnek: KA-IT-DU-MU-001 (Kalite - IT - Düzeltici - Müşteri şikayeti + sıra numarası)
    
    Args:
        dof_type (int): DOF tipi (1: Düzeltici, 2: Önleyici)
        dof_source (int): DOF kaynağı (1: İç Denetim, 2: Dış Denetim, 3: Müşteri Şikayet, vb.)
        department_id (int): Atanan departman ID'si
        creator_id (int): DOF'u oluşturan kullanıcı ID'si
        
    Returns:
        str: Oluşturulan DOF kodu (örn: "KA-IT-DU-MU-001")
    """
    # DOF tipini metne çevir
    if dof_type == DOFType.CORRECTIVE:
        type_name = "Duzeltici"
    elif dof_type == DOFType.PREVENTIVE:
        type_name = "Onleyici"
    else:
        type_name = "Diger"
        
    # DOF kaynağını metne çevir
    source_name = "Diger"
    if dof_source == DOFSource.INTERNAL_AUDIT:
        source_name = "Ic Denetim"
    elif dof_source == DOFSource.EXTERNAL_AUDIT:
        source_name = "Dis Denetim"
    elif dof_source == DOFSource.CUSTOMER_COMPLAINT:
        source_name = "Musteri Sikayeti"
    elif dof_source == DOFSource.EMPLOYEE_SUGGESTION:
        source_name = "Calisan Onerisi"
    elif dof_source == DOFSource.NONCONFORMITY:
        source_name = "Uygunsuzluk"
    
    # Türkçe karakterleri İngilizce karakterlere dönüştür
    def replace_turkish_chars(text):
        if not text:
            return ""
        # Özel karakterleri dönüştürme
        text = text.replace('Ç', 'C').replace('ç', 'c')
        text = text.replace('Ğ', 'G').replace('ğ', 'g')
        text = text.replace('İ', 'I').replace('ı', 'i')
        text = text.replace('Ö', 'O').replace('ö', 'o')
        text = text.replace('Ş', 'S').replace('ş', 's')
        text = text.replace('Ü', 'U').replace('ü', 'u')
        # Diacritical işaretleri kaldır
        text = ''.join(c for c in unicodedata.normalize('NFD', text)
                      if unicodedata.category(c) != 'Mn')
        # Sadece alfanümerik karakterleri ve tire/alt çizgiyi koru
        text = re.sub(r'[^\w\s-]', '', text)
        return text
    
    # Kaynak departman bilgisini al (oluşturan kullanıcının departmanı)
    source_dept_code = "XX"
    if creator_id:
        creator = User.query.get(creator_id)
        if creator and creator.department_id:
            source_dept = Department.query.get(creator.department_id)
            if source_dept and source_dept.name:
                source_dept_name = replace_turkish_chars(source_dept.name)
                source_dept_code = source_dept_name[:2].upper()
    
    # Atanan departman bilgisini al
    assigned_dept_code = "XX"
    if department_id:
        assigned_dept = Department.query.get(department_id)
        if assigned_dept and assigned_dept.name:
            assigned_dept_name = replace_turkish_chars(assigned_dept.name)
            assigned_dept_code = assigned_dept_name[:2].upper()
    
    # DOF tipi kodunu oluştur
    type_code = type_name[:2].upper() if type_name else "XX"
    
    # DOF kaynağı kodunu oluştur
    source_code = "XX"
    if source_name:
        source_name = replace_turkish_chars(source_name)
        source_code = source_name[:2].upper()
    
    # Oluşturulacak kod formatı: KK-AA-TT-SS
    # KK: Kaynak departman, AA: Atanan departman, TT: Tip kodu, SS: Kaynak kodu (Source)
    code_prefix = f"{source_dept_code}-{assigned_dept_code}-{type_code}-{source_code}"
    
    # Aynı prefixe sahip son DOF kodunu bul
    last_dof = DOF.query.filter(DOF.code.like(f"{code_prefix}-%")).order_by(DOF.code.desc()).first()
    
    if last_dof and last_dof.code:
        try:
            # Son koddaki sayı kısmını al ve bir artır
            last_number = int(last_dof.code.split('-')[-1])
            new_number = last_number + 1
        except (IndexError, ValueError):
            # Kod formatı bozuksa veya başka bir hata varsa 1'den başla
            new_number = 1
    else:
        # Bu prefixi kullanan ilk DOF
        new_number = 1
    
    # Yeni kodu oluştur (Örn: KA-IT-DU-KN-001)
    return f"{code_prefix}-{new_number:03d}"
