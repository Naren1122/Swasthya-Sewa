from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.conf import settings
from django.views import View
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, JsonResponse, HttpResponseForbidden
from django.utils import timezone

from apps.appointments.models import Appointment
from apps.appointments.services.booking_service import complete_appointment
from apps.telemed.models import MedicalDocument, ConsultationNote
from apps.telemed.services.room_service import TelemedRoomService

class TelemedRoomView(LoginRequiredMixin, View):
    """
    Main Teleconsultation Video Room interface.
    Enforces cryptographic participant authentication, timing windows,
    and displays split Jitsi Meet video + in-call clinical sidebar.
    """
    def get(self, request, appointment_id, *args, **kwargs):
        is_authorized, err_msg, appointment, context = TelemedRoomService.verify_telemed_access(
            user=request.user,
            appointment_id=appointment_id
        )

        if not is_authorized:
            messages.error(request, err_msg)
            if appointment and appointment.doctor and hasattr(appointment.doctor, 'slug'):
                return redirect('patient_bookings')
            return redirect('home')

        # Load existing medical documents and notes
        medical_docs = appointment.medical_documents.all().order_by('-created_at')
        consultation_note = getattr(appointment, 'consultation_note', None)

        context.update({
            'appointment': appointment,
            'medical_docs': medical_docs,
            'consultation_note': consultation_note,
            'document_types': MedicalDocument.DocumentType.choices,
            'jitsi_domain': getattr(settings, 'JITSI_DOMAIN', 'jitsi.riot.im'),
        })

        return render(request, 'telemed/room.html', context)


class DocumentUploadView(LoginRequiredMixin, View):
    """
    Handles pre-call and in-call upload and real-time retrieval of diagnostic reports (PDF, images).
    Supports HTMX asynchronous upload and polling.
    """
    def get(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'patient'),
            id=appointment_id
        )
        if request.user.id not in [appointment.patient.id, appointment.doctor.user.id]:
            return HttpResponseForbidden("You are not authorized to view documents for this consultation.")

        docs = appointment.medical_documents.all().order_by('-created_at')
        return render(request, 'telemed/partials/_documents_list.html', {
            'medical_docs': docs,
            'appointment': appointment,
        })

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'patient'),
            id=appointment_id
        )

        # Access check: Only the patient or the doctor can upload documents
        if request.user.id not in [appointment.patient.id, appointment.doctor.user.id]:
            return HttpResponseForbidden("You are not authorized to upload documents for this consultation.")

        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            messages.error(request, "Please choose a file to upload.")
            return redirect('telemed_room', appointment_id=appointment.id)

        # File size check (Max 10 MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            messages.error(request, "File size exceeds the 10 MB limit.")
            return redirect('telemed_room', appointment_id=appointment.id)

        title = request.POST.get('title', '').strip() or uploaded_file.name
        doc_type = request.POST.get('document_type', MedicalDocument.DocumentType.LAB_REPORT)
        notes = request.POST.get('notes', '').strip()

        doc = MedicalDocument.objects.create(
            appointment=appointment,
            patient=appointment.patient,
            title=title,
            document_type=doc_type,
            file=uploaded_file,
            file_size_bytes=uploaded_file.size,
            notes=notes
        )

        messages.success(request, f"Document '{doc.title}' uploaded successfully.")

        if request.headers.get('HX-Request'):
            # Return partial document list
            docs = appointment.medical_documents.all().order_by('-created_at')
            return render(request, 'telemed/partials/_documents_list.html', {
                'medical_docs': docs,
                'appointment': appointment,
            })

        return redirect('telemed_room', appointment_id=appointment.id)


class ConsultationNoteSaveView(LoginRequiredMixin, View):
    """
    Doctor endpoint to save clinical diagnosis, prescriptions, and advice.
    Also serves real-time prescription view to patient via GET.
    """
    def get(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'patient'),
            id=appointment_id
        )
        if request.user.id not in [appointment.patient.id, appointment.doctor.user.id]:
            return HttpResponseForbidden("You are not authorized to access clinical notes for this consultation.")

        note = getattr(appointment, 'consultation_note', None)
        is_doctor = (request.user.id == appointment.doctor.user.id)
        return render(request, 'telemed/partials/_notes_form.html', {
            'appointment': appointment,
            'consultation_note': note,
            'is_doctor': is_doctor,
        })

    def post(self, request, appointment_id, *args, **kwargs):
        appointment = get_object_or_404(
            Appointment.objects.select_related('doctor__user', 'patient'),
            id=appointment_id
        )

        # Only the assigned doctor can record clinical notes
        if request.user.id != appointment.doctor.user.id:
            return HttpResponseForbidden("Only the assigned doctor can author clinical consultation notes.")

        diagnosis = request.POST.get('diagnosis', '').strip()
        symptoms = request.POST.get('symptoms', '').strip()
        prescription = request.POST.get('prescription', '').strip()
        advice = request.POST.get('advice', '').strip()
        follow_up_date = request.POST.get('follow_up_date') or None
        is_finalize = request.POST.get('finalize') == 'true'

        note, _ = ConsultationNote.objects.get_or_create(
            appointment=appointment,
            defaults={'doctor': appointment.doctor}
        )

        note.diagnosis = diagnosis
        note.symptoms = symptoms
        note.prescription = prescription
        note.advice = advice
        if follow_up_date:
            note.follow_up_date = follow_up_date

        uploaded_prescription = request.FILES.get('prescription_file')
        if uploaded_prescription:
            note.prescription_file = uploaded_prescription

        if is_finalize:
            note.finalize()
            # Transition appointment to COMPLETED if active
            if appointment.status in [Appointment.Status.ACCEPTED, Appointment.Status.CONFIRMED]:
                complete_appointment(doctor_user=request.user, appointment_id=appointment.id)
            messages.success(request, "Consultation successfully completed and clinical summary finalized.")
        else:
            note.save()
            messages.success(request, "Clinical notes saved.")

        if request.headers.get('HX-Request'):
            return render(request, 'telemed/partials/_notes_form.html', {
                'appointment': appointment,
                'consultation_note': note,
                'is_doctor': True,
            })

        return redirect('telemed_room', appointment_id=appointment.id)
