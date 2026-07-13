import csv
import io
import json

import qrcode
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import User, Course, Enrollment, Session, Attendance


# ---------- Authentication ----------

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('dashboard')
        messages.error(request, 'Invalid username or password.')
    return render(request, 'attendance/login.html')


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def register_view(request):
    """Public self-registration for students using their matric number."""
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        matric_no = request.POST.get('matric_no', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        department = request.POST.get('department', '').strip()
        level = request.POST.get('level', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        errors = []
        if not matric_no or not first_name or not last_name or not password:
            errors.append('Please fill in all required fields.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if len(password) < 6:
            errors.append('Password must be at least 6 characters.')
        if User.objects.filter(username=matric_no).exists():
            errors.append('An account with this matric number already exists.')

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, 'attendance/register.html', {
                'matric_no': matric_no, 'first_name': first_name,
                'last_name': last_name, 'department': department, 'level': level,
            })

        student = User.objects.create(
            username=matric_no,
            matric_no=matric_no,
            first_name=first_name,
            last_name=last_name,
            department=department,
            level=level,
            role=User.STUDENT,
        )
        student.set_password(password)
        student.save()
        auth_login(request, student)
        messages.success(request, 'Account created successfully. You can now enroll in your courses.')
        return redirect('dashboard')

    return render(request, 'attendance/register.html')


# ---------- Dashboard router ----------

@login_required
def dashboard(request):
    if request.user.is_lecturer():
        return lecturer_dashboard(request)
    return student_dashboard(request)


# ---------- Lecturer views ----------

@login_required
def lecturer_dashboard(request):
    if not request.user.is_lecturer():
        return redirect('dashboard')
    courses = Course.objects.filter(lecturer=request.user)
    return render(request, 'attendance/lecturer_dashboard.html', {'courses': courses})


@login_required
@require_POST
def add_course(request):
    """Lets a lecturer create a new course, auto-linked to themselves.
    Also updates the lecturer's display name if provided, since some
    accounts (e.g. seeded via admin) may not have a name set yet."""
    if not request.user.is_lecturer():
        return redirect('dashboard')

    course_code = request.POST.get('course_code', '').strip().upper()
    title = request.POST.get('title', '').strip()
    department = request.POST.get('department', '').strip()
    lecturer_name = request.POST.get('lecturer_name', '').strip()

    if not course_code or not title:
        messages.error(request, 'Course code and title are required.')
        return redirect('dashboard')

    if Course.objects.filter(course_code=course_code).exists():
        messages.error(request, f'A course with code {course_code} already exists.')
        return redirect('dashboard')

    if lecturer_name:
        parts = lecturer_name.split(' ', 1)
        request.user.first_name = parts[0]
        request.user.last_name = parts[1] if len(parts) > 1 else ''
        request.user.save()

    Course.objects.create(
        course_code=course_code,
        title=title,
        department=department or request.user.department,
        lecturer=request.user,
    )
    messages.success(request, f'{course_code} — {title} created successfully.')
    return redirect('dashboard')


@login_required
def start_session(request, course_id):
    if not request.user.is_lecturer():
        return redirect('dashboard')
    course = get_object_or_404(Course, id=course_id, lecturer=request.user)

    venue = request.POST.get('venue', '') if request.method == 'POST' else ''
    session = Session.objects.create(course=course, venue=venue)
    return redirect('session_qr', session_id=session.id)


@login_required
def session_qr(request, session_id):
    session = get_object_or_404(Session, id=session_id, course__lecturer=request.user)
    return render(request, 'attendance/session_qr.html', {'session': session})


@login_required
def qr_image(request, session_id):
    """Generates and returns the QR code PNG for a session on the fly."""
    session = get_object_or_404(Session, id=session_id, course__lecturer=request.user)

    img = qrcode.make(session.qr_token)
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


@login_required
def session_status(request, session_id):
    """Polled by the lecturer's QR page to show live attendance count."""
    session = get_object_or_404(Session, id=session_id, course__lecturer=request.user)
    count = session.attendance_records.count()
    return JsonResponse({
        'count': count,
        'expired': session.is_expired,
        'expires_at': session.expires_at.isoformat(),
    })


@login_required
def session_detail(request, session_id):
    session = get_object_or_404(Session, id=session_id, course__lecturer=request.user)
    records = session.attendance_records.select_related('student').order_by('student__last_name')
    return render(request, 'attendance/session_detail.html', {'session': session, 'records': records})


@login_required
def export_attendance_csv(request, session_id):
    session = get_object_or_404(Session, id=session_id, course__lecturer=request.user)
    records = session.attendance_records.select_related('student').order_by('student__last_name')

    response = HttpResponse(content_type='text/csv')
    filename = f"{session.course.course_code}_{session.created_at:%Y%m%d_%H%M}.csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    writer = csv.writer(response)
    writer.writerow(['Matric No', 'Name', 'Timestamp', 'Status'])
    for record in records:
        writer.writerow([
            record.student.matric_no,
            record.student.get_full_name(),
            record.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            record.status,
        ])
    return response


# ---------- Student views ----------

@login_required
def student_dashboard(request):
    if not request.user.is_student():
        return redirect('dashboard')
    enrollments = Enrollment.objects.filter(student=request.user).select_related('course')
    enrolled_course_ids = enrollments.values_list('course_id', flat=True)
    available_courses = Course.objects.exclude(id__in=enrolled_course_ids).select_related('lecturer')
    recent_attendance = Attendance.objects.filter(student=request.user).select_related(
        'session__course'
    ).order_by('-timestamp')[:10]
    return render(request, 'attendance/student_dashboard.html', {
        'enrollments': enrollments,
        'available_courses': available_courses,
        'recent_attendance': recent_attendance,
    })


@login_required
@require_POST
def enroll_course(request, course_id):
    """Lets a student self-enroll into a course."""
    if not request.user.is_student():
        return redirect('dashboard')
    course = get_object_or_404(Course, id=course_id)
    Enrollment.objects.get_or_create(student=request.user, course=course)
    messages.success(request, f'You are now registered for {course.course_code}.')
    return redirect('dashboard')


@login_required
def scan_page(request):
    if not request.user.is_student():
        return redirect('dashboard')
    return render(request, 'attendance/scan.html')


@login_required
@require_POST
def mark_attendance(request):
    """
    Called via AJAX from the scan page once the browser's camera has
    decoded a QR token. Validates the token and records attendance.
    """
    if not request.user.is_student():
        return JsonResponse({'ok': False, 'error': 'Only students can mark attendance.'}, status=403)

    try:
        payload = json.loads(request.body)
    except (ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'Invalid request.'}, status=400)

    token = payload.get('token', '').strip()
    gps = payload.get('gps', '')

    session = Session.objects.filter(qr_token=token).select_related('course').first()
    if session is None:
        return JsonResponse({'ok': False, 'error': 'Invalid QR code.'}, status=404)

    if session.is_expired:
        return JsonResponse({'ok': False, 'error': 'This QR code has expired. Ask your lecturer to generate a new one.'}, status=410)

    enrolled = Enrollment.objects.filter(student=request.user, course=session.course).exists()
    if not enrolled:
        return JsonResponse({'ok': False, 'error': f'You are not registered for {session.course.course_code}.'}, status=403)

    already_marked = Attendance.objects.filter(student=request.user, session=session).exists()
    if already_marked:
        return JsonResponse({'ok': False, 'error': 'Attendance already recorded for this session.'}, status=409)

    Attendance.objects.create(
        student=request.user,
        session=session,
        gps_coordinates=gps,
    )
    return JsonResponse({
        'ok': True,
        'message': f'Attendance marked for {session.course.course_code} at {timezone.localtime(timezone.now()):%H:%M}.',
    })
