from django.conf import settings
from django.core.mail import send_mail
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils.timezone import localdate
from collections import defaultdict
from django.contrib.auth.hashers import check_password
from functools import wraps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.urls import reverse
import json
import uuid

from .forms import (
    PersonalDetailsForm,
    AppointmentDetailsForm,
    ReceptionistRegisterForm,
    ReceptionistLoginForm,
    RescheduleForm,
)
from .models import Entry, ReceptionistUserAuth

def receptionist_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('receptionist_id'):
            return redirect('receptionist_login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def admin_login_required(view_func):
    @wraps(view_func)
    def _wrapped(request, *args, **kwargs):
        if not request.session.get('is_admin'):
            return redirect('admin_login')
        return view_func(request, *args, **kwargs)
    return _wrapped

def send_status_email(entry, status):
    """Send email based on appointment status"""
    base_url = getattr(settings, 'BASE_URL', 'http://localhost:8000')
    
    if status == 'approved':
        subject = "Appointment Approved - Confirmation"
        message = f"""
Dear {entry.name},

Great news! Your appointment has been APPROVED.

Appointment Details:
- Date: {entry.appointment_date}
- Time: {entry.appointment_time}
- Category: {entry.get_category_display()}
- Attendee: {entry.get_designated_attendee_display()}

Please arrive 15 minutes before your scheduled time.

If you need to make any changes, please contact us immediately.

Best regards,
Appointment Management Team
        """.strip()
        
    elif status == 'rejected':
        subject = "Appointment Status Update - Alternative Options Available"
        message = f"""
Dear {entry.name},

We regret to inform you that your appointment scheduled for {entry.appointment_date} at {entry.appointment_time} is not available due to scheduling conflicts.

However, we would be happy to help you reschedule at a more convenient time.

To reschedule your appointment, please visit: {base_url}/reschedule/{entry.reschedule_token}/

Alternatively, you can book a new appointment at: {base_url}/

We apologize for any inconvenience and look forward to serving you soon.

Best regards,
Appointment Management Team
        """.strip()
        
    elif status == 'rescheduled':
        subject = "Reschedule Required - Please Select New Time"
        message = f"""
Dear {entry.name},

Your appointment scheduled for {entry.appointment_date} at {entry.appointment_time} needs to be rescheduled due to unforeseen circumstances.

To select a new appointment time, please visit: {base_url}/reschedule/{entry.reschedule_token}/

Your appointment details:
- Original Date: {entry.appointment_date}
- Original Time: {entry.appointment_time}
- Category: {entry.get_category_display()}
- Reason: {entry.reason}

Please reschedule within 7 days to secure your appointment.

We apologize for the inconvenience.

Best regards,
Appointment Management Team
        """.strip()
    
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', None),
            [entry.email],
            fail_silently=False
        )
        return True
    except Exception as e:
        print(f"Email sending failed: {e}")
        return False

def step1(request):
    if request.method == 'POST':
        form = PersonalDetailsForm(request.POST)
        if form.is_valid():
            request.session['step1'] = form.cleaned_data
            return redirect('step2')
    else:
        initial = request.session.get('step1')
        form = PersonalDetailsForm(initial=initial)
    return render(request, 'step1.html', {'form': form})

def step2(request):
    step1_data = request.session.get('step1')
    if not step1_data:
        return redirect('step1')

    if request.method == 'POST':
        form = AppointmentDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            entry = form.save(commit=False)
            entry.name = step1_data['name']
            entry.email = step1_data['email']
            entry.phone = step1_data['phone']
            entry.category = step1_data['category']
            # Generate reschedule token
            entry.reschedule_token = str(uuid.uuid4())
            entry.save()

            subject_user = "Appointment Scheduled Successfully"
            message_user = (
                f"Hello {entry.name},\n\n"
                f"Your appointment has been scheduled and is pending review.\n"
                f"Date: {entry.appointment_date}\n"
                f"Time: {entry.appointment_time}\n\n"
                f"You will receive a confirmation email once your appointment is approved.\n\n"
                f"Thank you!"
            )
            send_mail(subject_user, message_user,
                      getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                      [entry.email], fail_silently=True)

            subject_admin = "New Appointment Booking Notification"
            message_admin = (
                f"New appointment booked by {entry.name}\n"
                f"Date: {entry.appointment_date}\n"
                f"Time: {entry.appointment_time}\n"
                f"Category: {entry.category}\n"
                f"Phone: {entry.phone}\n"
                f"Email: {entry.email}"
            )
            send_mail(subject_admin, message_admin,
                      getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                      ['dharshanjiju001@gmail.com'], fail_silently=True)

            request.session.pop('step1', None)
            return redirect('success')
    else:
        form = AppointmentDetailsForm()

    return render(request, 'step2.html', {'form': form})

def success(request):
    return render(request, 'success.html')

def receptionist_register(request):
    if request.method == "POST":
        form = ReceptionistRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Registered! Wait for admin approval before logging in.")
            return redirect('receptionist_login')
    else:
        form = ReceptionistRegisterForm()
    return render(request, 'receptionist_register.html', {'form': form})

def receptionist_login(request):
    if request.method == "POST":
        form = ReceptionistLoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']

            try:
                rec = ReceptionistUserAuth.objects.get(username=username)
            except ReceptionistUserAuth.DoesNotExist:
                messages.error(request, "Username not found.")
                return redirect('receptionist_login')

            if not rec.is_approved:
                messages.error(request, "Your account is not approved yet. Please contact admin.")
                return redirect('receptionist_login')

            if check_password(password, rec.password):
                request.session['receptionist_id'] = rec.id
                request.session['receptionist_username'] = rec.username
                return redirect('dashboard')
            else:
                messages.error(request, "Invalid password.")
                return redirect('receptionist_login')
    else:
        form = ReceptionistLoginForm()
    return render(request, 'receptionist_login.html', {'form': form})

