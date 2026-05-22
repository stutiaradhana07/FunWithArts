from django.contrib import admin
from django.utils.text import slugify
from .models import NewsletterSubscriber, Post


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('email',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
    actions = ['mark_inactive']

    @admin.action(description='Mark selected subscribers as inactive')
    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'author', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'excerpt', 'content')
    readonly_fields = ('created_at', 'updated_at')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)
