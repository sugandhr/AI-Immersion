# 🏥 SmartCare Queue AI

### “Less Waiting. Better Care.”

**SmartCare Queue AI** is an enterprise-grade, full-stack, AI-powered Hospital Queue Management Platform designed to eliminate physical waiting-room overcrowding, reduce patient anxiety, and streamline outpatient department (OPD) hospital operations.

---

## 1. Project Problem & Solution

### The Problem
Patients and their families traditionally spend hours trapped in chaotic hospital waiting rooms for:
- Initial registration & card issuance
- Doctor consultation & specialist OPD queues
- Diagnostic laboratory sample collection
- Inpatient & outpatient pharmacy dispensing
- Insurance verification & billing clearance

Physical queues generate high patient frustration, dangerous waiting-room overcrowding, delays in urgent care, and operational blind spots for clinical staff.

### The Solution
SmartCare Queue AI provides a digital-first hospital workflow where patients can:
1. **Join queues remotely** from their smartphone or digital kiosk.
2. **Receive a concurrency-safe atomic digital token** and safe QR reference.
3. **Monitor real-time queue position**, live token calls, and dynamic AI wait estimations.
4. **Navigate inside the hospital** using an interactive multi-floor indoor waypoint map.
5. **Track 4-stage laboratory orders** and digitally simulate OPD fee payments.

Hospital staff, attending physicians, and administrators have specialized operational consoles to call next tokens, manage counter assignments, review diagnostic test flows, and evaluate predictive resource analytics.

---

## 2. Technology Stack

- **Frontend**: Pure **HTML5**, **CSS3**, and **Vanilla JavaScript** (Zero frameworks: No React, Vue, Angular, Next.js, TypeScript, Tailwind, Bootstrap, or jQuery).
- **Styling**: Curated Vanilla CSS design system with custom HSL tokens, rounded cards, glassmorphism, high contrast accessibility mode, and fluid mobile responsiveness.
- **Backend**: **Python 3**, **Flask**, **Flask-CORS**, modular Blueprints, and server-side Supabase client.
- **Database**: **Supabase PostgreSQL** with strict primary/foreign key constraints, unique checks, performance indexes, and transactional concurrency locking.
- **Authentication**: **Supabase Auth** & RFC-7519 compliant JSON Web Tokens (JWT) with secure HTTP headers.
- **Security & Authorization**: PostgreSQL **Row Level Security (RLS)** ensuring patients can strictly never access other patients' private health records.
- **AI Services**: Analytical waiting-time prediction engine, historical crowd density forecasting (Best Time to Visit), and NLP Operational Hospital Assistant.

---

## 3. System Architecture

```
                         SMARTCARE QUEUE AI
                                │
                ┌───────────────┴───────────────┐
                │                               │
          Patient Portal                  Staff Portal
          (HTML/CSS/JS)                   (HTML/CSS/JS)
                │                               │
                └───────────────┬───────────────┘
                                │
                       Flask REST API
                         (Port 5002)
                                │
                    Authentication Middleware
                         (Bearer JWT)
                                │
                ┌───────────────┴───────────────┐
                │                               │
      Supabase PostgreSQL             Supabase Realtime
       • Row Level Security            • Live Token Calls
       • Concurrency Functions         • Status Updates
       • 13 Normalized Tables
                │
      AI Prediction Engine
       • Wait Time Estimator
       • Best Time to Visit
       • Resource Insights
```

---

## 4. Directory Structure

