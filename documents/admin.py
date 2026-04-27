from django.contrib import admin
from .models import Document, DocumentComment


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'owner', 'category', 'file_size_display', 'download_count', 'is_public', 'created_at')
    list_filter = ('category', 'is_public', 'file_type')
    search_fields = ('title', 'description', 'owner__email')
    date_hierarchy = 'created_at'


@admin.register(DocumentComment)
class DocumentCommentAdmin(admin.ModelAdmin):
    list_display = ('document', 'user', 'content_short', 'created_at')
    search_fields = ('content', 'user__email')

    def content_short(self, obj):
        return obj.content[:50]
    content_short.short_description = 'Commentaire'
