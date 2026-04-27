from django.contrib import admin
from .models import CalendarEvent, EventReminder, Attendance


@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_type', 'start_date', 'end_date', 'is_public', 'created_by')
    list_filter = ('event_type', 'color', 'is_public')
    search_fields = ('title', 'description', 'location')
    date_hierarchy = 'start_date'


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'reminded_at', 'is_read')
    list_filter = ('is_read',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('event', 'user', 'is_present', 'checked_at')
    list_filter = ('is_present',)
