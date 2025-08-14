from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class UserRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea un usuario normal (no admin)"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and not user.is_staff
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            # Usuario autenticado pero es staff
            raise PermissionDenied(_("Esta sección es solo para usuarios normales"))


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea administrador"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and (user.is_staff or user.is_superuser)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            # Usuario autenticado pero no es admin
            raise PermissionDenied(_("Esta sección es solo para administradores"))


class SuperUserRequiredMixin(UserPassesTestMixin):
    """Mixin que requiere que el usuario sea superusuario"""
    
    def test_func(self):
        user = self.request.user
        return user.is_authenticated and user.is_superuser
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            return super().handle_no_permission()
        else:
            # Usuario autenticado pero no es superuser
            raise PermissionDenied(_("Esta sección requiere permisos de superusuario"))