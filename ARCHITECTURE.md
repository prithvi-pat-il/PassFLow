# System Architecture & Workflow Diagram

## Bus Pass Management System - Workflow Diagram

### Overall System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BUS PASS MANAGEMENT SYSTEM (PassFlow)                │
│                     Flask Web Application Architecture                   │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                              PRESENTATION LAYER                          │
├─────────────────────────────────────────────────────────────────────────┤
│  • Bootstrap 5 Frontend                                                 │
│  • HTML5 Templates (Jinja2)                                             │
│  • JavaScript (Leaflet Maps, AJAX)                                      │
│  • Responsive Design (Mobile/Tablet/Desktop)                            │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                            APPLICATION LAYER (Flask)                     │
├─────────────────────────────────────────────────────────────────────────┤
│  Route Handlers                    │  Authentication/Authorization       │
│  • /register, /login               │  • Session Management              │
│  • /dashboard, /profile            │  • Role-based Access (admin/user)  │
│  • /create_pass, /payment          │  • Password Hashing (Bcrypt)       │
│  • /admin/*                        │  • CSRF Protection                 │
│  Business Logic                    │  File Upload Handling              │
│  • Pass Creation                   │  • Image Resizing (Pillow)          │
│  • Payment Processing              │  • Secure Filename                 │
│  • QR Code Generation              │  • File Validation                 │
│  • Notification System             │                                     │
│  • Background Scheduler            │                                     │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              DATA LAYER                                  │
├─────────────────────────────────────────────────────────────────────────┤
│  SQLAlchemy ORM                    │  SQLite Database                    │
│  • User Management                 │  • users                            │
│  • Profile Management              │  • profiles                         │
│  • Route Management                │  • routes                           │
│  • Pass Management                 │  • passes                           │
│  • Payment Management              │  • payments                         │
│  • Pricing Management              │  • pricing                          │
│  • Alert Configuration             │  • alert_configurations             │
│  • Notification Logs               │  • notification_logs                │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                         EXTERNAL INTEGRATIONS                            │
├─────────────────────────────────────────────────────────────────────────┤
│  • Twilio SMS (Optional)           │  • Leaflet Maps API                 │
│  • Email SMTP (Optional)           │  • QR Code Generation               │
│  • Payment Gateway (Mock)          │  • Excel Data Import                │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## User Registration & Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              START                                       │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
                        ┌─────────────────────────┐
                        │   User Lands on Site    │
                        │   (index.html)          │
                        └─────────────────────────┘
                                     ↓
                    ┌──────────────────────────────────┐
                    │  User Clicks "Register"          │
                    └──────────────────────────────────┘
                                     ↓
                   ┌─────────────────────────────────────┐
                   │  Registration Form (GET /register)  │
                   └─────────────────────────────────────┘
                                     ↓
                ┌─────────────────────────────────────────────┐
                │  User Fills: Name, Email, Phone, Password   │
                │  (POST /register)                           │
                └─────────────────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Validate Form Data            │
                    │  • Check all fields filled     │
                    │  • Check passwords match       │
                    │  • Check email unique          │
                    └────────────────────────────────┘
                                     ↓
                           ┌────────────────────┐
                           │  Validation        │
                           │  Successful?       │
                           └────────────────────┘
                       YES ↙        ↘ NO
            ┌──────────────┐       ┌──────────────┐
            │ Create User  │       │ Show Error   │
            │ • Hash pwd   │       │ Message      │
            │ • Add to DB  │       │ • Return to  │
            │ • Create     │       │   Form       │
            │   Profile    │       └──────────────┘
            └──────────────┘
                    ↓
        ┌───────────────────────────┐
        │  Success Message          │
        │  Redirect to /login       │
        └───────────────────────────┘
                    ↓
            ┌──────────────────┐
            │  Login Form      │
            │  (GET /login)    │
            └──────────────────┘
                    ↓
        ┌───────────────────────────────┐
        │  User Enters Credentials      │
        │  (POST /login)                │
        └───────────────────────────────┘
                    ↓
            ┌────────────────────┐
            │  Validate Login    │
            │  • Check email     │
            │  • Verify password │
            └────────────────────┘
                    ↓
         ┌───────────────────────┐
         │  Credentials Valid?   │
         └───────────────────────┘
     YES ↙        ↘ NO
┌────────────┐    ┌────────────┐
│ Create     │    │ Show Error │
│ Session    │    │ Redirect to│
│ Redirect   │    │ Login Form │
│ Based on   │    └────────────┘
│ Role       │
│ • admin →  │
│   /admin   │
│ • user →   │
│   /dashboard│
└────────────┘
      ↓
┌──────────────┐
│   FINISH     │
│ (Dashboard)  │
└──────────────┘
```

---

## Student Bus Pass Creation Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              START                                       │
│                        (Logged-in Student)                               │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Access Dashboard              │
                    │  (GET /dashboard)              │
                    └────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Profile Complete?             │
                    │  (Check is_complete flag)      │
                    └────────────────────────────────┘
              NO ↙                          ↘ YES
  ┌──────────────────────┐     ┌──────────────────────────────────┐
  │ Redirect to          │     │  Display:                        │
  │ /profile/complete    │     │  • Available Locations           │
  │ • Enter PRN          │     │  • Pricing Information           │
  │ • Upload Photo       │     │  • Bus Routes                    │
  │ • Select Location    │     │  • Route Map Link                │
  │ • Enter Semester     │     │  • Latest Pass Status            │
  │ • Select Route       │     └──────────────────────────────────┘
  │ • Generate Pass No.  │                      ↓
  └──────────────────────┘      ┌──────────────────────────────┐
            ↓                   │  User Clicks "Create Pass"   │
    ┌──────────────────────┐   └──────────────────────────────┘
    │ Save Profile         │              ↓
    │ (POST /profile/      │   ┌──────────────────────────────┐
    │   complete)          │   │  Select Location & Route     │
    └──────────────────────┘   │  (GET /create_pass)          │
            ↓                  └──────────────────────────────┘
    Return to Dashboard                 ↓
            ↓              ┌──────────────────────────────┐
            └────────────→ │  Submit Selection            │
            (User completes)│  (POST /create_pass)         │
                            └──────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  Calculate Price               │
                    │  • Query Pricing table         │
                    │  • Store in session            │
                    └────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Redirect to Payment Gateway           │
            │  (GET /payment_gateway)                │
            │  • Display Amount                      │
            │  • Generate QR Code                    │
            │  • Show Payment Options                │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  User Makes Payment                    │
            │  (POST /process_payment)               │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Process Payment                       │
            │  • Create Pass Record                  │
            │  • Set Status: "Approved"              │
            │  • Create Payment Record               │
            │  • Generate Transaction ID             │
            │  • Update Profile with Route           │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Success!                              │
            │  Redirect to Pass Details              │
            │  (GET /pass/<id>)                      │
            │  • Show Pass Info                      │
            │  • Display QR Code                     │
            │  • Show Expiry Info                    │
            │  • Print Option                        │
            └────────────────────────────────────────┘
                                     ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              FINISH                                      │
│                        (Pass Created & Active)                           │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Admin Workflow - Pass Management Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              START                                       │
│                    (Logged-in Admin User)                                │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Access Admin Dashboard                │
            │  (GET /admin)                          │
            │  • View Statistics                     │
            │  • Recent Passes                       │
            │  • Pending Approvals                   │
            └────────────────────────────────────────┘
                                     ↓
        ┌───────────────────────────────────────────────┐
        │  Admin Navigation Menu                        │
        └───────────────────────────────────────────────┘
                         │
        ┌────────────────┼────────────────┐
        ↓                ↓                ↓
┌─────────────┐   ┌──────────────┐  ┌─────────────┐
│ Approve     │   │ Manage Routes│  │ Manage      │
│ Passes      │   │              │  │ Pricing     │
└─────────────┘   └──────────────┘  └─────────────┘
        ↓                ↓                ↓
┌─────────────┐   ┌──────────────┐  ┌─────────────┐
│ View Pending│   │ Add/Edit     │  │ Add/Edit    │
│ Applications│   │ Routes       │  │ Prices      │
│             │   │ • Stops      │  │             │
│ For each:   │   │ • Timings    │  │             │
│ • View Details│  │ • Bus Number │  │             │
│ • Approve   │   │              │  │             │
│ • Reject    │   └──────────────┘  └─────────────┘
└─────────────┘
        ↓
┌──────────────────────────────────────────────┐
│  Action Decision: Approve or Reject?         │
└──────────────────────────────────────────────┘
        ↓
   ┌────────┐
   │ Choice │
   └────────┘
Approve ↙  ↘ Reject
┌──────┐    ┌────────┐
│ Update│   │ Update │
│ Status│   │ Status │
│ to    │   │ to     │
│ "Approved"││"Rejected"│
│ Send  │   │ Notify │
│ Notification│User    │
└──────┘    └────────┘
   ↓            ↓
┌──────────────────────────────┐
│  Return to Admin Dashboard   │
└──────────────────────────────┘
           ↓
┌─────────────────────────────────────────────────────────────────────────┐
│                              FINISH                                      │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Data Model Relationships

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           DATABASE SCHEMA                                │
└─────────────────────────────────────────────────────────────────────────┘

    ┌──────────────┐
    │     USER     │
    │──────────────│
    │ id (PK)      │
    │ name         │
    │ email        │
    │ phone        │
    │ password     │
    │ role         │
    │ created_at   │
    └──────────────┘
         │
         │ 1:N
         ├─────────────────────────────────────────┐
         │                                         │
    ┌──────────────┐                        ┌──────────────┐
    │   PROFILE    │                        │     PASS     │
    │──────────────│                        │──────────────│
    │ id (PK)      │                        │ id (PK)      │
    │ user_id (FK) │───────────────────────→│ user_id (FK) │
    │ prn          │  1:1                   │ route_id(FK) │
    │ pass_no      │                        │ amount_paid  │
    │ photo        │                        │ issue_date   │
    │ location     │                        │ expiry_date  │
    │ semester     │                        │ status       │
    │ semester_end │                        │ created_at   │
    │ route_id(FK) │                        └──────────────┘
    │ bus_number   │                              │
    │ is_complete  │                              │ 1:1
    │ created_at   │                              │
    └──────────────┘                              │
         │                                        │
         │ N:1                                    ↓
         │                                  ┌──────────────┐
         └─────────────────────────────────→│   ROUTE      │       ┌──────────────┐
                                           │──────────────│       │   PAYMENT    │
                                           │ id (PK)      │←──────│──────────────│
                                           │ name         │  N:1  │ id (PK)      │
                                           │ bus_number   │       │ user_id (FK) │
                                           │ stops (JSON) │       │ pass_id (FK) │
                                           │ timings(JSON)│       │ amount       │
                                           │ created_at   │       │ method       │
                                           └──────────────┘       │ transaction_id│
                                                                  │ status       │
                                                                  │ created_at   │
                                                                  └──────────────┘
                                                                         │
    ┌───────────────────────────────────────────┐                     │
    │          PRICING                          │◄────────────────────┘
    │───────────────────────────────────────────│
    │ id (PK)                                   │
    │ location                                  │
    │ price                                     │
    │ created_at                                │
    └───────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────────────────┐
    │              NOTIFICATION SYSTEM                                 │
    ├──────────────────────────────────────────────────────────────────┤
    │  ┌─────────────────────────┐    ┌─────────────────────────────┐ │
    │  │ ALERT_CONFIGURATION     │    │ NOTIFICATION_LOG            │ │
    │  │─────────────────────────│    │─────────────────────────────│ │
    │  │ id (PK)                 │    │ id (PK)                     │ │
    │  │ name                    │────│ user_id (FK)                │ │
    │  │ days_before             │  N │ pass_id (FK)                │ │
    │  │ email_template          │    │ alert_config_id (FK)        │ │
    │  │ sms_template            │    │ notification_type           │ │
    │  │ is_active               │    │ recipient                   │ │
    │  │ created_at              │    │ message                     │ │
    │  │ updated_at              │    │ status                      │ │
    │  └─────────────────────────┘    │ error_message               │ │
    │                                  │ sent_at                     │ │
    │                                  │ created_at                  │ │
    │                                  └─────────────────────────────┘ │
    └──────────────────────────────────────────────────────────────────┘
```

---

## Background Notification System

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    BACKGROUND SCHEDULER (Thread)                         │
│              Checks Pass Expiry Alerts Every Hour                        │
└─────────────────────────────────────────────────────────────────────────┘
                                     ↓
                    ┌────────────────────────────────┐
                    │  App Starts                    │
                    │  start_alert_scheduler()       │
                    │  Called                        │
                    └────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Background Thread Starts               │
            │  • Runs independently                  │
            │  • Checks every 3600 seconds (1 hour)  │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  send_expiry_alerts()                  │
            │  • Get Active Alert Configs            │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  For Each Alert Configuration:         │
            │  • 3 Weeks Before (21 days)            │
            │  • 1 Week Before (7 days)              │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Calculate Target Date                 │
            │  target_date = today + days_before     │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Query Passes                         │
            │  • expiry_date == target_date          │
            │  • status == 'Approved'                │
            │  • No previous alert sent              │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  For Each Pass:                        │
            │  • Get User Details                    │
            │  • Format Email Template               │
            │  • Format SMS Template                 │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Send Notifications                    │
            │  • send_email_notification()           │
            │  • send_sms_notification()             │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Log Notification Attempt               │
            │  • Create NotificationLog entry         │
            │  • Mark as 'sent' or 'failed'           │
            │  • Store error if failed                │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Commit to Database                    │
            │  • Save all logs                       │
            └────────────────────────────────────────┘
                                     ↓
            ┌────────────────────────────────────────┐
            │  Wait 1 Hour                           │
            │  • sleep(3600)                         │
            └────────────────────────────────────────┘
                                     ↓
                    ┌────────────────────────┐
                    │  Loop Back to Check    │
                    └────────────────────────┘
```

---

## Security & Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        SECURITY ARCHITECTURE                             │
└─────────────────────────────────────────────────────────────────────────┘

    ┌────────────────────────┐
    │  User Request          │
    └────────────────────────┘
             ↓
    ┌────────────────────────────────────┐
    │  Flask Route Decorator Check       │
    │  • @login_required                 │
    │  • @admin_required                 │
    └────────────────────────────────────┘
             ↓
    ┌────────────────────────────────────┐
    │  Session Check                     │
    │  • 'user_id' in session?           │
    └────────────────────────────────────┘
             ↓
    NO ↙            ↘ YES
┌──────────┐     ┌──────────────────────┐
│ Redirect │     │ Fetch User from DB   │
│ to Login │     │ • Get user.role      │
└──────────┘     └──────────────────────┘
                       ↓
         ┌─────────────────────────────┐
         │  Check Admin Access         │
         │  • user.role == 'admin'?    │
         └─────────────────────────────┘
                       ↓
            ┌──────────────────────┐
            │  Grant Access        │
            │  • Execute Handler   │
            └──────────────────────┘

    ┌────────────────────────────────────┐
    │  Password Security                 │
    │  • Registration: Hash with Bcrypt  │
    │  • Login: Verify with Bcrypt       │
    │  • Storage: Never plain text       │
    └────────────────────────────────────┘

    ┌────────────────────────────────────┐
    │  File Upload Security              │
    │  • Secure filename generation      │
    │  • Image resizing (Pillow)         │
    │  • Max file size check             │
    │  • Upload folder isolation         │
    └────────────────────────────────────┘

    ┌────────────────────────────────────┐
    │  SQL Injection Protection          │
    │  • SQLAlchemy ORM                  │
    │  • Parameterized queries           │
    │  • No raw SQL strings              │
    └────────────────────────────────────┘

    ┌────────────────────────────────────┐
    │  Session Security                  │
    │  • Flask secret key                │
    │  • Session timeouts                │
    │  • Secure cookie flags             │
    └────────────────────────────────────┘
```

---

## Deployment Architecture (Render)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         DEPLOYMENT ARCHITECTURE                          │
└─────────────────────────────────────────────────────────────────────────┘

    GitHub Repository
    (PassFlow)
           ↓
           │ Git Push Triggers Build
           ↓
    ┌─────────────────────────────────────┐
    │       Render Build Process          │
    ├─────────────────────────────────────┤
    │  1. Clone Repository                │
    │  2. Detect Python Runtime           │
    │  3. Install Dependencies            │
    │     (requirements.txt)              │
    │  4. Build Static Assets             │
    │  5. Prepare Application             │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │      Production Server              │
    ├─────────────────────────────────────┤
    │  Web Server: Gunicorn               │
    │  WSGI Application: app_complete.py  │
    │  Port: Dynamic (Render provides)    │
    │  Host: 0.0.0.0                      │
    │  Workers: Auto-scaling              │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │      Application Containers         │
    ├─────────────────────────────────────┤
    │  • SQLite Database (ephemeral)      │
    │  • File Storage (static/uploads/)   │
    │  • Background Scheduler             │
    │  • Session Management               │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │      External Services              │
    ├─────────────────────────────────────┤
    │  • Twilio SMS (Optional)            │
    │  • Email SMTP (Optional)            │
    │  • Leaflet Maps (Client-side)       │
    └─────────────────────────────────────┘
           ↓
    ┌─────────────────────────────────────┐
    │      User Access                    │
    ├─────────────────────────────────────┤
    │  Public URL: app-name.onrender.com  │
    │  HTTPS: Automatic                   │
    │  Load Balancing: Auto               │
    └─────────────────────────────────────┘

    ┌─────────────────────────────────────────────────────────────────┐
    │                    ENVIRONMENT VARIABLES                         │
    ├─────────────────────────────────────────────────────────────────┤
    │  • PORT (Auto-set by Render)                                    │
    │  • SECRET_KEY (Auto-generated)                                  │
    │  • TWILIO_ACCOUNT_SID (Optional)                                │
    │  • TWILIO_AUTH_TOKEN (Optional)                                 │
    │  • TWILIO_FROM (Optional)                                       │
    │  • SMTP Configuration (Optional)                                │
    └─────────────────────────────────────────────────────────────────┘
```

---

## Technology Stack Summary

```
┌─────────────────────────────────────────────────────────────────────────┐
│                        TECHNOLOGY STACK                                  │
└─────────────────────────────────────────────────────────────────────────┘

    BACKEND:
    ┌─────────────────────────────────────┐
    │ • Python 3.x                        │
    │ • Flask 2.3.3                       │
    │ • Flask-SQLAlchemy 3.0.5            │
    │ • Flask-Bcrypt 1.0.1                │
    │ • Gunicorn 21.2.0 (Production)      │
    │ • SQLite (Database)                 │
    └─────────────────────────────────────┘

    FRONTEND:
    ┌─────────────────────────────────────┐
    │ • HTML5 + Jinja2 Templates          │
    │ • Bootstrap 5                       │
    │ • JavaScript (Vanilla)              │
    │ • Leaflet.js (Maps)                 │
    │ • OpenStreetMap                     │
    └─────────────────────────────────────┘

    UTILITIES:
    ┌─────────────────────────────────────┐
    │ • Pillow (Image Processing)         │
    │ • QRCode (QR Generation)            │
    │ • Bcrypt (Password Hashing)         │
    │ • Twilio (SMS Notifications)        │
    │ • Werkzeug (Security)               │
    └─────────────────────────────────────┘

    DEPLOYMENT:
    ┌─────────────────────────────────────┐
    │ • Render.com (Hosting)              │
    │ • GitHub (Version Control)          │
    │ • Gunicorn (WSGI Server)            │
    │ • HTTPS (SSL/TLS)                   │
    └─────────────────────────────────────┘
```

---

## Key Design Patterns

1. **MVC Architecture**: Model-View-Controller separation
2. **Decorator Pattern**: `@login_required`, `@admin_required`
3. **Template Pattern**: Jinja2 templates for views
4. **Observer Pattern**: Background scheduler observes pass expiry
5. **Singleton Pattern**: Flask app instance
6. **Factory Pattern**: Route and pricing factories
7. **Strategy Pattern**: Different notification strategies (email/SMS)

---

## System Capabilities

### Student Features
- ✅ Secure Registration & Authentication
- ✅ Profile Management with Photo Upload
- ✅ Interactive Route Map
- ✅ Pass Creation & Payment
- ✅ Pass Details & QR Code
- ✅ Password Change
- ✅ Expiry Alerts

### Admin Features
- ✅ Dashboard with Statistics
- ✅ Pass Approval/Rejection
- ✅ Route Management
- ✅ Pricing Management
- ✅ User Management
- ✅ Payment Tracking
- ✅ Notification Configuration
- ✅ Bulk Print

---

This architecture document provides a comprehensive overview of the Bus Pass Management System's structure, workflows, and technical implementation.
