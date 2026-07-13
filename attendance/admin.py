from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Course, Enrollment, Session, Attendance


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Attendance System Fields', {
            'fields': ('role', 'matric_no', 'staff_id', 'department', 'level')
        }),
    )
    list_display = ('username', 'first_name', 'last_name', 'role', 'matric_no', 'staff_id')
    list_filter = ('role', 'department')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'title', 'lecturer', 'department')
    search_fields = ('course_code', 'title')


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'academic_session')
    list_filter = ('course', 'academic_session')


@admin.register(Session)
class SessionAdmin(admin.ModelAdmin):
    list_display = ('course', 'created_at', 'expires_at', 'venue')
    list_filter = ('course',)


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'session', 'timestamp', 'status')
    list_filter = ('session__course', 'status')
