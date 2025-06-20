import requests
import logging
import os
import time
from functools import lru_cache

logger = logging.getLogger(__name__)

class GeolocationService:
    """Service for getting IP geolocation data"""
    
    def __init__(self):
        self.api_key = os.environ.get('IPSTACK_API_KEY', '')
        self.last_request_time = 0
        self.rate_limit_delay = 1  # 1 second between requests
    
    @lru_cache(maxsize=1000)
    def get_location_cached(self, ip_address):
        """Get location data with caching to avoid repeated API calls"""
        return self._get_location_from_api(ip_address)
    
    def _get_location_from_api(self, ip_address):
        """Get location data from IP geolocation API"""
        try:
            # Rate limiting
            current_time = time.time()
            time_since_last = current_time - self.last_request_time
            if time_since_last < self.rate_limit_delay:
                time.sleep(self.rate_limit_delay - time_since_last)
            
            self.last_request_time = time.time()
            
            # Skip private/local IPs
            if self._is_private_ip(ip_address):
                return {
                    'country': 'Local',
                    'city': 'Private Network',
                    'latitude': 0.0,
                    'longitude': 0.0
                }
            
            # Try multiple free services
            geo_data = None
            
            # Try ipapi.co first (no API key required)
            try:
                response = requests.get(
                    f'https://ipapi.co/{ip_address}/json/',
                    timeout=5
                )
                if response.status_code == 200:
                    data = response.json()
                    if 'error' not in data:
                        geo_data = {
                            'country': data.get('country_name', 'Unknown'),
                            'city': data.get('city', 'Unknown'),
                            'latitude': float(data.get('latitude', 0)) if data.get('latitude') else 0.0,
                            'longitude': float(data.get('longitude', 0)) if data.get('longitude') else 0.0
                        }
            except Exception as e:
                logger.debug(f"ipapi.co failed for {ip_address}: {e}")
            
            # Try ip-api.com as fallback
            if not geo_data:
                try:
                    response = requests.get(
                        f'http://ip-api.com/json/{ip_address}',
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if data.get('status') == 'success':
                            geo_data = {
                                'country': data.get('country', 'Unknown'),
                                'city': data.get('city', 'Unknown'),
                                'latitude': float(data.get('lat', 0)) if data.get('lat') else 0.0,
                                'longitude': float(data.get('lon', 0)) if data.get('lon') else 0.0
                            }
                except Exception as e:
                    logger.debug(f"ip-api.com failed for {ip_address}: {e}")
            
            # If we have an API key, try ipstack as fallback
            if not geo_data and self.api_key:
                try:
                    response = requests.get(
                        f'http://api.ipstack.com/{ip_address}?access_key={self.api_key}',
                        timeout=5
                    )
                    if response.status_code == 200:
                        data = response.json()
                        if 'error' not in data:
                            geo_data = {
                                'country': data.get('country_name', 'Unknown'),
                                'city': data.get('city', 'Unknown'),
                                'latitude': float(data.get('latitude', 0)) if data.get('latitude') else 0.0,
                                'longitude': float(data.get('longitude', 0)) if data.get('longitude') else 0.0
                            }
                except Exception as e:
                    logger.debug(f"ipstack failed for {ip_address}: {e}")
            
            # Default response if all services fail
            if not geo_data:
                geo_data = {
                    'country': 'Unknown',
                    'city': 'Unknown',
                    'latitude': 0.0,
                    'longitude': 0.0
                }
            
            logger.debug(f"Geolocation for {ip_address}: {geo_data}")
            return geo_data
            
        except Exception as e:
            logger.error(f"Error getting geolocation for {ip_address}: {e}")
            return {
                'country': 'Unknown',
                'city': 'Unknown',
                'latitude': 0.0,
                'longitude': 0.0
            }
    
    def _is_private_ip(self, ip_address):
        """Check if IP address is private/local"""
        try:
            import ipaddress
            ip = ipaddress.ip_address(ip_address)
            return ip.is_private or ip.is_loopback or ip.is_link_local
        except:
            # If we can't parse the IP, assume it's not private
            return False

# Global instance
geolocation_service = GeolocationService()

def get_ip_geolocation(ip_address):
    """Get geolocation data for an IP address"""
    return geolocation_service.get_location_cached(ip_address)
