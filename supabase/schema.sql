-- ==============================================================================
-- SmartCare Queue AI - Supabase PostgreSQL Database Schema
-- Problem: Hospital Queue Overcrowding & Delays
-- Tagline: "Less Waiting. Better Care."
-- ==============================================================================

-- Enable UUID extension if not enabled
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. PROFILES TABLE (Linked with Supabase Auth users)
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_user_id UUID UNIQUE,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    phone VARCHAR(50),
    date_of_birth DATE,
    gender VARCHAR(20) CHECK (gender IN ('male', 'female', 'other', 'prefer_not_to_say')),
    role VARCHAR(20) NOT NULL DEFAULT 'patient' CHECK (role IN ('patient', 'staff', 'doctor', 'admin')),
    profile_image TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 2. DEPARTMENTS TABLE
CREATE TABLE IF NOT EXISTS departments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    description TEXT,
    location VARCHAR(100) NOT NULL,
    floor VARCHAR(20) NOT NULL,
    code_prefix VARCHAR(5) NOT NULL,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 3. DOCTORS TABLE
CREATE TABLE IF NOT EXISTS doctors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    profile_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    specialization VARCHAR(150) NOT NULL,
    room_number VARCHAR(50) NOT NULL,
    average_consultation_minutes INTEGER NOT NULL DEFAULT 15 CHECK (average_consultation_minutes > 0),
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'busy', 'offline')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 4. QUEUES TABLE (Daily Queue per Department / Service)
CREATE TABLE IF NOT EXISTS queues (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE RESTRICT,
    service_type VARCHAR(50) NOT NULL,
    queue_date DATE NOT NULL DEFAULT CURRENT_DATE,
    current_token_number INTEGER NOT NULL DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'closed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_dept_service_date UNIQUE (department_id, service_type, queue_date)
);

