
from django.http import JsonResponse
from django.conf import settings


def get_header(request, name):
    # Django converts headers of the form X-Header to HTTP_X_HEADER
    # except for requests from the test client (weird).
    token = request.META.get(name)
    if not token:
        alt_name = 'HTTP_%s' % name.replace('-', '_').upper()
        token = request.META.get(alt_name)
    return token


def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


class LogRequestMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        print('%s %s - %s - %s - "%s"' % (
            request.method.upper(),
            request.path,
            response.status_code,
            get_client_ip(request),
            request.META.get('HTTP_USER_AGENT', 'Unknown user agent')
        ))
        return response


class InternalAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        token = get_header(request, settings.INTERNAL_AUTH_HEADER)
        if token != settings.INTERNAL_AUTH_TOKEN:
            return JsonResponse({'error': 'Not authorized. Please '\
                'contact hello@toolbox.com to request API access.'},
                status=403)
