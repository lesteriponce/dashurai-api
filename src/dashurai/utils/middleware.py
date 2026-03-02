import time
import logging
from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from .logging import log_api_request, log_security_event

class RequestLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('api.requests')
        super().__init__(get_response)
    
    def process_request(self, request):
        request.start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            
            # Skip logging for static files and health checks
            if (request.path.startswith('/static/') or 
                request.path.startswith('/media/') or
                request.path == '/health/'):
                return response
            
            # Log API requests
            if request.path.startswith('/api/'):
                log_api_request(request, response)
                
                # Log slow requests
                if duration > 2.0:  
                    self.logger.warning(
                        f"Slow API request: {request.method} {request.path} - "
                        f"Duration: {duration:.2f}s - Status: {response.status_code}"
                    )
        
        return response
    
    def process_exception(self, request, exception):
        log_api_request(request, exception=exception)
        return None


class SecurityLoggingMiddleware(MiddlewareMixin):
    def __init__(self, get_response):
        self.get_response = get_response
        self.logger = logging.getLogger('django.security')
        super().__init__(get_response)
    
    def process_request(self, request):
        # Log requests with suspicious headers
        suspicious_headers = []
        for header, value in request.META.items():
            if header.startswith('HTTP_'):
                if any(pattern in value.lower() for pattern in ['<script', 'javascript:', 'vbscript:']):
                    suspicious_headers.append(f"{header}: {value}")
        
        if suspicious_headers:
            log_security_event(
                'suspicious_headers',
                f"Suspicious headers detected: {'; '.join(suspicious_headers)}",
                getattr(request, 'user', None)
            )
        
        # Log requests from suspicious user agents
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        suspicious_agents = ['sqlmap', 'nikto', 'nmap', 'masscan', 'zap']
        if any(agent in user_agent.lower() for agent in suspicious_agents):
            log_security_event(
                'suspicious_user_agent',
                f"Suspicious user agent: {user_agent}",
                getattr(request, 'user', None)
            )
        
        return None
