# QR Code Attendance System
Design and Implementation of an Automated Attendance System Using QR Code Technology
Alvan Ikoku Federal University of Education, Owerri, Imo State

## Setup Instructions

1. **Install Python 3.10+** if not already installed.

2. **Create a virtual environment and install dependencies:**
   ```
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run migrations to create the database:**
   ```
   python manage.py makemigrations
   python manage.py migrate
   ```

4. **Seed demo data (creates a lecturer, 3 students, and one course):**
   ```
   python manage.py seed_demo
   ```
   This prints login credentials to the terminal — save them.

5. **Run the development server:**
   ```
   python manage.py runserver 0.0.0.0:8000
   ```

6. **Access the app:**
   - On your computer: http://127.0.0.1:8000
   - On your phone (same WiFi, for camera scanning to work over HTTP): use your computer's local IP,
     e.g. http://192.168.x.x:8000 — find it with `ipconfig` (Windows) or `ifconfig` (Mac/Linux).
   - Django admin: http://127.0.0.1:8000/admin (login: admin / admin12345)

   **Note:** Most mobile browsers only allow camera access on `https://` or `localhost`.
   If scanning fails on your phone over plain HTTP, either:
   - Test the scan page on the same machine via `localhost`, or
   - Use a tool like `ngrok` to tunnel your local server over HTTPS for a live demo.

## How to Demo for Your Defense

1. Log in as the lecturer (`LEC001` / `lecturer123`), go to the dashboard, click
   "Start Session & Generate QR" for CSC401. A QR code appears, refreshing the
   attendance count live.
2. On another device/browser, log in as a student (e.g. `AIFCE/CSC/21/001` / `student123`),
   click "Scan Attendance QR Code", and scan the code shown on the lecturer's screen.
3. The lecturer's screen updates the count automatically; click "View Attendance List"
   to see the record, and "Export CSV" to download it.

## Adding Your Own Courses/Students

Use the Django admin (`/admin`) to add real courses, lecturers, students, and enrollments
once you're ready to move past the demo data.

## Project Structure
```
attendance_system/
├── manage.py
├── requirements.txt
├── attendance_system/       # project settings, root urls
└── attendance/               # the app: models, views, templates
    ├── models.py             # User, Course, Enrollment, Session, Attendance
    ├── views.py               # auth, QR generation, scanning, validation
    ├── urls.py
    ├── admin.py
    ├── templates/attendance/
    └── management/commands/seed_demo.py
```

## Key Design Decisions (for your report)

- **QR tokens expire** (default 10 minutes, configurable in `settings.py` via
  `QR_SESSION_LIFETIME_SECONDS`) to prevent students from sharing a screenshot
  of the code after class ends.
- **Duplicate scans are blocked** at the database level via a `unique_together`
  constraint on `(student, session)`, not just application logic.
- **Enrollment is checked** before attendance is recorded, so students can only
  check into courses they're registered for.
- **GPS is optional** and captured client-side via the browser's geolocation API,
  stored as a string — you can extend `mark_attendance` in `views.py` to reject
  scans outside a geofence around the venue if you want to strengthen the
  anti-proxy argument in your report.
