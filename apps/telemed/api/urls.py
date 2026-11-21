from django.urls import path
from apps.telemed.api.views import (
    TelemedRoomAccessAPIView,
    MedicalDocumentListCreateAPIView,
    ConsultationNoteAPIView,
)

urlpatterns = [
    # Room Access & Participant Credentials (GET)
    path('telemed/appointments/<uuid:appointment_id>/room-access/', TelemedRoomAccessAPIView.as_view(), name='api_telemed_room_access'),

    # Medical Documents Upload & List (GET, POST)
    path('telemed/appointments/<uuid:appointment_id>/documents/', MedicalDocumentListCreateAPIView.as_view(), name='api_telemed_documents'),

    # Clinical Notes & Prescriptions (GET, POST)
    path('telemed/appointments/<uuid:appointment_id>/notes/', ConsultationNoteAPIView.as_view(), name='api_telemed_notes'),
]
