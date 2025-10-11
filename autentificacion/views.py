# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny

from .serializers import RegisterSerializer, LoginSerializer
from .services import AuthService

class RegisterAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = AuthService.register_user_api(serializer.validated_data)
            if user:
                return Response({"detail": "Registro exitoso."}, status=status.HTTP_201_CREATED)
            return Response({"detail": "Error al registrar usuario."}, status=status.HTTP_400_BAD_REQUEST)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user, token = AuthService.login_user_api(request, username, password)
            if user:
                return Response({
                    "detail": "Inicio de sesión exitoso.",
                    "user": {"id": user.id, "username": user.username},
                    "token": token
                }, status=status.HTTP_200_OK)
            return Response({"detail": "Usuario o contraseña incorrectos."}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutAPIView(APIView):
    def post(self, request):
        AuthService.logout_user_api(request)
        return Response({"detail": "Sesión cerrada correctamente."}, status=status.HTTP_200_OK)
