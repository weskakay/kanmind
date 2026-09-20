from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework.validators import UniqueValidator

from auth_app.models import User


class LowercaseEmailField(serializers.EmailField):
    """Email field that keeps addresses in lower case."""

    def to_internal_value(self, data):
        """Normalize the address before any validator sees it."""
        return super().to_internal_value(data).lower()


class RegistrationSerializer(serializers.ModelSerializer):
    """Validates the signup payload and creates a new user."""

    email = LowercaseEmailField(
        validators=[UniqueValidator(queryset=User.objects.all())],
    )
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
    )
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']

    def validate(self, attrs):
        """Reject a signup where both passwords differ."""
        if attrs['password'] != attrs['repeated_password']:
            raise serializers.ValidationError(
                {'repeated_password': 'Passwords do not match.'}
            )
        return attrs

    def create(self, validated_data):
        """Create the user with a hashed password."""
        validated_data.pop('repeated_password')
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    """Validates the login payload."""

    email = LowercaseEmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    """Public representation of a user."""

    class Meta:
        model = User
        fields = ['id', 'email', 'fullname']
