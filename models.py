from datetime import datetime
from app import db

class AttackLog(db.Model):
    """Model for storing attack attempt logs"""
    __tablename__ = 'attack_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    source_ip = db.Column(db.String(45), nullable=False)  # IPv6 compatible
    source_port = db.Column(db.Integer, nullable=False)
    username = db.Column(db.String(255), nullable=True)
    password = db.Column(db.String(255), nullable=True)
    command = db.Column(db.Text, nullable=True)
    session_id = db.Column(db.String(64), nullable=True)
    attack_type = db.Column(db.String(50), default='ssh_login', nullable=False)
    country = db.Column(db.String(100), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    user_agent = db.Column(db.String(500), nullable=True)
    
    def __repr__(self):
        return f'<AttackLog {self.source_ip}:{self.source_port} at {self.timestamp}>'
    
    def to_dict(self):
        """Convert attack log to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None,
            'source_ip': self.source_ip,
            'source_port': self.source_port,
            'username': self.username,
            'password': self.password,
            'command': self.command,
            'session_id': self.session_id,
            'attack_type': self.attack_type,
            'country': self.country,
            'city': self.city,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'user_agent': self.user_agent
        }

class HoneypotStats(db.Model):
    """Model for storing honeypot statistics"""
    __tablename__ = 'honeypot_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, default=datetime.utcnow().date, nullable=False, unique=True)
    total_attacks = db.Column(db.Integer, default=0)
    unique_ips = db.Column(db.Integer, default=0)
    successful_logins = db.Column(db.Integer, default=0)
    failed_logins = db.Column(db.Integer, default=0)
    top_username = db.Column(db.String(255), nullable=True)
    top_password = db.Column(db.String(255), nullable=True)
    
    def __repr__(self):
        return f'<HoneypotStats {self.date}: {self.total_attacks} attacks>'
