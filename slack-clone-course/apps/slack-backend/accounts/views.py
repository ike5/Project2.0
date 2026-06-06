"""Auth endpoints: register, login, refresh, logout, and "who am I"."""
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .serializers import EmailTokenObtainSerializer, RegisterSerializer, UserSerializer


class RegisterView(generics.CreateAPIView):
    """Open endpoint to create an account."""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class LoginView(TokenObtainPairView):
    """Exchange email + password for an access + refresh token pair."""
    serializer_class = EmailTokenObtainSerializer
    permission_classes = [permissions.AllowAny]


class LogoutView(APIView):
    """Blacklist the supplied refresh token so it can't mint new access tokens."""

    def post(self, request):
        try:
            RefreshToken(request.data["refresh"]).blacklist()
        except (KeyError, TokenError):
            return Response({"detail": "Invalid or missing refresh token."},
                            status=status.HTTP_400_BAD_REQUEST)
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    """Read or update the authenticated user's own profile."""
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user
