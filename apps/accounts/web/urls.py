from django.urls import path
from apps.accounts.web.views import (
    PatientSignUpView,
    CustomLoginView,
    CustomLogoutView,
    RoleRedirectView
)

urlpatterns = [
    # Authentication Routes
    path('signup/', PatientSignUpView.as_view(), name='signup'),
    path('login/', CustomLoginView.as_view(), name='login'),
    path('logout/', CustomLogoutView.as_view(), name='logout'),
    
    # Post-Login Role-Based Redirection
    path('redirect/', RoleRedirectView.as_view(), name='role_redirect'),
]
