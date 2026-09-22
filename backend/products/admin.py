from django.conf import settings
from django.contrib import admin, messages
from django.db import models
from django.db.models import Count, Q
from django.urls import reverse
from django.utils.html import format_html

from .models import Category, Product, ProductQuestion, Review
from .widgets import AdminImagePreviewWidget, AdminVideoPreviewWidget


class StockStatusFilter(admin.SimpleListFilter):
    title = 'Stock Status'
    parameter_name = 'stock_status'

    def lookups(self, request, model_admin):
        threshold = getattr(settings, 'PRODUCT_LOW_STOCK_THRESHOLD', 5)
        return (
            ('in_stock', f'In Stock (> {threshold})'),
            ('low_stock', f'Low Stock (1–{threshold})'),
            ('out_of_stock', 'Out of Stock (0)'),
        )

    def queryset(self, request, queryset):
        threshold = getattr(settings, 'PRODUCT_LOW_STOCK_THRESHOLD', 5)
        val = self.value()
        if val == 'in_stock':
            return queryset.filter(stock__gt=threshold)
        if val == 'low_stock':
            return queryset.filter(stock__gt=0, stock__lte=threshold)
        if val == 'out_of_stock':
            return queryset.filter(stock__lte=0)
        return queryset


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        'thumbnail_display',
        'name',
        'category',
        'price',
        'stock',
        'stock_badge',
        'is_available',
        'is_new',
        'created_at_formatted',
        'storefront_link',
    )
    list_display_links = ('thumbnail_display',)
    list_editable = (
        'name',
        'price',
        'stock',
        'is_available',
        'is_new',
    )
    list_filter = (
        'category',
        'is_available',
        'is_new',
        StockStatusFilter,
        ('created_at', admin.DateFieldListFilter),
    )
    search_fields = (
        '=id',
        'name',
        'category__name',
        'description',
    )
    search_help_text = 'Search by exact ID (e.g. 12), product name, category, or description...'
    list_per_page = 20
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'category', 'description')
        }),
        ('Pricing & Inventory', {
            'fields': (
                ('price', 'stock'),
                ('has_set_option', 'set_price'),
                ('is_available', 'is_new'),
            )
        }),
        ('Product Media', {
            'fields': ('image', 'image2', 'image3', 'video'),
            'description': 'Upload primary and additional images or product video.'
        }),
        ('Display Settings', {
            'fields': ('image_position', 'image_zoom'),
            'description': 'Focal-point cropping and zoom level for the storefront archive page.'
        }),
        ('Metadata', {
            'classes': ('collapse',),
            'fields': ('created_at',),
        }),
    )

    formfield_overrides = {
        models.ImageField: {'widget': AdminImagePreviewWidget},
        models.FileField: {'widget': AdminVideoPreviewWidget},
    }

    actions = [
        'mark_available',
        'mark_unavailable',
        'mark_as_new',
        'remove_new_status',
    ]

    class Media:
        js = (
            'admin/js/focal_point_picker.js',
            'admin/js/product_admin.js',
        )
        css = {
            'all': (
                'admin/css/focal_point_picker.css',
                'admin/css/product_admin.css',
            )
        }

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('category')

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        threshold = getattr(settings, 'PRODUCT_LOW_STOCK_THRESHOLD', 5)
        stats = Product.objects.aggregate(
            total=Count('id'),
            active=Count('id', filter=Q(is_available=True)),
            low_stock=Count('id', filter=Q(stock__gt=0, stock__lte=threshold)),
            out_of_stock=Count('id', filter=Q(stock__lte=0)),
        )
        extra_context['catalog_stats'] = stats
        extra_context['low_stock_threshold'] = threshold
        return super().changelist_view(request, extra_context=extra_context)

    @admin.display(description='Image', ordering='id')
    def thumbnail_display(self, obj):
        change_url = reverse('admin:products_product_change', args=[obj.pk])
        if obj.image and hasattr(obj.image, 'url'):
            url = obj.image.url
            if 'res.cloudinary.com' in url and '/upload/' in url:
                thumb_url = url.replace('/upload/', '/upload/c_fill,w_120,h_120,q_auto,f_auto/')
                popover_url = url.replace('/upload/', '/upload/c_fill,w_360,h_360,q_auto,f_auto/')
            else:
                thumb_url = url
                popover_url = url

            return format_html(
                '<div class="product-thumb-container">'
                '  <a href="{0}" class="product-thumb-link" title="Edit {1}">'
                '    <img src="{2}" alt="{1}" class="product-thumb-img" loading="lazy" />'
                '  </a>'
                '  <div class="product-thumb-zoom">'
                '    <img src="{3}" alt="{1}" loading="lazy" />'
                '  </div>'
                '</div>',
                change_url,
                obj.name,
                thumb_url,
                popover_url,
            )

        return format_html(
            '<div class="product-thumb-container">'
            '  <a href="{0}" class="product-thumb-link product-thumb-placeholder" title="Edit {1} (No image)">'
            '    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">'
            '      <path d="M8 3h8l1 4-2 7v5a2 2 0 0 1-2 2h-2a2 2 0 0 1-2-2v-5l-2-7 1-4z"/>'
            '      <path d="M6 7h12"/>'
            '    </svg>'
            '  </a>'
            '</div>',
            change_url,
            obj.name,
        )

    @admin.display(description='Stock Status', ordering='stock')
    def stock_badge(self, obj):
        threshold = getattr(settings, 'PRODUCT_LOW_STOCK_THRESHOLD', 5)
        stock = obj.stock
        if stock is None or stock <= 0:
            return format_html(
                '<span class="stock-badge badge-out-of-stock" data-product-id="{0}">✖ Out of Stock</span>',
                obj.pk
            )
        elif stock <= threshold:
            return format_html(
                '<span class="stock-badge badge-low-stock" data-product-id="{0}">⚠ Low Stock ({1})</span>',
                obj.pk,
                stock
            )
        else:
            return format_html(
                '<span class="stock-badge badge-in-stock" data-product-id="{0}">● In Stock ({1})</span>',
                obj.pk,
                stock
            )

    @admin.display(description='Created', ordering='created_at')
    def created_at_formatted(self, obj):
        if not obj.created_at:
            return '-'
        return obj.created_at.strftime('%d %b %Y')

    @admin.display(description='Store')
    def storefront_link(self, obj):
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173').rstrip('/')
        url = f"{frontend_url}/product/{obj.slug or obj.pk}"
        return format_html(
            '<a href="{0}" target="_blank" rel="noopener noreferrer" class="product-store-link" title="Open product in store">'
            '  ↗ View'
            '</a>',
            url
        )

    @admin.action(description='Mark selected products as Available')
    def mark_available(self, request, queryset):
        updated = queryset.update(is_available=True)
        self.message_user(request, f'{updated} product(s) marked as available.', messages.SUCCESS)

    @admin.action(description='Mark selected products as Unavailable')
    def mark_unavailable(self, request, queryset):
        updated = queryset.update(is_available=False)
        self.message_user(request, f'{updated} product(s) marked as unavailable.', messages.SUCCESS)

    @admin.action(description='Mark selected products as New')
    def mark_as_new(self, request, queryset):
        updated = queryset.update(is_new=True)
        self.message_user(request, f'{updated} product(s) marked as new.', messages.SUCCESS)

    @admin.action(description='Remove New status from selected products')
    def remove_new_status(self, request, queryset):
        updated = queryset.update(is_new=False)
        self.message_user(request, f'Removed New status from {updated} product(s).', messages.SUCCESS)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'product', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('user__username', 'product__name', 'comment')
    raw_id_fields = ('user', 'product')


@admin.register(ProductQuestion)
class ProductQuestionAdmin(admin.ModelAdmin):
    list_display = ('id', 'product', 'asker_name', 'is_answered', 'answered_by', 'created_at')
    list_filter = ('created_at', 'answered_at')
    search_fields = ('product__name', 'asker_name', 'question', 'answer_text')
    raw_id_fields = ('product', 'user', 'answered_by')
