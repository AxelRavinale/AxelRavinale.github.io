from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import PermissionDenied
from django.utils.translation import gettext_lazy as _


class AdminRequiredMixin(UserPassesTestMixin):
    """Mixin para vistas que requieren permisos de administrador"""
    
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_superuser
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, _('Debe iniciar sesión para acceder a esta página'))
        else:
            messages.error(self.request, _('No tiene permisos para acceder a esta página'))
        return super().handle_no_permission()


class UserRequiredMixin(UserPassesTestMixin):
    """Mixin para vistas que requieren usuario normal (no admin)"""
    
    def test_func(self):
        return (self.request.user.is_authenticated and 
                not self.request.user.is_superuser)
    
    def handle_no_permission(self):
        if not self.request.user.is_authenticated:
            messages.error(self.request, _('Debe iniciar sesión para acceder a esta página'))
        else:
            # Si es admin, redirigir a panel admin
            if self.request.user.is_superuser:
                messages.info(self.request, _('Esta sección es solo para usuarios. Acceda al panel de administrador'))
                from django.shortcuts import redirect
                return redirect('reservas:admin_inicio')
            else:
                messages.error(self.request, _('No tiene permisos para acceder a esta página'))
        
        return super().handle_no_permission()

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