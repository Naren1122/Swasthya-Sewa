from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from apps.accounts.api.views import RegisterPatientAPIView, UserProfileAPIView

urlpatterns = [
    # JWT Token Issuance & Refresh
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # Patient Registration & Current Profile
    path('register/', RegisterPatientAPIView.as_view(), name='api_register_patient'),
    path('me/', UserProfileAPIView.as_view(), name='api_user_profile'),
]
