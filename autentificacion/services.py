from django.contrib.auth import login, logout
from rest_framework.authtoken.models import Token
from .repositories import AuthRepository


class AuthService:

    @staticmethod
    def register_user_api(data):
        username = data.get('username')
        password = data.get('password')

        if AuthRepository.get_user_by_username(username):
            return None  # Usuario ya existe

        user = AuthRepository.create_user(username, password)
        Token.objects.get_or_create(user=user)
        return user

    @staticmethod
    def login_user_api(request, username, password):
        user = AuthRepository.authenticate_user(username, password)
        if user:
            login(request, user)
            token, _ = Token.objects.get_or_create(user=user)
            return user, token.key
        return None, None

    @staticmethod
    def logout_user_api(request):
        user = request.user
        if user.is_authenticated:
            Token.objects.filter(user=user).delete()
            logout(request)
