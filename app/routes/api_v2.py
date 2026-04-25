"""
REST API v2 — serves the standalone frontend (frontend/).
No auth required; separate from the existing Jinja2 routes.
"""

from flask import Blueprint, jsonify, request
from app.models import Sensor, SensorData, BatteryStatus, Alert, db
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

api_v2_bp = Blueprint('api_v2', __name__, url_prefix='/api/v2')


@api_v2_bp.after_request
def add_cors(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@api_v2_bp.route('/', defaults={'path': ''}, methods=['OPTIONS'])
@api_v2_bp.route('/<path:path>', methods=['OPTIONS'])
def options_handler(path):
    return '', 204


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _time_ago(dt):
    if not dt:
        return 'Never'
    now = datetime.utcnow()
    diff = now - dt
    seconds = int(diff.total_seconds())
    if seconds < 0:
        return 'just now'
    if seconds < 60:
        return f'{seconds} sec ago'
    minutes = seconds // 60
    if minutes < 60:
        return f'{minutes} min ago'
    hours = minutes // 60
    if hours < 24:
        return f'{hours} hr ago'
    days = hours // 24
    return f'{days} day{"s" if days > 1 else ""} ago'


def _build_alert_map():
    """Returns {severity: set(sensor_ids)} for active/acknowledged alerts."""
    rows = Alert.query.filter(Alert.status.in_(['active', 'acknowledged'])).all()
    result = {'high': set(), 'medium': set(), 'low': set()}
    for a in rows:
        result.setdefault(a.severity, set()).add(a.sensor_id)
    return result


def _sensor_status(sensor, alert_map):
    if sensor.id in alert_map.get('high', set()):
        return 'critical'
    if not sensor.is_online():
        return 'offline'
    if sensor.id in alert_map.get('medium', set()):
        return 'warning'
    return 'online'


SEVERITY_DISPLAY = {'high': 'Critical', 'medium': 'Warning', 'low': 'Info'}


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@api_v2_bp.route('/dashboard/stats')
def dashboard_stats():
    sensors = Sensor.query.options(joinedload(Sensor.battery_status)).all()
    alert_map = _build_alert_map()

    total = len(sensors)
    online = sum(1 for s in sensors if s.is_online())
    active_alerts = Alert.query.filter(Alert.status.in_(['active', 'acknowledged'])).count()
    districts = len(set(s.location for s in sensors if s.location))

    return jsonify({
        'total_sensors': total,
        'online_sensors': online,
        'offline_sensors': total - online,
        'active_alerts': active_alerts,
        'districts_count': districts,
        'online_pct': round(online / total * 100, 1) if total > 0 else 0,
    })


@api_v2_bp.route('/sensors')
def list_sensors():
    sensors = Sensor.query.options(joinedload(Sensor.battery_status)).all()
    alert_map = _build_alert_map()

    result = []
    for s in sensors:
        b = s.battery_status
        pct = int(b.battery_percentage) if b and b.battery_percentage is not None else None
        result.append({
            'id': s.id,
            'name': s.name,
            'unique_id': s.unique_id,
            'type': s.sensor_type,
            'model': getattr(s, 'model', None),
            'location': s.location,
            'status': _sensor_status(s, alert_map),
            'battery_pct': pct,
            'last_seen': b.last_seen.isoformat() if b and b.last_seen else None,
            'last_seen_ago': _time_ago(b.last_seen) if b else 'Never',
            'lat': s.latitude,
            'lng': s.longitude,
        })
    return jsonify(result)


@api_v2_bp.route('/sensors/map')
def sensors_map():
    sensors = Sensor.query.options(joinedload(Sensor.battery_status)).filter(
        Sensor.latitude.isnot(None),
        Sensor.longitude.isnot(None),
    ).all()
    alert_map = _build_alert_map()

    return jsonify([{
        'id': s.id,
        'name': s.name,
        'lat': s.latitude,
        'lng': s.longitude,
        'type': s.sensor_type,
        'status': _sensor_status(s, alert_map),
        'battery': int(s.battery_status.battery_percentage)
            if s.battery_status and s.battery_status.battery_percentage is not None else None,
    } for s in sensors])


@api_v2_bp.route('/alerts')
def list_alerts():
    tab = request.args.get('tab', 'all')
    now = datetime.utcnow()
    day_ago = now - timedelta(hours=24)

    all_alerts = Alert.query.options(joinedload(Alert.sensor)).order_by(Alert.created_at.desc()).all()

    total = len(all_alerts)
    unresolved = sum(1 for a in all_alerts if a.status in ('active', 'acknowledged'))
    critical = sum(1 for a in all_alerts if a.severity == 'high' and a.status in ('active', 'acknowledged'))
    resolved_24h = sum(
        1 for a in all_alerts
        if a.status == 'resolved' and a.resolved_at and a.resolved_at >= day_ago
    )

    if tab == 'unresolved':
        filtered = [a for a in all_alerts if a.status in ('active', 'acknowledged')]
    elif tab == 'resolved':
        filtered = [a for a in all_alerts if a.status == 'resolved']
    else:
        filtered = all_alerts

    return jsonify({
        'total': total,
        'unresolved': unresolved,
        'critical': critical,
        'resolved_24h': resolved_24h,
        'alerts': [{
            'id': a.id,
            'sensor_name': a.sensor.name if a.sensor else 'Unknown',
            'sensor_id': a.sensor_id,
            'alert_type': a.alert_type,
            'severity': a.severity,
            'severity_display': SEVERITY_DISPLAY.get(a.severity, a.severity.capitalize()),
            'message': a.message,
            'status': a.status,
            'created_ago': _time_ago(a.created_at),
            'created_at': a.created_at.isoformat() if a.created_at else None,
            'resolved_at': a.resolved_at.isoformat() if a.resolved_at else None,
        } for a in filtered],
    })


@api_v2_bp.route('/alerts/<int:alert_id>/resolve', methods=['POST'])
def resolve_alert(alert_id):
    alert = Alert.query.get_or_404(alert_id)
    alert.resolve()
    db.session.commit()
    return jsonify({'success': True})


@api_v2_bp.route('/dashboard/trends')
def dashboard_trends():
    parameter = request.args.get('parameter', 'temperature')
    cutoff = datetime.utcnow() - timedelta(hours=24)

    rows = db.session.query(
        db.func.strftime('%H:00', SensorData.timestamp).label('hour'),
        db.func.avg(SensorData.value).label('avg_value'),
        db.func.max(SensorData.unit).label('unit'),
    ).filter(
        SensorData.parameter.ilike(f'%{parameter}%'),
        SensorData.timestamp >= cutoff,
    ).group_by('hour').order_by('hour').all()

    return jsonify({
        'parameter': parameter,
        'labels': [r.hour for r in rows],
        'values': [round(r.avg_value, 1) if r.avg_value is not None else 0 for r in rows],
        'unit': rows[0].unit if rows else '',
    })


@api_v2_bp.route('/locations')
def locations():
    sensors = Sensor.query.options(joinedload(Sensor.battery_status)).all()
    alert_map = _build_alert_map()

    loc_map = {}
    for s in sensors:
        loc = s.location or 'Unknown'
        if loc not in loc_map:
            loc_map[loc] = {'total': 0, 'online': 0}
        loc_map[loc]['total'] += 1
        if s.is_online():
            loc_map[loc]['online'] += 1

    location_list = []
    for name, data in sorted(loc_map.items()):
        uptime = int(data['online'] / data['total'] * 100) if data['total'] > 0 else 0
        location_list.append({
            'name': name,
            'total': data['total'],
            'online': data['online'],
            'uptime': uptime,
        })

    map_sensors = [{
        'id': s.id,
        'name': s.name,
        'lat': s.latitude,
        'lng': s.longitude,
        'type': s.sensor_type,
        'status': _sensor_status(s, alert_map),
    } for s in sensors if s.latitude and s.longitude]

    return jsonify({
        'locations': location_list,
        'map_sensors': map_sensors,
    })
