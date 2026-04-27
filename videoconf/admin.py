from django.contrib import admin
from .models import MeetingRoom, RoomParticipant, RoomMessage


@admin.register(MeetingRoom)
class MeetingRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'created_by', 'status', 'is_public', 'is_active', 'participant_count_display', 'created_at')
    list_filter = ('status', 'is_public', 'is_active')
    search_fields = ('name', 'description', 'created_by__email', 'created_by__first_name')
    readonly_fields = ('id', 'created_at', 'started_at', 'ended_at')
    date_hierarchy = 'created_at'

    def participant_count_display(self, obj):
        return obj.participant_count
    participant_count_display.short_description = 'Participants'


@admin.register(RoomParticipant)
class RoomParticipantAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'role', 'status', 'joined_at', 'left_at')
    list_filter = ('role', 'status')
    search_fields = ('user__email', 'user__first_name', 'room__name')
    readonly_fields = ('id', 'joined_at')


@admin.register(RoomMessage)
class RoomMessageAdmin(admin.ModelAdmin):
    list_display = ('user', 'room', 'content_short', 'created_at', 'is_system_message')
    list_filter = ('is_system_message',)
    search_fields = ('content', 'user__email', 'room__name')
    readonly_fields = ('id', 'created_at')

    def content_short(self, obj):
        return obj.content[:80]
    content_short.short_description = 'Message'
