from django import forms
from django.contrib import admin
from django.utils.text import slugify
from .models import NewsletterSubscriber, Post


FONT_SIZE_CHOICES = [
    ('', 'Default Size'),
    ('24px', '24px (Small)'),
    ('28px', '28px (Medium-Small)'),
    ('32px', '32px (Medium)'),
    ('40px', '40px (Large)'),
    ('48px', '48px (Extra Large)'),
    ('56px', '56px (2XL)'),
    ('64px', '64px (3XL)'),
    ('72px', '72px (4XL)'),
]


class PostAdminForm(forms.ModelForm):
    title_font_size = forms.ChoiceField(
        choices=FONT_SIZE_CHOICES,
        initial='40px',
        required=False,
        help_text='Select the font size for the title'
    )
    title_color = forms.CharField(
        widget=forms.TextInput(attrs={
            'type': 'color',
            'class': 'color-picker-input',
            'style': 'width: 60px; height: 35px; border: 1px solid #ccc; border-radius: 4px; cursor: pointer; padding: 0; vertical-align: middle;'
        }),
        initial='#1e293b',
        required=False,
        help_text='Choose the title color'
    )

    class Meta:
        model = Post
        fields = '__all__'
        widgets = {
            'content': forms.Textarea(attrs={'class': 'vLargeTextField rich-text-editor'}),
            'excerpt': forms.Textarea(attrs={'rows': 4}),
        }


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
    form = PostAdminForm
    list_display = ('title', 'status', 'author', 'published_at', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('title', 'excerpt', 'content')
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('-created_at',)
    fieldsets = (
        (None, {
            'fields': (
                'title',
                'title_is_bold',
                'title_is_italic',
                'title_font_size',
                'title_color',
                'slug',
                'author',
                'cover_image',
                'cover_image_position',
                'excerpt',
                'content',
                'status',
                'published_at',
                'created_at',
                'updated_at',
            ),
        }),
    )

    @property
    def media(self):
        from django.conf import settings
        api_key = getattr(settings, 'TINYMCE_API_KEY', 'no-api-key')
        return forms.Media(
            js=[f'https://cdn.tiny.cloud/1/{api_key}/tinymce/6/tinymce.min.js']
        )

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        form.request = request
        return form

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        from django.conf import settings
        extra_context = extra_context or {}
        extra_context['tinymce_init'] = True
        extra_context['tinymce_api_key'] = getattr(settings, 'TINYMCE_API_KEY', 'no-api-key')
        return super().changeform_view(request, object_id, form_url, extra_context)


    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        # Set published_at when status flips from non-published to published
        if obj.status == 'published' and obj.published_at is None:
            from django.utils import timezone
            obj.published_at = timezone.now()
        super().save_model(request, obj, form, change)