```
SmartCare-Queue-AI/
│
├── frontend/                     # 22 Responsive Semantic HTML5 Pages
│   ├── index.html                # Public Landing Page & Feature Showcase
│   ├── login.html                # Patient Login
│   ├── register.html             # Patient Registration
│   ├── forgot-password.html      # Password Recovery
│   │
│   ├── patient-dashboard.html    # Patient Live OPD Hub
│   ├── queue.html                # Digital Queue Joining
│   ├── appointments.html         # Scheduled Doctor Bookings
│   ├── departments.html          # Clinical Department Directory
│   ├── hospital-map.html         # Interactive Indoor Wayfinding Floorplan
│   ├── qr-token.html             # Safe QR Token & Verification
│   ├── lab-tests.html            # Diagnostic Stage Tracker
│   ├── billing.html              # OPD Invoices & Simulated Digital Payment
│   ├── waiting-history.html      # Patient Visit Logs & Metrics
│   ├── best-time.html            # AI Low-Crowd Visiting Forecast
│   ├── notifications.html        # Real-time Patient Alerts
│   ├── feedback.html             # 5-Star Rating & Review Matrix
│   ├── ai-assistant.html         # Operational NLP Hospital Guide
│   ├── accessibility.html        # High Contrast, Text Scale & Voice Synthesis
│   │
│   ├── staff-login.html          # Clinical & Admin Login
│   ├── staff-dashboard.html      # Counter Desk Operations & KPIs
│   ├── queue-management.html     # Live Call Next, Recall, Skip, Complete
│   ├── patients.html             # Operational Patient Directory
│   ├── doctors.html              # Specialist Status & Counter Desk Controls
│   ├── staff-departments.html    # Department Configuration
│   ├── staff-lab.html            # Laboratory Processing
│   ├── staff-billing.html        # OPD Invoice Generation Desk
│   ├── analytics.html            # Pure Canvas Charts & AI Insights
│   ├── staff-feedback.html       # Aggregated Patient Reviews
│   │
│   ├── doctor-dashboard.html     # Attending Physician Consultation Portal
│   └── admin-dashboard.html      # Executive Hospital System Console
│
├── css/                          # 10 Vanilla CSS Stylesheets
│   ├── style.css                 # Global Tokens, Reset, Buttons, Modals, Toasts
│   ├── auth.css                  # Split-Screen Auth & Demo Autofill
│   ├── dashboard.css             # Navigation Sidebar, Top Header, Stats Grid
│   ├── queue.css                 # Large Digital Token Badge & Pulsing Indicators
│   ├── map.css                   # Floorplan Canvas & Route Steps
│   ├── billing.css               # Invoice Breakdown & Payment Method Selectors
│   ├── staff.css                 # Queue Action Bar & Operational Tables
│   ├── analytics.css             # Canvas Chart Styling & Severity Banners
│   ├── accessibility.css         # WCAG AA High Contrast & Text Scaling
│   └── responsive.css            # Mobile & Tablet Breakpoint Optimization
│
├── js/                           # 18 Modular Vanilla JavaScript Files
│   ├── config.js                 # API Endpoints & Supabase Settings
│   ├── api.js                    # Central HTTP Fetch Wrapper & Toast Notifier
│   ├── auth.js                   # JWT / Supabase Session & Role Page Guards
│   ├── patient.js                # Patient Dashboard & Live Polling
│   ├── queue.js                  # Department Selection & Atomic Token Generation
│   ├── appointments.js           # Doctor Appointment Scheduling
│   ├── departments.js            # Department Directory
│   ├── navigation.js             # Canvas Hospital Floorplan & Waypoint Routing
│   ├── qr-token.js               # Safe Token QR Generator (Canvas)
│   ├── lab.js                    # Diagnostic Stage Progression
│   ├── billing.js                # Simulated Payment Processing
│   ├── notifications.js          # User Notification Dispatcher
│   ├── history.js                # Visit History Analytics
│   ├── best-time.js              # AI Crowd Prediction Heatbars
│   ├── feedback.js               # Star Rating Submissions
│   ├── ai-assistant.js           # NLP Assistant & Medical Guardrails
│   ├── accessibility.js          # Multi-Language (EN, TA, HI) & Speech Audio
│   ├── staff.js                  # Queue Counter Actions (Call, Skip, Complete)
│   └── analytics.js              # Pure HTML5 Canvas Chart Renderers
│
├── backend/                      # Python Flask REST API
│   ├── app.py                    # Main Flask App & Static Asset Server
│   ├── config.py                 # Environment Configuration
│   ├── requirements.txt          # Python Package Dependencies
│   ├── .env.example              # Environment Variable Template
│   ├── routes/                   # 13 Modular Blueprints
│   ├── services/                 # Queue, Prediction, Notification, Analytics Services
│   ├── middleware/               # Auth & Role-Based Authorization
│   └── utils/                    # Input Validators & Response Helpers
│
├── supabase/                     # Database Engine
│   ├── schema.sql                # Complete Table DDL, Constraints & Indexes
│   ├── policies.sql              # PostgreSQL Row Level Security (RLS) Policies
│   ├── functions.sql             # Atomic Concurrency Token Function & Triggers
│   └── seed.sql                  # Realistic Demo Departments, Doctors, and Visits
│
├── .gitignore                    # Git Exclusion Rules (Protects .env & venv)
├── README.md                     # Documentation
└── requirements.txt              # Root Python Dependencies
```

