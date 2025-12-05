"""
Media Manager Models
Centralized media file management
"""
from django.db import models
from django.core.validators import FileExtensionValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import BaseModel
from apps.accounts.models import CustomUser


class MediaFile(BaseModel):
    """
    Centralized media file storage
    """
    
    class MediaType(models.TextChoices):
        IMAGE = 'image', _('Image')
        VIDEO = 'video', _('Video')
        DOCUMENT = 'document', _('Document')
    
    uploader = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_media'
    )
    
    file = models.FileField('File', upload_to='media/%Y/%m/%d/')
    
    file_name = models.CharField('File Name', max_length=255)
    file_size = models.PositiveBigIntegerField('File Size (bytes)')
    mime_type = models.CharField('MIME Type', max_length=100)
    
    media_type = models.CharField(
        'Media Type',
        max_length=20,
        choices=MediaType.choices
    )
    
    # Image-specific fields
    width = models.PositiveIntegerField('Width', null=True, blank=True)
    height = models.PositiveIntegerField('Height', null=True, blank=True)
    
    # Video-specific fields
    duration = models.DurationField('Duration', null=True, blank=True)
    
    # Metadata
    title = models.CharField('Title', max_length=200, blank=True)
    description = models.TextField('Description', blank=True)
    alt_text = models.CharField('Alt Text', max_length=200, blank=True)
    
    # Usage tracking
    download_count = models.PositiveIntegerField('Download Count', default=0)
    
    class Meta:
        db_table = 'media_files'
        verbose_name = 'Media File'
        verbose_name_plural = 'Media Files'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['uploader', '-created_at']),
            models.Index(fields=['media_type']),
        ]
    
    def __str__(self):
        return self.file_name or str(self.file)


class MediaTag(models.Model):
    """
    Tags for organizing media files
    """
    name = models.CharField('Tag Name', max_length=50, unique=True)
    slug = models.SlugField('Slug', unique=True)
    
    media_files = models.ManyToManyField(
        MediaFile,
        related_name='tags',
        blank=True
    )
    
    class Meta:
        db_table = 'media_tags'
        verbose_name = 'Media Tag'
        verbose_name_plural = 'Media Tags'
        ordering = ['name']
    
    def __str__(self):
        return self.name
