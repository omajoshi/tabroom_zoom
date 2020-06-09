from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext, gettext_lazy as _


from .models import *

admin.site.register(Tournament)
admin.site.register(Event)
admin.site.register(Team)
admin.site.register(Round)
admin.site.register(Room)
admin.site.register(Pairing)
admin.site.register(BreakoutRoom)
admin.site.register(Person)
admin.site.register(School)

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'tabroom_email', 'zoom_email', 'password', 'email_confirmed', 'zoom_confirmed', 'tabroom_confirmed')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'tabroom_email', 'zoom_email', 'password1', 'password2', 'email_confirmed', 'zoom_confirmed', 'tabroom_confirmed'),
        }),
    )
    list_display = ('email', 'tabroom_email', 'zoom_email', 'first_name', 'last_name', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')
    search_fields = ('email', 'tabroom_email', 'zoom_email', 'first_name', 'last_name')
    ordering = ('email',)
    filter_horizontal = ('groups', 'user_permissions',)

# Register your models here.
