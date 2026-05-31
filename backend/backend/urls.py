from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from rest_framework.decorators import api_view
from rest_framework.response import Response
from blogs.views import newsletter_subscribe
from orders.views import delivery_check
from products.views import product_search


from django.http import HttpResponse

@api_view(['GET'])
def health_check(request):
    return Response({'status': 'ok'})


def api_home(request):
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fun With Art | API Hub</title>
        <link href="https://fonts.googleapis.com/css2?family=Playfair+Display:ital,wght@0,600;1,400&family=Lato:wght@300;400;700&display=swap" rel="stylesheet">
        <style>
            body {
                margin: 0;
                padding: 0;
                font-family: 'Lato', sans-serif;
                background-color: #fdfbf9;
                color: #222;
                display: grid;
                place-items: center;
                min-height: 100vh;
                background-image: radial-gradient(circle at 10% 20%, rgba(215, 168, 141, 0.08), transparent 40%), radial-gradient(circle at 90% 80%, rgba(215, 168, 141, 0.08), transparent 40%);
            }
            .card {
                text-align: center;
                background: white;
                padding: 3.5rem 2.5rem;
                border-radius: 24px;
                box-shadow: 0 16px 48px rgba(107, 63, 48, 0.04);
                border: 1px solid rgba(215, 168, 141, 0.15);
                max-width: 480px;
                width: 90%;
            }
            h1 {
                font-family: 'Playfair Display', serif;
                font-size: 2.2rem;
                color: #1f1410;
                margin: 0 0 0.5rem;
                font-weight: 600;
            }
            .badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                background: rgba(107, 185, 120, 0.1);
                color: #2e7d32;
                padding: 6px 14px;
                border-radius: 50px;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.5px;
                text-transform: uppercase;
                margin-bottom: 1.5rem;
            }
            .badge::before {
                content: '';
                display: inline-block;
                width: 6px;
                height: 6px;
                background: #2e7d32;
                border-radius: 50%;
            }
            p {
                color: #6b5e56;
                font-size: 0.95rem;
                line-height: 1.6;
                margin: 0 0 2rem;
            }
            .btn-group {
                display: flex;
                flex-direction: column;
                gap: 12px;
            }
            .btn {
                display: block;
                padding: 14px;
                border-radius: 12px;
                text-decoration: none;
                font-size: 0.9rem;
                font-weight: 700;
                transition: all 0.25s ease;
                text-align: center;
            }
            .btn-primary {
                background: #111;
                color: white;
                box-shadow: 0 10px 20px rgba(0,0,0,0.05);
            }
            .btn-primary:hover {
                background: #d7a88d;
                box-shadow: 0 10px 20px rgba(215, 168, 141, 0.2);
            }
            .btn-secondary {
                background: white;
                color: #6b5e56;
                border: 1px solid rgba(215, 168, 141, 0.3);
            }
            .btn-secondary:hover {
                border-color: #111;
                color: #111;
            }
        </style>
    </head>
    <body>
        <div class="card">
            <span class="badge">API System Online</span>
            <h1>Fun With Art</h1>
            <p>Welcome to the backend API hub for Fun With Art ceramics. The system is fully operational and servicing the artisan storefront.</p>
            <div class="btn-group">
                <a href="/admin/" class="btn btn-primary">Go to Admin Dashboard</a>
                <a href="https://www.funwithartstudio.com" class="btn btn-secondary">Visit Storefront</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_content)


urlpatterns = [
    path('', api_home),
    path('admin/', admin.site.urls),

    # ── API routes (v1) ────────────────────────────────────────────────────
    path('api/health/', health_check),
    path('api/products/', include('products.urls')),
    path('api/search/', product_search),
    path('api/workshops/', include('workshops.urls')),
    path('api/orders/', include('orders.urls')),
    path('api/delivery-check/', delivery_check),
    path('api/auth/', include('accounts.urls')),
    path('api/blogs/', include('blogs.urls')),
    path('api/newsletter/subscribe/', newsletter_subscribe),
    path('api/users/', include('users.urls')),
    path('api/payments/', include('payments.urls')),
    path('api/cart/', include('cart.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
