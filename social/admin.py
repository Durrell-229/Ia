from django.contrib import admin
from .models import Forum, Topic, Post, StudyGroup, Like


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ('name', 'topic_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('title', 'forum', 'author', 'is_pinned', 'views', 'post_count', 'created_at')
    list_filter = ('is_pinned', 'is_active', 'forum')
    search_fields = ('title', 'content')


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'topic', 'created_at', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('content', 'author__email')


@admin.register(StudyGroup)
class StudyGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'creator', 'member_count', 'is_private', 'max_members', 'created_at')
    list_filter = ('is_private',)
    search_fields = ('name', 'description')


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    list_display = ('user', 'content_type', 'content_id', 'created_at')
    list_filter = ('content_type',)
