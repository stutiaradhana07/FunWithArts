from django.conf import settings


class SimpleCORSMiddleware:
    """
    Minimal CORS support for local frontend integration without extra packages.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.method == 'OPTIONS':
            response = self._build_preflight_response()
        else:
            response = self.get_response(request)
        return self._add_cors_headers(request, response)

    def _build_preflight_response(self):
        from django.http import HttpResponse
        return HttpResponse(status=200)

    def _add_cors_headers(self, request, response):
        origin = request.headers.get('Origin')
        if origin and origin in settings.CORS_ALLOWED_ORIGINS:
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Authorization, Content-Type'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PATCH, PUT, DELETE, OPTIONS'
        return response
