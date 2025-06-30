from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user
from app import db
from models import Notification, User, DOF, DOFStatus, Department
from sqlalchemy import func

api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/notifications')
@login_required
def get_notifications():
    """Kullanıcının okunmamış bildirimlerini döndürür"""
    notifications = Notification.query.filter_by(user_id=current_user.id, is_read=False).order_by(Notification.created_at.desc()).limit(5).all()
    
    result = []
    for notification in notifications:
        result.append({
            'id': notification.id,
            'message': notification.message,
            'created_at': notification.created_at.strftime('%d.%m.%Y %H:%M'),
            'dof_id': notification.dof_id
        })
    
    return jsonify(result)

@api_bp.route('/notifications/mark-read', methods=['POST'])
@login_required
def mark_notification_read():
    """Bildirimi okundu olarak işaretler"""
    notification_id = request.json.get('notification_id')
    
    if not notification_id:
        return jsonify({'success': False, 'message': 'Bildirim ID\'si gereklidir'})
    
    notification = Notification.query.filter_by(id=notification_id, user_id=current_user.id).first()
    
    if not notification:
        return jsonify({'success': False, 'message': 'Bildirim bulunamadı'})
    
    notification.is_read = True
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Bildirim okundu olarak işaretlendi'})

@api_bp.route('/notifications/mark-all-read', methods=['POST'])
@login_required
def mark_all_notifications_read():
    """Tüm bildirimleri okundu olarak işaretler"""
    Notification.query.filter_by(user_id=current_user.id, is_read=False).update({'is_read': True})
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Tüm bildirimler okundu olarak işaretlendi'})

@api_bp.route('/chart-data/dof-status')
@login_required
def dof_status_chart_data():
    """DÖF durumlarına göre sayıları döndürür"""
    result = db.session.query(DOF.status, func.count(DOF.id)).group_by(DOF.status).all()
    
    labels = []
    data = []
    
    status_names = {
        DOFStatus.DRAFT: "Taslak",
        DOFStatus.SUBMITTED: "Gönderildi",
        DOFStatus.IN_REVIEW: "İncelemede",
        DOFStatus.ASSIGNED: "Atandı",
        DOFStatus.IN_PROGRESS: "Devam Ediyor",
        DOFStatus.RESOLVED: "Çözüldü",
        DOFStatus.CLOSED: "Kapatıldı",
        DOFStatus.REJECTED: "Reddedildi"
    }
    
    for status, count in result:
        labels.append(status_names.get(status, "Bilinmiyor"))
        data.append(count)
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'DÖF Durumları',
            'data': data,
            'backgroundColor': [
                '#007bff', '#28a745', '#ffc107', '#dc3545', 
                '#6c757d', '#17a2b8', '#343a40', '#f8f9fa'
            ]
        }]
    })

@api_bp.route('/chart-data/monthly-dofs')
@login_required
def monthly_dofs_chart_data():
    """Aylık DÖF sayılarını döndürür"""
    from datetime import datetime, timedelta
    
    labels = []
    data = []
    
    for i in range(5, -1, -1):
        date = datetime.now() - timedelta(days=30 * i)
        month_name = date.strftime('%B %Y')
        start_date = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        if i > 0:
            end_date = (date.replace(day=1) + timedelta(days=32)).replace(day=1, hour=0, minute=0, second=0, microsecond=0) - timedelta(seconds=1)
        else:
            end_date = datetime.now()
        
        count = DOF.query.filter(DOF.created_at.between(start_date, end_date)).count()
        
        labels.append(month_name)
        data.append(count)
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Aylık DÖF Sayıları',
            'data': data,
            'borderColor': '#007bff',
            'backgroundColor': 'rgba(0, 123, 255, 0.2)',
            'fill': True
        }]
    })

@api_bp.route('/chart-data/department-stats')
@login_required
def department_stats_chart_data():
    """Departman bazında DÖF istatistiklerini döndürür"""
    result = db.session.query(
        Department.name,
        func.count(DOF.id).label('total')
    ).outerjoin(DOF, Department.id == DOF.department_id)\
    .group_by(Department.name).all()
    
    labels = []
    data = []
    
    for dept_name, count in result:
        if not dept_name:  # Skip if department is None
            continue
        
        labels.append(dept_name)
        data.append(count)
    
    return jsonify({
        'labels': labels,
        'datasets': [{
            'label': 'Departmanlara Göre DÖF Sayıları',
            'data': data,
            'backgroundColor': [
                '#007bff', '#28a745', '#ffc107', '#dc3545', 
                '#6c757d', '#17a2b8', '#343a40', '#f8f9fa'
            ]
        }]
    })

@api_bp.route('/user-lookup')
@login_required
def user_lookup():
    """Kullanıcı araması yapar"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    users = User.query.filter(
        (User.username.like(f'%{query}%')) |
        (User.first_name.like(f'%{query}%')) |
        (User.last_name.like(f'%{query}%')) |
        (User.email.like(f'%{query}%'))
    ).filter(User.is_active == True).limit(10).all()
    
    result = []
    for user in users:
        result.append({
            'id': user.id,
            'text': f"{user.first_name} {user.last_name} ({user.username})"
        })
    
    return jsonify(result)

@api_bp.route('/department-lookup')
@login_required
def department_lookup():
    """Departman araması yapar"""
    query = request.args.get('q', '')
    
    if not query or len(query) < 2:
        return jsonify([])
    
    departments = Department.query.filter(
        Department.name.like(f'%{query}%')
    ).filter(Department.is_active == True).limit(10).all()
    
    result = []
    for dept in departments:
        result.append({
            'id': dept.id,
            'text': dept.name
        })
    
    return jsonify(result)

@api_bp.route('/departments')
@login_required 
def get_departments():
    """Tüm aktif departmanları döndürür"""
    departments = Department.query.filter_by(is_active=True).order_by(Department.name).all()
    
    result = []
    for dept in departments:
        result.append({
            'id': dept.id,
            'name': dept.name
        })
    
    return jsonify(result)
