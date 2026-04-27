from django.contrib import admin
from .models import Course, CourseResource

class CourseResourceInline(admin.TabularInline):
    model = CourseResource
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'matiere', 'classe', 'creator', 'difficulty', 'created_at')
    list_filter = ('difficulty', 'matiere', 'classe')
    search_fields = ('title', 'description')
    inlines = [CourseResourceInline]

@admin.register(CourseResource)
class CourseResourceAdmin(admin.ModelAdmin):
    list_display = ('title', 'course', 'file_type', 'created_at')
    list_filter = ('file_type',)
