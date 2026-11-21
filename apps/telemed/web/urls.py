from django.urls import path
from apps.telemed.web.views import (
    TelemedRoomView,
    DocumentUploadView,
    ConsultationNoteSaveView,
)

urlpatterns = [
    # Video Consultation Room (GET)
    path('appointments/<uuid:appointment_id>/video-room/', TelemedRoomView.as_view(), name='telemed_room'),

    # Document / Report Upload (POST)
    path('appointments/<uuid:appointment_id>/documents/upload/', DocumentUploadView.as_view(), name='telemed_document_upload'),

    # Doctor Clinical Note & Prescription Save / Finalize (POST)
    path('appointments/<uuid:appointment_id>/notes/save/', ConsultationNoteSaveView.as_view(), name='telemed_note_save'),
]
