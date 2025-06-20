from flask import render_template, jsonify, request
from datetime import datetime, timedelta
from sqlalchemy import func, desc
from app import app, db
from models import AttackLog, HoneypotStats
import logging

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    """Main dashboard page"""
    try:
        # Get recent statistics
        total_attacks = db.session.query(AttackLog).count()
        unique_ips = db.session.query(func.count(func.distinct(AttackLog.source_ip))).scalar()
        
        # Get attacks from last 24 hours
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_attacks = db.session.query(AttackLog).filter(
            AttackLog.timestamp >= yesterday
        ).count()
        
        # Get top attacking countries
        top_countries = db.session.query(
            AttackLog.country,
            func.count(AttackLog.id).label('count')
        ).filter(
            AttackLog.country.isnot(None)
        ).group_by(AttackLog.country).order_by(desc('count')).limit(5).all()
        
        # Get recent attacks for the timeline
        recent_logs = db.session.query(AttackLog).order_by(
            desc(AttackLog.timestamp)
        ).limit(10).all()
        
        stats = {
            'total_attacks': total_attacks,
            'unique_ips': unique_ips,
            'recent_attacks': recent_attacks,
            'top_countries': [{'country': c[0], 'count': c[1]} for c in top_countries]
        }
        
        return render_template('index.html', stats=stats, recent_logs=recent_logs)
        
    except Exception as e:
        logger.error(f"Error loading dashboard: {e}")
        return render_template('index.html', stats={}, recent_logs=[], error=str(e))

@app.route('/logs')
def logs():
    """Attack logs page"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = 50
        
        logs_query = db.session.query(AttackLog).order_by(desc(AttackLog.timestamp))
        logs_pagination = logs_query.paginate(page=page, per_page=per_page, error_out=False)
        
        return render_template('logs.html', logs=logs_pagination.items, pagination=logs_pagination)
        
    except Exception as e:
        logger.error(f"Error loading logs: {e}")
        return render_template('logs.html', logs=[], pagination=None, error=str(e))

@app.route('/analytics')
def analytics():
    """Analytics and visualizations page"""
    return render_template('analytics.html')

@app.route('/api/attacks/recent')
def api_recent_attacks():
    """API endpoint for recent attacks data"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        attacks = db.session.query(AttackLog).filter(
            AttackLog.timestamp >= since
        ).order_by(desc(AttackLog.timestamp)).all()
        
        return jsonify([attack.to_dict() for attack in attacks])
        
    except Exception as e:
        logger.error(f"Error fetching recent attacks: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attacks/by-hour')
def api_attacks_by_hour():
    """API endpoint for attacks grouped by hour"""
    try:
        hours = request.args.get('hours', 24, type=int)
        since = datetime.utcnow() - timedelta(hours=hours)
        
        # Group attacks by hour
        attacks_by_hour = db.session.query(
            func.strftime('%Y-%m-%d %H:00:00', AttackLog.timestamp).label('hour'),
            func.count(AttackLog.id).label('count')
        ).filter(
            AttackLog.timestamp >= since
        ).group_by('hour').order_by('hour').all()
        
        result = []
        for hour, count in attacks_by_hour:
            result.append({
                'hour': hour,
                'count': count
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching attacks by hour: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attacks/by-country')
def api_attacks_by_country():
    """API endpoint for attacks grouped by country"""
    try:
        attacks_by_country = db.session.query(
            AttackLog.country,
            func.count(AttackLog.id).label('count')
        ).filter(
            AttackLog.country.isnot(None)
        ).group_by(AttackLog.country).order_by(desc('count')).limit(20).all()
        
        result = []
        for country, count in attacks_by_country:
            result.append({
                'country': country,
                'count': count
            })
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching attacks by country: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/attacks/map-data')
def api_map_data():
    """API endpoint for map visualization data"""
    try:
        # Get attacks with valid coordinates
        attacks = db.session.query(AttackLog).filter(
            AttackLog.latitude.isnot(None),
            AttackLog.longitude.isnot(None),
            AttackLog.latitude != 0,
            AttackLog.longitude != 0
        ).all()
        
        # Group by coordinates to avoid overlapping markers
        location_counts = {}
        for attack in attacks:
            key = f"{attack.latitude},{attack.longitude}"
            if key not in location_counts:
                location_counts[key] = {
                    'latitude': attack.latitude,
                    'longitude': attack.longitude,
                    'country': attack.country,
                    'city': attack.city,
                    'count': 0,
                    'recent_attacks': []
                }
            location_counts[key]['count'] += 1
            if len(location_counts[key]['recent_attacks']) < 5:
                location_counts[key]['recent_attacks'].append({
                    'timestamp': attack.timestamp.isoformat() if attack.timestamp else None,
                    'username': attack.username,
                    'source_ip': attack.source_ip
                })
        
        return jsonify(list(location_counts.values()))
        
    except Exception as e:
        logger.error(f"Error fetching map data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/top-credentials')
def api_top_credentials():
    """API endpoint for most common usernames and passwords"""
    try:
        # Top usernames
        top_usernames = db.session.query(
            AttackLog.username,
            func.count(AttackLog.id).label('count')
        ).filter(
            AttackLog.username.isnot(None)
        ).group_by(AttackLog.username).order_by(desc('count')).limit(10).all()
        
        # Top passwords
        top_passwords = db.session.query(
            AttackLog.password,
            func.count(AttackLog.id).label('count')
        ).filter(
            AttackLog.password.isnot(None)
        ).group_by(AttackLog.password).order_by(desc('count')).limit(10).all()
        
        result = {
            'usernames': [{'username': u[0], 'count': u[1]} for u in top_usernames],
            'passwords': [{'password': p[0], 'count': p[1]} for p in top_passwords]
        }
        
        return jsonify(result)
        
    except Exception as e:
        logger.error(f"Error fetching top credentials: {e}")
        return jsonify({'error': str(e)}), 500
