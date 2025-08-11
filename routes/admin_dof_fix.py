from flask import Blueprint, render_template, flash, redirect, url_for, request, abort, current_app
from flask_login import login_required, current_user
from extensions import db, mail
from models import User, Department, SystemLog, DOF, DOFAction, WorkflowDefinition, WorkflowStep, UserRole, DOFStatus, UserDepartmentMapping, DirectorManagerMapping
from forms import RegisterForm, DepartmentForm, WorkflowDefinitionForm, WorkflowStepForm, EmailSettingsForm
from utils import log_activity, get_department_stats
from datetime import datetime, timedelta
from sqlalchemy import func, desc
import os

def fixed_reports():
    # DÖF sayıları - İlişkili DÖF'leri filtreleme
    # İlişkili DÖF'ler başlığında "[İlişkili #" prefix'i içerir
    related_dof_filter = ~DOF.title.like("[İlişkili #%")
    dof_counts = db.session.query(DOF.status, func.count(DOF.id)).filter(related_dof_filter).group_by(DOF.status).all()
    
    # Departman istatistikleri
    department_stats = get_department_stats()
    
    # DÖF Tipleri (Düzeltici/Önleyici) - İlişkili DÖF'leri filtrele
    dof_types = db.session.query(DOF.dof_type, func.count(DOF.id)).filter(related_dof_filter).group_by(DOF.dof_type).all()
    corrective_count = 0
    preventive_count = 0
    
    for dof_type, count in dof_types:
        if dof_type == 'corrective':
            corrective_count = count
        elif dof_type == 'preventive':
            preventive_count = count
    
    # Bugün ve bu hafta açılan DÖF'ler - İlişkili DÖF'leri filtrele
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    tomorrow = today + timedelta(days=1)
    todays_count = DOF.query.filter(DOF.created_at.between(today, tomorrow), related_dof_filter).count()
    
    week_start = (today - timedelta(days=today.weekday()))
    weekly_count = DOF.query.filter(DOF.created_at >= week_start, related_dof_filter).count()
    
    # Acil işlem gerektiren DÖF'ler (öncelik alanı kaldırıldı) - İlişkili DÖF'leri filtrele
    # Bunun yerine son tarihi yaklaşan aktif DÖF'leri sayıyoruz
    next_week = today + timedelta(days=7)
    urgent_count = DOF.query.filter(
        DOF.due_date.between(today, next_week),
        DOF.status.notin_([5, 6, 7]),
        related_dof_filter
    ).count()
    
    # Geciken DÖF'ler (Son tarihi geçmiş ancak tamamlanmamış) - İlişkili DÖF'leri filtrele
    overdue_count = DOF.query.filter(
        DOF.due_date < today, 
        DOF.status.notin_([5, 6, 7]),
        related_dof_filter
    ).count()
    
    # Kalite onay süresi (Çözüldü durumundan Kapatıldı durumuna geçiş süresi)
    quality_subquery = db.session.query(
        DOFAction.dof_id,
        func.min(DOFAction.created_at).label('solved_date')
    ).filter(
        DOFAction.action_type == 2,  # 2: Durum Değişikliği
        DOFAction.new_status == 5    # 5: Çözüldü
    ).group_by(DOFAction.dof_id).subquery('quality_subquery')
    
    closed_subquery = db.session.query(
        DOFAction.dof_id,
        func.min(DOFAction.created_at).label('closed_date')
    ).filter(
        DOFAction.action_type == 2,  # 2: Durum Değişikliği
        DOFAction.new_status == 6    # 6: Kapatıldı
    ).group_by(DOFAction.dof_id).subquery('closed_subquery')
    
    quality_approval_time_result = db.session.query(
        func.avg(closed_subquery.c.closed_date - quality_subquery.c.solved_date)
    ).join(
        quality_subquery,
        closed_subquery.c.dof_id == quality_subquery.c.dof_id
    ).scalar()
    
    if quality_approval_time_result is not None:
        quality_approval_time = quality_approval_time_result.total_seconds() / (24 * 3600)  # Gün cinsinden
    else:
        quality_approval_time = 0
    
    # Son 6 ayın DÖF sayıları - İlişkili DÖF'leri filtrele
    months = []
    monthly_counts = []
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        month_name = date.strftime('%B %Y')
        months.append(month_name)
        
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        if i > 0:
            end_date = (date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
        else:
            end_date = datetime.now()
            
        count = DOF.query.filter(DOF.created_at.between(start_date, end_date), related_dof_filter).count()
        monthly_counts.append(count)
    
    # Ortalama çözüm süresi
    avg_resolution_time = db.session.query(
        func.avg(DOFAction.created_at - DOF.created_at)
    ).join(DOF).filter(
        DOFAction.action_type == 2,     # 2: Durum Değişikliği
        DOFAction.new_status == 6,      # 6: Kapatıldı
        related_dof_filter              # İlişkili DÖF'leri filtrele
    ).scalar()
    
    if avg_resolution_time is not None:
        # Decimal nesnesini doğrudan float'a çevirip gün cinsine dönüştür
        avg_resolution_time = float(avg_resolution_time) / (24 * 3600)  # Gün cinsinden
    else:
        avg_resolution_time = 0
    
    # En aktif kullanıcılar
    active_users = db.session.query(User.username, func.count(DOFAction.id).label('action_count'))\
    .join(DOFAction, DOFAction.user_id == User.id)\
    .group_by(User.username)\
    .order_by(desc('action_count'))\
    .limit(5).all()
    
    return {
        'dof_counts': dof_counts,
        'department_stats': department_stats,
        'months': months,
        'monthly_counts': monthly_counts,
        'avg_resolution_time': avg_resolution_time,
        'active_users': active_users,
        'corrective_count': corrective_count,
        'preventive_count': preventive_count,
        'todays_count': todays_count,
        'weekly_count': weekly_count,
        'urgent_count': urgent_count,
        'overdue_count': overdue_count,
        'quality_approval_time': quality_approval_time
    }