---

## 5. Step-by-Step Setup Guide

### Step 1: Clone or Navigate to Project
```bash
cd "/Users/sugandh/AI Immersion 2026/SmartCare-Queue-AI"
```

### Step 2: Set Up Python Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Step 3: Configure Database in Supabase
1. Create a new Supabase project at [https://supabase.com](https://supabase.com).
2. Navigate to the **SQL Editor** in your Supabase dashboard.
3. Execute the SQL scripts in this exact order:
   - `supabase/schema.sql` (Creates all 13 core tables, constraints, and indexes)
   - `supabase/policies.sql` (Enforces Row Level Security for data privacy)
   - `supabase/functions.sql` (Installs the concurrency-safe token function `generate_queue_token`)
   - `supabase/seed.sql` (Populates demo departments, specialists, and hospital nodes)

### Step 4: Configure Environment Variables
Copy `backend/.env.example` to `backend/.env`:
```bash
cp backend/.env.example backend/.env
```
Fill in your Supabase credentials:
```ini
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-public-key
SUPABASE_SERVICE_ROLE_KEY=your-service-role-secret-key
FLASK_SECRET_KEY=smartcare-super-secret-key-change-in-production
PORT=5001
```

> **Note on Zero-Setup Evaluation:** The project includes an intelligent offline database fallback pre-populated with identical seed data. Even before you connect live Supabase credentials, the app runs 100% out of the box with fully working APIs, concurrency locking, and token workflows!

### Step 5: Start the Flask Backend Server
```bash
./venv/bin/python3 -m backend.app
```
The server will start on: `http://localhost:5002`.

### Step 6: Open the Application
Open your web browser and navigate to:
```
http://localhost:5002/
```
Or open `frontend/index.html` directly.

---

## 6. Demo Accounts & Credentials

To test the role-based features without creating accounts, use these pre-seeded demo logins:

| Role | Email | Password | Access Portal |
| :--- | :--- | :--- | :--- |
| **Patient** | `patient@smartcare.org` | `password123` | Patient Dashboard & Queue |
| **Patient (Alt)** | `rahul.raj@example.com` | `password123` | Patient Dashboard & Queue |
| **Staff Nurse** | `staff@smartcare.org` | `password123` | Staff Queue Management |
| **Doctor** | `arun.cardio@smartcare.org` | `password123` | Doctor Consultation Desk |
| **Administrator** | `admin@smartcare.org` | `password123` | Hospital Admin Console |

Clicking any **Quick Demo Role** chip on the login screens automatically fills these credentials.

---

## 7. Security & Concurrency Safety

### 🔒 Concurrency-Safe Token Generation
To prevent multiple patients from receiving duplicate token numbers when clicking "Join Queue" simultaneously, the system uses:
1. PostgreSQL row-level locks via `SELECT ... FOR UPDATE` in `generate_queue_token()`.
2. Master counter increments inside isolated atomic database transactions.
3. Thread-safe execution locks on the Flask server.

### 🛡️ Row Level Security (RLS)
PostgreSQL Row Level Security is active across all tables:
- **Patients** can only query their own queue entries, appointments, lab orders, invoices, and notifications (`auth.uid() = patient_id`).
- **Staff** and **Doctors** have operational access restricted to hospital counters and assigned patients.
- **Service Role Key** is restricted strictly to backend server code and never exposed to the frontend browser.

---

## 8. AI Safety Guardrails

SmartCare Queue AI strictly adheres to healthcare software safety guidelines:
- **Operational Only**: The AI wait-time estimation and Best Time to Visit modules operate strictly on logistical variables (active doctors, queue counts, time of day).
- **No Medical Diagnoses**: The AI Assistant strictly detects and blocks medical queries (e.g. diagnosing symptoms, prescribing drug doses, or making emergency treatment calls), directing patients to the physical Emergency Department (Ground Floor, Gate 2) or licensed medical officers.

---

## 9. Disclaimer

*SmartCare Queue AI is developed as an advanced full-stack AI engineering capstone demonstration project. All medical personnel names, patient records, and diagnostic reports in the seed data are strictly fictional. It is not intended to replace certified emergency response dispatch or professional medical consultation.*
