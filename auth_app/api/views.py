from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from auth_app.api.serializers import LoginSerializer, RegistrationSerializer


def build_auth_response(user):
    """Return the payload the frontend expects after authentication."""
    token, _ = Token.objects.get_or_create(user=user)
    return {
        'token': token.key,
        'fullname': user.fullname,
        'email': user.email,
        'user_id': user.id,
    }


class RegistrationView(APIView):
    """POST /api/registration/ creates an account and returns a token."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Register a new user."""
        serializer = RegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            build_auth_response(user),
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    """POST /api/login/ returns a token for valid credentials."""

    permission_classes = [AllowAny]

    def post(self, request):
        """Log an existing user in."""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = self.find_user(request, serializer.validated_data)
        if user is None:
            return Response(
                {'detail': 'Invalid email or password.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(build_auth_response(user))

    def find_user(self, request, credentials):
        """Return the user behind the credentials, or None."""
        return authenticate(
            request,
            username=credentials['email'],
            password=credentials['password'],
        )