-- 5. QUEUE ENTRIES TABLE
CREATE TABLE IF NOT EXISTS queue_entries (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    queue_id UUID NOT NULL REFERENCES queues(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES doctors(id) ON DELETE SET NULL,
    token_number INTEGER NOT NULL,
    token_code VARCHAR(30) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'waiting' CHECK (status IN ('waiting', 'called', 'serving', 'completed', 'skipped', 'cancelled')),
    priority_requested BOOLEAN NOT NULL DEFAULT FALSE,
    priority_approved BOOLEAN NOT NULL DEFAULT FALSE,
    joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    called_at TIMESTAMPTZ,
    serving_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    estimated_wait_minutes INTEGER NOT NULL DEFAULT 15,
    counter_number VARCHAR(20),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_queue_token UNIQUE (queue_id, token_number)
);

-- 6. APPOINTMENTS TABLE
CREATE TABLE IF NOT EXISTS appointments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    doctor_id UUID NOT NULL REFERENCES doctors(id) ON DELETE CASCADE,
    department_id UUID NOT NULL REFERENCES departments(id) ON DELETE CASCADE,
    appointment_date DATE NOT NULL,
    appointment_time VARCHAR(20) NOT NULL,
    reason TEXT,
    status VARCHAR(20) NOT NULL DEFAULT 'scheduled' CHECK (status IN ('scheduled', 'confirmed', 'completed', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 7. LAB ORDERS TABLE
CREATE TABLE IF NOT EXISTS lab_orders (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    doctor_id UUID REFERENCES doctors(id) ON DELETE SET NULL,
    test_name VARCHAR(150) NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'ordered' CHECK (status IN ('ordered', 'sample_collected', 'processing', 'report_ready')),
    ordered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sample_collected_at TIMESTAMPTZ,
    processing_at TIMESTAMPTZ,
    report_ready_at TIMESTAMPTZ,
    report_reference VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 8. BILLS TABLE
CREATE TABLE IF NOT EXISTS bills (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    bill_number VARCHAR(50) NOT NULL UNIQUE,
    consultation_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    lab_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    pharmacy_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    registration_fee NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    other_charges NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    total_amount NUMERIC(10, 2) NOT NULL DEFAULT 0.00,
    payment_status VARCHAR(20) NOT NULL DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'paid', 'partially_paid', 'cancelled')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9. PAYMENTS TABLE
CREATE TABLE IF NOT EXISTS payments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    bill_id UUID NOT NULL REFERENCES bills(id) ON DELETE CASCADE,
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    amount NUMERIC(10, 2) NOT NULL,
    payment_method VARCHAR(50) NOT NULL,
    transaction_id VARCHAR(100) NOT NULL UNIQUE,
    status VARCHAR(20) NOT NULL DEFAULT 'completed' CHECK (status IN ('pending', 'completed', 'failed')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 10. NOTIFICATIONS TABLE
CREATE TABLE IF NOT EXISTS notifications (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    title VARCHAR(150) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(30) NOT NULL CHECK (type IN ('queue', 'appointment', 'billing', 'lab', 'system', 'emergency')),
    is_read BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 11. HOSPITAL LOCATIONS (Indoor Navigation Nodes)
CREATE TABLE IF NOT EXISTS hospital_locations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL,
    location_type VARCHAR(50) NOT NULL,
    floor VARCHAR(20) NOT NULL,
    description TEXT,
    x_position INTEGER NOT NULL,
    y_position INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 12. PRIORITY REQUESTS TABLE
CREATE TABLE IF NOT EXISTS priority_requests (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    queue_entry_id UUID NOT NULL REFERENCES queue_entries(id) ON DELETE CASCADE,
    reason TEXT NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'approved', 'rejected')),
    reviewed_by UUID REFERENCES profiles(id) ON DELETE SET NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ
);

-- 13. FEEDBACK TABLE
CREATE TABLE IF NOT EXISTS feedback (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    patient_id UUID NOT NULL REFERENCES profiles(id) ON DELETE CASCADE,
    department_id UUID REFERENCES departments(id) ON DELETE SET NULL,
    queue_entry_id UUID UNIQUE REFERENCES queue_entries(id) ON DELETE SET NULL,
    overall_rating INTEGER NOT NULL CHECK (overall_rating BETWEEN 1 AND 5),
    waiting_rating INTEGER CHECK (waiting_rating BETWEEN 1 AND 5),
    staff_rating INTEGER CHECK (staff_rating BETWEEN 1 AND 5),
    doctor_rating INTEGER CHECK (doctor_rating BETWEEN 1 AND 5),
    facility_rating INTEGER CHECK (facility_rating BETWEEN 1 AND 5),
    comment TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ==============================================================================
-- INDEXES FOR HIGH PERFORMANCE QUERYING
-- ==============================================================================
CREATE INDEX IF NOT EXISTS idx_profiles_role ON profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);
CREATE INDEX IF NOT EXISTS idx_profiles_auth_uid ON profiles(auth_user_id);

CREATE INDEX IF NOT EXISTS idx_doctors_department ON doctors(department_id);
CREATE INDEX IF NOT EXISTS idx_doctors_status ON doctors(status);

CREATE INDEX IF NOT EXISTS idx_queues_lookup ON queues(department_id, service_type, queue_date);
CREATE INDEX IF NOT EXISTS idx_queues_date_status ON queues(queue_date, status);

CREATE INDEX IF NOT EXISTS idx_entries_queue_status ON queue_entries(queue_id, status);
CREATE INDEX IF NOT EXISTS idx_entries_patient_id ON queue_entries(patient_id);
CREATE INDEX IF NOT EXISTS idx_entries_token ON queue_entries(queue_id, token_number);
CREATE INDEX IF NOT EXISTS idx_entries_joined_at ON queue_entries(joined_at);

CREATE INDEX IF NOT EXISTS idx_appointments_patient ON appointments(patient_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(appointment_date, status);

CREATE INDEX IF NOT EXISTS idx_lab_orders_patient ON lab_orders(patient_id);
CREATE INDEX IF NOT EXISTS idx_bills_patient ON bills(patient_id);
CREATE INDEX IF NOT EXISTS idx_bills_number ON bills(bill_number);
CREATE INDEX IF NOT EXISTS idx_notifications_user ON notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_feedback_dept ON feedback(department_id);
