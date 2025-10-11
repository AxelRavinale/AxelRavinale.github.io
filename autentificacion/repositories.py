from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class AuthRepository:

    @staticmethod
    def create_user(username, password):
        return User.objects.create_user(username=username, password=password)

    @staticmethod
    def get_user_by_username(username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            return None

    @staticmethod
    def authenticate_user(username, password):
        return authenticate(username=username, password=password)
