"""
Dashboard and main routes.
"""

from flask import Blueprint, render_template, redirect, url_for
from app.routes.auth import login_required
from app.services import SensorService, AlertService
from app.services import SensorService
from app.models import Alert

dashboard_bp = Blueprint('dashboard', __name__, url_prefix='/')


@dashboard_bp.route('/')
@login_required
def index():
    """Main dashboard."""
    stats = SensorService.get_sensor_stats()
    alerts = AlertService.get_active_alerts()
    recent_messages = SensorService.get_recent_messages(limit=20)
    ingestion_stats = SensorService.get_ingestion_stats(minutes=60)
    
    # Alert summary
    alert_summary = {
        'high': len([a for a in alerts if a.severity == 'high']),
        'medium': len([a for a in alerts if a.severity == 'medium']),
        'low': len([a for a in alerts if a.severity == 'low']),
    }
    
    return render_template(
        'dashboard/index.html',
        stats=stats,
        alerts=alerts[:10],  # Show latest 10 alerts
        alert_summary=alert_summary,
        recent_messages=recent_messages,
        ingestion_stats=ingestion_stats,
    )


@dashboard_bp.route('/alerts')
@login_required
def alerts():
    """View all alerts."""
    alerts_list = AlertService.get_active_alerts()
    return render_template('dashboard/alerts.html', alerts=alerts_list)


@dashboard_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
@login_required
def resolve_alert(alert_id):
    """Resolve an alert."""
    from app.models import db
    
    alert = Alert.query.get_or_404(alert_id)
    alert.resolve()
    db.session.commit()
    
    return redirect(url_for('dashboard.alerts'))
