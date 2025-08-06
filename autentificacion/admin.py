from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from core.models import Persona

class PersonaInline(admin.StackedInline):
    model = Persona
    can_delete = False
    verbose_name_plural = 'Persona'

class UserAdmin(BaseUserAdmin):
    inlines = (PersonaInline,)

admin.site.unregister(User)
admin.site.register(User, UserAdmin)
