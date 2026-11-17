from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiResponse
from apps.accounts.api.serializers import UserProfileSerializer, RegisterPatientSerializer

@extend_schema(
    tags=['Authentication'],
    summary="Register a new patient",
    description="Public endpoint allowing new patients to self-register via REST API. Returns the created patient profile.",
    responses={
        201: OpenApiResponse(response=UserProfileSerializer, description="Patient registered successfully"),
        400: OpenApiResponse(description="Validation error (e.g. email exists or passwords mismatch)")
    }
)
class RegisterPatientAPIView(generics.CreateAPIView):
    """
    API endpoint for Patient self-registration.
    Public access (AllowAny).
    """
    serializer_class = RegisterPatientSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        profile_serializer = UserProfileSerializer(user)
        return Response(profile_serializer.data, status=status.HTTP_201_CREATED)


@extend_schema(
    tags=['Authentication'],
    summary="Get or update current authenticated user profile",
    description="Requires JWT Bearer token authentication. Returns the authenticated user's profile details.",
    responses={
        200: OpenApiResponse(response=UserProfileSerializer, description="Current user profile"),
        401: OpenApiResponse(description="Unauthorized - Invalid or missing token")
    }
)
class UserProfileAPIView(generics.RetrieveUpdateAPIView):
    """
    API endpoint to retrieve or update the currently authenticated user's profile.
    Requires Bearer Token authentication (IsAuthenticated).
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
