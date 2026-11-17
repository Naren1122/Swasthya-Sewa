import re
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError
from apps.accounts.models import User
from apps.accounts.validators import validate_email_domain, validate_password_complexity

class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for retrieving and updating user profile information.
    Exposes UUID, email, full name, phone, and role.
    """
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'email',
            'full_name',
            'phone',
            'role',
            'role_display',
            'created_at'
        ]
        read_only_fields = ['id', 'email', 'role', 'role_display', 'created_at']


class RegisterPatientSerializer(serializers.ModelSerializer):
    """
    Serializer for mobile / API client self-registration of Patients.
    Enforces password confirmation and automatic assignment of the PATIENT role.
    """
    password = serializers.CharField(write_only=True, min_length=8, style={'input_type': 'password'})
    password_confirm = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['id', 'email', 'full_name', 'phone', 'password', 'password_confirm']
        read_only_fields = ['id']

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        try:
            validate_email_domain(normalized_email)
        except DjangoValidationError as err:
            raise serializers.ValidationError(list(err.messages))

        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("An account with this email address already exists.")
        return normalized_email

    def validate_phone(self, value):
        phone = (value or '').strip()
        if not phone:
            raise serializers.ValidationError("Phone number is required.")

        clean_number = re.sub(r'[\s\-+]', '', phone)
        if clean_number.startswith('977'):
            clean_number = clean_number[3:]

        if not re.match(r'^9[78]\d{8}$', clean_number):
            raise serializers.ValidationError("Please enter a valid 10-digit Nepali mobile number (e.g., 98XXXXXXXX).")

        if User.objects.filter(phone=clean_number).exists():
            raise serializers.ValidationError("An account with this phone number already exists.")

        return clean_number

    def validate_password(self, value):
        try:
            validate_password_complexity(value)
        except DjangoValidationError as err:
            raise serializers.ValidationError(list(err.messages))
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        password = validated_data.pop('password')
        
        user = User.objects.create_user(
            role=User.Role.PATIENT,
            password=password,
            **validated_data
        )
        return user
