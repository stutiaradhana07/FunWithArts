import os
from django import forms
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.html import format_html
from django.utils.safestring import mark_safe


class AdminImagePreviewWidget(AdminFileWidget):
    """
    Enhanced image upload widget for Django Admin.
    Renders an elegant thumbnail preview card (approx 120px) while maintaining
    full compatibility with Django's ClearableFileInput, Cloudinary URLs,
    and the existing focal_point_picker.js DOM queries.
    """

    def render(self, name, value, attrs=None, renderer=None):
        preview_html = ''
        if value and hasattr(value, 'url'):
            url = value.url
            filename = os.path.basename(getattr(value, 'name', '')) or 'image'
            preview_html = format_html(
                '<div class="admin-media-preview-card">'
                '  <a href="{0}" target="_blank" rel="noopener noreferrer" class="admin-preview-anchor" title="View full size image">'
                '    <img src="{0}" alt="{1}" class="admin-preview-image" />'
                '  </a>'
                '  <div class="admin-preview-meta">'
                '    <span class="admin-preview-filename" title="{1}">{1}</span>'
                '    <a href="{0}" target="_blank" rel="noopener noreferrer" class="admin-preview-zoom-btn">↗ View Full Size</a>'
                '  </div>'
                '</div>',
                url,
                filename
            )

        # Base file widget HTML (includes standard file input and clear checkbox)
        base_html = super().render(name, value, attrs, renderer)
        
        return mark_safe(f'<div class="admin-image-widget-wrapper">{preview_html}{base_html}</div>')


class AdminVideoPreviewWidget(AdminFileWidget):
    """
    Enhanced video upload widget for Django Admin.
    Renders a compact HTML5 video preview player for uploaded videos.
    """

    def render(self, name, value, attrs=None, renderer=None):
        preview_html = ''
        if value and hasattr(value, 'url'):
            url = value.url
            filename = os.path.basename(getattr(value, 'name', '')) or 'video'
            preview_html = format_html(
                '<div class="admin-media-preview-card video-card">'
                '  <video src="{0}" controls preload="metadata" class="admin-preview-video">'
                '    Your browser does not support the video tag.'
                '  </video>'
                '  <div class="admin-preview-meta">'
                '    <span class="admin-preview-filename" title="{1}">{1}</span>'
                '    <a href="{0}" target="_blank" rel="noopener noreferrer" class="admin-preview-zoom-btn">↗ Open Video</a>'
                '  </div>'
                '</div>',
                url,
                filename
            )

        base_html = super().render(name, value, attrs, renderer)
        return mark_safe(f'<div class="admin-video-widget-wrapper">{preview_html}{base_html}</div>')
