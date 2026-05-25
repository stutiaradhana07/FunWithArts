from django.conf import settings


class SimpleCORSMiddleware:
    """
    Minimal CORS support for local frontend integration without extra packages.

    In DEBUG mode, also allows requests with Origin: null (filesystem-opened
    HTML files) so you can test directly without running a local dev server.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = self._build_preflight_response(request)
        else:
            response = self.get_response(request)
        return self._add_cors_headers(request, response)

    def _build_preflight_response(self, request):
        from django.http import HttpResponse
        response = HttpResponse(status=200)
        self._add_cors_headers(request, response)
        return response

    def _add_cors_headers(self, request, response):
        origin = request.headers.get('Origin')
        if not origin:
            return response

        allowed = origin in settings.CORS_ALLOWED_ORIGINS
        # Allow filesystem-opened HTML pages (Origin: null) in DEBUG mode
        if not allowed and settings.DEBUG and origin == 'null':
            allowed = True

        if allowed:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
        return response
