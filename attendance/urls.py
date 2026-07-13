from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('register/', views.register_view, name='register'),

    # Lecturer
    path('course/add/', views.add_course, name='add_course'),
    path('course/<int:course_id>/start-session/', views.start_session, name='start_session'),
    path('session/<int:session_id>/qr/', views.session_qr, name='session_qr'),
    path('session/<int:session_id>/qr-image/', views.qr_image, name='qr_image'),
    path('session/<int:session_id>/status/', views.session_status, name='session_status'),
    path('session/<int:session_id>/', views.session_detail, name='session_detail'),
    path('session/<int:session_id>/export/', views.export_attendance_csv, name='export_attendance_csv'),

    # Student
    path('course/<int:course_id>/enroll/', views.enroll_course, name='enroll_course'),
    path('scan/', views.scan_page, name='scan_page'),
    path('mark-attendance/', views.mark_attendance, name='mark_attendance'),
]