def receptionist_logout(request):
    request.session.flush()
    return redirect('receptionist_login')

@receptionist_login_required
def dashboard(request):
    entries = Entry.objects.all().order_by('appointment_date', 'appointment_time')
    grouped_entries = defaultdict(list)
    for entry in entries:
        grouped_entries[entry.appointment_date].append(entry)
    grouped_entries = dict(sorted(grouped_entries.items(), key=lambda x: x[0]))
    today = localdate()

    return render(request, 'dashboard.html', {
        'grouped_entries': grouped_entries,
        'today': today,
        'receptionist_username': request.session.get('receptionist_username')
    })

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        if username == "admin" and password == "admin123":
            request.session["is_admin"] = True
            return redirect("approval_page")
        else:
            messages.error(request, "Invalid admin credentials.")
            return redirect("admin_login")
    return render(request, "admin_login.html")

def admin_logout(request):
    request.session.flush()
    return redirect("admin_login")

@admin_login_required
def approval_page(request):
    receptionists = ReceptionistUserAuth.objects.all().order_by("-created_at")
    return render(request, "approval_page.html", {"receptionists": receptionists})

@admin_login_required
def approve_receptionist(request, pk):
    receptionist = get_object_or_404(ReceptionistUserAuth, pk=pk)
    receptionist.is_approved = True
    receptionist.save()
    messages.success(request, f"{receptionist.username} approved successfully ✅")
    return redirect("approval_page")

@admin_login_required
def reject_receptionist(request, pk):
    receptionist = get_object_or_404(ReceptionistUserAuth, pk=pk)
    receptionist.delete()
    messages.error(request, f"{receptionist.username} rejected ❌")
    return redirect("approval_page")

@csrf_exempt
@require_GET
def get_appointments(request):
    entries = Entry.objects.all().order_by('appointment_date', 'appointment_time')
    
    appointments_data = []
    for entry in entries:
        appointments_data.append({
            'id': entry.id,
            'date': entry.appointment_date.strftime('%Y-%m-%d'),
            'time': entry.appointment_time.strftime('%I:%M %p'),
            'name': entry.name,
            'email': entry.email,
            'phone': entry.phone,
            'category': entry.category,
            'reason': entry.reason,
            'status': entry.status,
            'document_url': entry.document.url if entry.document else None,
            'designated_attendee': entry.designated_attendee,
        })
    
    return JsonResponse({'appointments': appointments_data}, safe=False)

@csrf_exempt
@require_POST
def update_appointment_status(request):
    try:
        data = json.loads(request.body)
        appointment_id = data.get('id')
        new_status = data.get('status')
        
        appointment = Entry.objects.get(id=appointment_id)
        old_status = appointment.status
        appointment.status = new_status
        appointment.save()
        
        # Send email notification only if status actually changed
        if old_status != new_status:
            email_sent = send_status_email(appointment, new_status)
            if email_sent:
                return JsonResponse({'success': True, 'message': 'Status updated and email sent'})
            else:
                return JsonResponse({'success': True, 'message': 'Status updated but email failed'})
        
        return JsonResponse({'success': True, 'message': 'Status updated'})
        
    except Entry.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

def reschedule_appointment(request, token):
    """Handle appointment rescheduling"""
    try:
        appointment = Entry.objects.get(reschedule_token=token)
    except Entry.DoesNotExist:
        messages.error(request, "Invalid or expired reschedule link.")
        return redirect('step1')
    
    if request.method == 'POST':
        form = RescheduleForm(request.POST)
        if form.is_valid():
            # Update appointment with new details
            appointment.appointment_date = form.cleaned_data['appointment_date']
            appointment.appointment_time = form.cleaned_data['appointment_time']
            appointment.designated_attendee = form.cleaned_data['designated_attendee']
            appointment.status = 'pending'  # Reset to pending for approval
            
            # Update reason if provided
            if form.cleaned_data.get('reason'):
                appointment.reason = form.cleaned_data['reason']
            
            appointment.save()
            
            # Send confirmation email
            subject = "Appointment Rescheduled Successfully"
            message = f"""
Dear {appointment.name},

Your appointment has been successfully rescheduled.

New Appointment Details:
- Date: {appointment.appointment_date}
- Time: {appointment.appointment_time}
- Category: {appointment.get_category_display()}
- Attendee: {appointment.get_designated_attendee_display()}

Your appointment is now pending approval. You will receive a confirmation email once approved.

Thank you for using our service.

Best regards,
Appointment Management Team
            """.strip()
            
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                [appointment.email],
                fail_silently=True
            )
            
            # Notify admin
            admin_subject = "Appointment Rescheduled - Needs Approval"
            admin_message = f"""
Appointment rescheduled by {appointment.name}

New Details:
- Date: {appointment.appointment_date}
- Time: {appointment.appointment_time}
- Category: {appointment.category}
- Phone: {appointment.phone}
- Email: {appointment.email}
- Reason: {appointment.reason}

Please review and approve.
            """.strip()
            
            send_mail(
                admin_subject,
                admin_message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', None),
                ['dharshanjiju001@gmail.com'],
                fail_silently=True
            )
            
            return render(request, 'reschedule_success.html', {'appointment': appointment})
    else:
        # Pre-populate form with existing appointment data
        initial_data = {
            'appointment_date': appointment.appointment_date,
            'appointment_time': appointment.appointment_time,
            'designated_attendee': appointment.designated_attendee,
            'reason': appointment.reason,
        }
        form = RescheduleForm(initial=initial_data)
    
    return render(request, 'reschedule.html', {
        'form': form,
        'appointment': appointment
    })