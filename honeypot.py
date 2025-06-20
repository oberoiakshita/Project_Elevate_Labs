import socket
import threading
import logging
import time
import hashlib
from datetime import datetime
import random
import string
from app import app, db
from models import AttackLog
from geolocation import get_ip_geolocation

logger = logging.getLogger(__name__)

class SSHHoneypot:
    """SSH Honeypot simulation"""
    
    SSH_BANNER = b"SSH-2.0-OpenSSH_7.4\r\n"
    
    def __init__(self, client_socket, client_address):
        self.client_socket = client_socket
        self.client_address = client_address
        self.session_id = self.generate_session_id()
        self.username = None
        self.password = None
        
    def generate_session_id(self):
        """Generate a unique session ID"""
        return hashlib.md5(f"{self.client_address}{time.time()}".encode()).hexdigest()
    
    def handle_connection(self):
        """Handle incoming SSH connection"""
        try:
            logger.info(f"New SSH connection from {self.client_address[0]}:{self.client_address[1]}")
            
            # Send SSH banner
            self.client_socket.send(self.SSH_BANNER)
            
            # Read client banner
            try:
                client_banner = self.client_socket.recv(1024)
                logger.debug(f"Client banner: {client_banner}")
            except:
                client_banner = b"Unknown"
            
            # Simulate SSH handshake
            self.simulate_ssh_handshake()
            
            # Log the connection attempt
            self.log_attack_attempt()
            
        except Exception as e:
            logger.error(f"Error handling SSH connection: {e}")
        finally:
            self.client_socket.close()
    
    def simulate_ssh_handshake(self):
        """Simulate SSH protocol handshake"""
        try:
            # Send key exchange init
            kexinit = self.generate_kexinit()
            self.client_socket.send(kexinit)
            
            # Wait for client response
            time.sleep(0.5)
            
            # Try to receive more data (login attempts)
            for _ in range(3):  # Allow up to 3 login attempts
                try:
                    data = self.client_socket.recv(1024)
                    if not data:
                        break
                    
                    # Try to extract credentials (simplified)
                    self.parse_ssh_data(data)
                    
                    # Send authentication failure
                    auth_failure = b"\x00\x00\x00\x0c\x0a\x33Authentication failed\r\n"
                    self.client_socket.send(auth_failure)
                    
                    time.sleep(1)
                    
                except socket.timeout:
                    break
                except Exception as e:
                    logger.debug(f"Error in SSH simulation: {e}")
                    break
                    
        except Exception as e:
            logger.error(f"Error in SSH handshake simulation: {e}")
    
    def generate_kexinit(self):
        """Generate a fake SSH KEXINIT packet"""
        # Simplified KEXINIT packet
        packet = b"\x00\x00\x01\x2c\x0a\x14" + b"A" * 16  # Fake random data
        packet += b"diffie-hellman-group14-sha1"
        packet += b"\x00" * 50  # Padding
        return packet
    
    def parse_ssh_data(self, data):
        """Try to extract username/password from SSH data (simplified)"""
        try:
            # This is a very simplified approach - real SSH parsing would be much more complex
            data_str = data.decode('utf-8', errors='ignore')
            
            # Look for common patterns that might indicate credentials
            if 'admin' in data_str.lower():
                self.username = 'admin'
            elif 'root' in data_str.lower():
                self.username = 'root'
            elif 'user' in data_str.lower():
                self.username = 'user'
            
            # Generate a random password if we found a username
            if self.username and not self.password:
                common_passwords = ['123456', 'password', 'admin', 'root', '12345', 'qwerty']
                self.password = random.choice(common_passwords)
                
        except Exception as e:
            logger.debug(f"Error parsing SSH data: {e}")
    
    def log_attack_attempt(self):
        """Log the attack attempt to database"""
        try:
            with app.app_context():
                # Get geolocation data
                geo_data = get_ip_geolocation(self.client_address[0])
                
                attack_log = AttackLog(
                    source_ip=self.client_address[0],
                    source_port=self.client_address[1],
                    username=self.username,
                    password=self.password,
                    session_id=self.session_id,
                    attack_type='ssh_login',
                    country=geo_data.get('country'),
                    city=geo_data.get('city'),
                    latitude=geo_data.get('latitude'),
                    longitude=geo_data.get('longitude')
                )
                
                db.session.add(attack_log)
                db.session.commit()
                
                logger.info(f"Logged attack attempt from {self.client_address[0]} (Username: {self.username})")
                
        except Exception as e:
            logger.error(f"Failed to log attack attempt: {e}")

class HoneypotServer:
    """Main honeypot server"""
    
    def __init__(self, host='0.0.0.0', port=2222):
        self.host = host
        self.port = port
        self.server_socket = None
        self.running = False
        
    def start(self):
        """Start the honeypot server"""
        try:
            self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.server_socket.bind((self.host, self.port))
            self.server_socket.listen(10)
            self.running = True
            
            logger.info(f"Honeypot server listening on {self.host}:{self.port}")
            
            while self.running:
                try:
                    client_socket, client_address = self.server_socket.accept()
                    
                    # Handle each connection in a separate thread
                    honeypot = SSHHoneypot(client_socket, client_address)
                    client_thread = threading.Thread(
                        target=honeypot.handle_connection,
                        daemon=True
                    )
                    client_thread.start()
                    
                except Exception as e:
                    if self.running:
                        logger.error(f"Error accepting connection: {e}")
                        
        except Exception as e:
            logger.error(f"Failed to start honeypot server: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Stop the honeypot server"""
        self.running = False
        if self.server_socket:
            self.server_socket.close()
        logger.info("Honeypot server stopped")
