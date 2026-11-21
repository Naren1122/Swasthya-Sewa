from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.accounts.web.views import PatientDashboardView

def home_view(request):
    return render(request, 'home.html')

urlpatterns = [
    # Admin Panel
    path('admin/', admin.site.urls),

    # Patient Dashboard
    path('patient/dashboard/', PatientDashboardView.as_view(), name='patient_dashboard'),

    # Custom Accounts Web App (Login, Signup, Role Redirect)
    path('accounts/', include('apps.accounts.web.urls')),

    # Allauth Accounts (Google OAuth & Social URLs)
    path('accounts/', include('allauth.urls')),

    # Domain REST API v1 Routes
    path('api/v1/auth/', include('apps.accounts.api.urls')),
    path('api/v1/', include('apps.doctors.api.urls')),
    path('api/v1/', include('apps.appointments.api.urls')),
    path('api/v1/', include('apps.payments.api.urls')),
    path('api/v1/', include('apps.telemed.api.urls')),

    # REST API Documentation (Swagger / OpenAPI)
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

    # Doctors Web App (Directory & Slot Picker)
    path('', include('apps.doctors.web.urls')),

    # Appointments Web App (Slot Hold, Checkout & Bookings)
    path('', include('apps.appointments.web.urls')),

    # Payments Web App (eSewa & Khalti Gateway Handlers)
    path('', include('apps.payments.web.urls')),

    # Telemedicine Web App (Jitsi Meet Video Room & Medical Records)
    path('', include('apps.telemed.web.urls')),

    # Home Landing Page
    path('', home_view, name='home'),
]

# Development Media & Static Serving
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
