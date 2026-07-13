from django.core.management.base import BaseCommand
from attendance.models import User, Course, Enrollment


class Command(BaseCommand):
    help = "Creates demo lecturer, students, a course and enrollments for testing."

    def handle(self, *args, **options):
        # Admin
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin12345')
            self.stdout.write(self.style.SUCCESS('Created superuser: admin / admin12345'))

        # Lecturer
        lecturer, created = User.objects.get_or_create(
            username='LEC001',
            defaults=dict(
                first_name='Ngozi', last_name='Eze', role=User.LECTURER,
                staff_id='LEC001', department='Computer Science',
            )
        )
        if created:
            lecturer.set_password('lecturer123')
            lecturer.save()
            self.stdout.write(self.style.SUCCESS('Created lecturer: LEC001 / lecturer123'))

        # Course
        course, _ = Course.objects.get_or_create(
            course_code='CSC401',
            defaults=dict(title='Software Engineering', lecturer=lecturer, department='Computer Science'),
        )

        # Students
        students_data = [
            ('AIFCE/CSC/21/001', 'Chidi', 'Okafor'),
            ('AIFCE/CSC/21/002', 'Amaka', 'Nwosu'),
            ('AIFCE/CSC/21/003', 'Emeka', 'Obi'),
        ]
        for matric, first, last in students_data:
            student, created = User.objects.get_or_create(
                username=matric,
                defaults=dict(
                    first_name=first, last_name=last, role=User.STUDENT,
                    matric_no=matric, department='Computer Science', level='400',
                )
            )
            if created:
                student.set_password('student123')
                student.save()
            Enrollment.objects.get_or_create(student=student, course=course)

        self.stdout.write(self.style.SUCCESS(
            'Demo data ready. Students login with matric no / student123. Lecturer: LEC001 / lecturer123.'
        ))
