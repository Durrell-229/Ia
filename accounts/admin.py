from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User, Profile


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = _('Profil')


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'full_name', 'role', 'matricule', 'country', 'is_active', 'date_joined']
    list_filter = ['role', 'is_active', 'is_staff', 'niveau', 'country']
    search_fields = ['email', 'first_name', 'last_name', 'matricule']
    ordering = ['-date_joined']
    inlines = [ProfileInline]

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('Informations personnelles'), {'fields': ('first_name', 'last_name', 'phone', 'country', 'avatar', 'bio')}),
        (_('Rôle & Scolarité'), {'fields': ('role', 'niveau', 'classe', 'matricule')}),
        (_('Préférences'), {'fields': ('preferred_language', 'dark_mode')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'date_joined', 'last_login_ip')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'first_name', 'last_name', 'role', 'password1', 'password2'),
        }),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'school', 'total_points', 'completed_exams', 'average_score', 'rank']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
