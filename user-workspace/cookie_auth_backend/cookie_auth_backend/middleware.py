from django.utils.deprecation import MiddlewareMixin
from django.middleware.csrf import CsrfViewMiddleware

class CsrfExemptMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Exempt API paths from CSRF verification
        if request.path.startswith((
            '/user/',
            '/admin/users/',
            '/services/',
            '/subscription-plans/',
            '/subscriptions/',
            '/cookies/',
            '/payments/',
        )):
            setattr(request, '_dont_enforce_csrf_checks', True)
        return None
