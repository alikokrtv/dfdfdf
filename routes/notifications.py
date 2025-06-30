from flask import Blueprint, render_template, redirect, url_for, flash, current_app, request
from flask_login import login_required, current_user
from app import db
from models import Notification, User
from sqlalchemy import desc
from functools import wraps

notifications_bp = Blueprint('notifications', __name__)

# Bildirim sayfası için route
@notifications_bp.route('/notifications')
@login_required
def all_notifications():
    page = request.args.get('page', 1, type=int)
    per_page = 20  # Her sayfada 20 bildirim göster
    
    # Tüm bildirimler
    pagination = current_user.notifications.order_by(desc(Notification.created_at)).paginate(
        page=page, per_page=per_page, error_out=False
    )
    notifications = pagination.items
    
    # Okunmamış bildirimler
    unread_notifications = current_user.notifications.filter_by(is_read=False).order_by(desc(Notification.created_at)).all()
    
    return render_template(
        'notifications/all_notifications.html',
        notifications=notifications,
        unread_notifications=unread_notifications,
        pagination=pagination
    )

# Bildirimi okundu olarak işaretle
@notifications_bp.route('/notifications/<int:notification_id>/mark_read')
@login_required
def mark_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    # Sadece kendi bildirimlerini okundu işaretleyebilir
    if notification.user_id != current_user.id:
        flash('Bu işlemi yapma yetkiniz yok.', 'danger')
        return redirect(url_for('notifications.all_notifications'))
    
    notification.is_read = True
    db.session.commit()
    
    flash('Bildirim okundu olarak işaretlendi.', 'success')
    return redirect(url_for('notifications.all_notifications'))

# Tüm bildirimleri okundu olarak işaretle
@notifications_bp.route('/notifications/mark_all_read')
@login_required
def mark_all_read():
    # Kullanıcının tüm okunmamış bildirimlerini al
    unread_notifications = current_user.notifications.filter_by(is_read=False).all()
    
    for notification in unread_notifications:
        notification.is_read = True
    
    db.session.commit()
    
    num_marked = len(unread_notifications)
    flash(f'{num_marked} bildirim okundu olarak işaretlendi.', 'success')
    return redirect(url_for('notifications.all_notifications'))
