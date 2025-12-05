"""
Media Manager Admin Configuration
"""
from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from .models import MediaFile, MediaTag


@admin.register(MediaFile)
class MediaFileAdmin(admin.ModelAdmin):
    list_display = [
        'file_preview',
        'file_name',
        'media_type',
        'file_size_display',
        'uploader_email',
        'download_count',
        'created_at'
    ]
    
    list_filter = ['media_type', 'created_at']
    search_fields = ['file_name', 'title', 'description', 'uploader__email']
    
    readonly_fields = [
        'uploader',
        'file_size',
        'mime_type',
        'width',
        'height',
        'duration',
        'download_count',
        'created_at',
        'updated_at',
        'file_preview_large'
    ]
    
    fieldsets = (
        ('File Info', {
            'fields': (
                'uploader',
                'file',
                'file_preview_large',
                'file_name',
                'media_type'
            )
        }),
        ('Metadata', {
            'fields': (
                'title',
                'description',
                'alt_text'
            )
        }),
        ('Technical Details', {
            'fields': (
                'file_size',
                'mime_type',
                'width',
                'height',
                'duration'
            )
        }),
        ('Statistics', {
            'fields': ('download_count',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        })
    )
    
    def file_preview(self, obj):
        if obj.media_type == MediaFile.MediaType.IMAGE:
            return mark_safe(f'<img src="{obj.file.url}" style="max-height: 50px;" />')
        return obj.file_name
    file_preview.short_description = 'Preview'
    
    def file_preview_large(self, obj):
        if obj.media_type == MediaFile.MediaType.IMAGE:
            return mark_safe(f'<img src="{obj.file.url}" style="max-width: 500px;" />')
        return '-'
    file_preview_large.short_description = 'Preview'
    
    def file_size_display(self, obj):
        size_kb = obj.file_size / 1024
        if size_kb < 1024:
            return f"{size_kb:.2f} KB"
        return f"{size_kb / 1024:.2f} MB"
    file_size_display.short_description = 'Size'
    
    def uploader_email(self, obj):
        if obj.uploader:
            url = reverse('admin:accounts_customuser_change', args=[obj.uploader.id])
            return format_html('<a href="{}">{}</a>', url, obj.uploader.email)
        return '-'
    uploader_email.short_description = 'Uploader'


@admin.register(MediaTag)
class MediaTagAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'media_count']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    
    def media_count(self, obj):
        return obj.media_files.count()
    media_count.short_description = 'Files'
