-- ==============================================================================
-- SmartCare Queue AI - Demo Seed Data
-- Fictional dataset for departments, doctors, locations, sample queues & visits
-- ==============================================================================

-- 1. DEPARTMENTS
INSERT INTO departments (id, name, description, location, floor, code_prefix, active) VALUES
('d1000000-0000-0000-0000-000000000001', 'General Medicine', 'Primary outpatient adult care, acute fevers, physical health assessments', 'Wing A - Room 101', 'Ground Floor', 'GM', true),
('d1000000-0000-0000-0000-000000000002', 'Cardiology', 'Heart health, ECG, echocardiograms, cardiovascular screenings', 'Wing B - Room 204', 'First Floor', 'C', true),
('d1000000-0000-0000-0000-000000000003', 'Orthopedics', 'Bones, joints, spine care, fractures, arthritis clinic', 'Wing B - Room 210', 'First Floor', 'ORT', true),
('d1000000-0000-0000-0000-000000000004', 'Pediatrics', 'Comprehensive childcare, vaccinations, developmental assessments', 'Wing C - Room 105', 'Ground Floor', 'PED', true),
('d1000000-0000-0000-0000-000000000005', 'Dermatology', 'Skin, hair, nail diagnostics and dermatological therapies', 'Wing A - Room 302', 'Second Floor', 'DER', true),
('d1000000-0000-0000-0000-000000000006', 'Neurology', 'Neurological consultations, headache disorders, nerve care', 'Wing B - Room 315', 'Second Floor', 'NEU', true),
('d1000000-0000-0000-0000-000000000007', 'ENT', 'Ear, Nose and Throat diagnostics and audiology screenings', 'Wing A - Room 205', 'First Floor', 'ENT', true),
('d1000000-0000-0000-0000-000000000008', 'Laboratory', 'Automated hematology, biochemistry, and rapid culture diagnostics', 'Central Block - Lab 1', 'Ground Floor', 'LAB', true),
('d1000000-0000-0000-0000-000000000009', 'Pharmacy', 'Outpatient drug dispensing, dosage counseling and generic medicine', 'Main Atrium - Counter 4', 'Ground Floor', 'PH', true),
('d1000000-0000-0000-0000-000000000010', 'Billing', 'Cashless insurance claims, computerized billing, receipt counters', 'Main Atrium - Counters 1-3', 'Ground Floor', 'BIL', true),
('d1000000-0000-0000-0000-000000000011', 'Registration', 'New patient registrations, digital token kiosks, inquiries', 'Main Entrance - Reception', 'Ground Floor', 'REG', true),
('d1000000-0000-0000-0000-000000000012', 'Emergency', '24/7 Trauma, acute resuscitation and critical medical triage', 'Emergency Bay - Gate 2', 'Ground Floor', 'EMG', true)
ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, code_prefix = EXCLUDED.code_prefix;

-- 2. FICTIONAL DEMO PROFILES (Staff, Doctors, Patients, Admin)
INSERT INTO profiles (id, auth_user_id, full_name, email, phone, gender, role) VALUES
-- Admin
('a0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000001', 'Hospital Administrator', 'admin@smartcare.org', '+91 98765 43210', 'other', 'admin'),
-- Staff
('s0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000002', 'Staff Nurse Ananya', 'staff@smartcare.org', '+91 98765 43211', 'female', 'staff'),
-- Doctors
('b0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000003', 'Dr. Arun Kumar', 'arun.cardio@smartcare.org', '+91 98765 43212', 'male', 'doctor'),
('b0000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000004', 'Dr. Priya Devi', 'priya.genmed@smartcare.org', '+91 98765 43213', 'female', 'doctor'),
('b0000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000005', 'Dr. Rahul Kumar', 'rahul.ortho@smartcare.org', '+91 98765 43214', 'male', 'doctor'),
('b0000000-0000-0000-0000-000000000004', '00000000-0000-0000-0000-000000000006', 'Dr. Divya S', 'divya.pedia@smartcare.org', '+91 98765 43215', 'female', 'doctor'),
-- Patients
('c0000000-0000-0000-0000-000000000001', '00000000-0000-0000-0000-000000000007', 'Priya Sharma', 'patient@smartcare.org', '+91 98765 43220', 'female', 'patient'),
('c0000000-0000-0000-0000-000000000002', '00000000-0000-0000-0000-000000000008', 'Rahul Raj', 'rahul.raj@example.com', '+91 98765 43221', 'male', 'patient'),
('c0000000-0000-0000-0000-000000000003', '00000000-0000-0000-0000-000000000009', 'Karthik M', 'karthik.m@example.com', '+91 98765 43222', 'male', 'patient')
ON CONFLICT (id) DO UPDATE SET full_name = EXCLUDED.full_name;

-- 3. DOCTOR ASSIGNMENTS
INSERT INTO doctors (id, profile_id, department_id, specialization, room_number, average_consultation_minutes, status) VALUES
('doc00000-0000-0000-0000-000000000001', 'b0000000-0000-0000-0000-000000000001', 'd1000000-0000-0000-0000-000000000002', 'Senior Cardiologist (MD, DM)', 'Room 204', 15, 'available'),
('doc00000-0000-0000-0000-000000000002', 'b0000000-0000-0000-0000-000000000002', 'd1000000-0000-0000-0000-000000000001', 'Chief Consultant Physician (MD)', 'Room 101', 12, 'available'),
('doc00000-0000-0000-0000-000000000003', 'b0000000-0000-0000-0000-000000000003', 'd1000000-0000-0000-0000-000000000003', 'Orthopedic Surgeon (MS Ortho)', 'Room 210', 18, 'available'),
('doc00000-0000-0000-0000-000000000004', 'b0000000-0000-0000-0000-000000000004', 'd1000000-0000-0000-0000-000000000004', 'Pediatric Specialist (MD)', 'Room 105', 14, 'available')
ON CONFLICT (id) DO NOTHING;

-- 4. HOSPITAL INDOOR LOCATIONS (Coordinates for map rendering)
INSERT INTO hospital_locations (id, name, location_type, floor, description, x_position, y_position) VALUES
('loc00000-0000-0000-0000-000000000001', 'Main Entrance', 'entrance', 'Ground Floor', 'Main hospital reception, digital kiosks, information', 80, 480),
('loc00000-0000-0000-0000-000000000002', 'Registration Counter', 'service', 'Ground Floor', 'Patient registration, card issue, inquiries', 180, 420),
('loc00000-0000-0000-0000-000000000003', 'Central Waiting Lounge', 'waiting', 'Ground Floor', 'Comfortable air-conditioned seating with live token displays', 360, 360),
('loc00000-0000-0000-0000-000000000004', 'Billing & Cashless Helpdesk', 'billing', 'Ground Floor', 'OPD billing counters 1 to 3', 540, 420),
('loc00000-0000-0000-0000-000000000005', 'Outpatient Pharmacy', 'pharmacy', 'Ground Floor', 'Pharmacy medicine dispensary counter 4', 680, 420),
('loc00000-0000-0000-0000-000000000006', 'Central Laboratory & Blood Collection', 'lab', 'Ground Floor', 'Blood draw, sample collection & automated diagnostics', 680, 220),
('loc00000-0000-0000-0000-000000000007', 'General Medicine OPD', 'clinic', 'Ground Floor', 'Rooms 101 to 104, Adult health checkups', 180, 200),
('loc00000-0000-0000-0000-000000000008', 'Emergency Trauma Bay', 'emergency', 'Ground Floor', '24x7 Emergency resuscitation and ambulance bay', 80, 160),
('loc00000-0000-0000-0000-000000000009', 'Cardiology Center', 'clinic', 'First Floor', 'Cardiology consultation rooms 201-204, ECG, Echo', 260, 220),
('loc00000-0000-0000-0000-000000000010', 'Orthopedic Clinic & Cast Room', 'clinic', 'First Floor', 'Rooms 210-214, Joint and spine rehabilitation', 500, 220),
('loc00000-0000-0000-0000-000000000011', 'Pediatric Care & Play Area', 'clinic', 'Ground Floor', 'Rooms 105-108, Child friendly clinical rooms', 360, 160)
ON CONFLICT (id) DO NOTHING;

-- 5. ACTIVE QUEUES (Today)
INSERT INTO queues (id, department_id, service_type, queue_date, current_token_number, status) VALUES
('q0000000-0000-0000-0000-000000000001', 'd1000000-0000-0000-0000-000000000002', 'Consultation', CURRENT_DATE, 25, 'active'),
('q0000000-0000-0000-0000-000000000002', 'd1000000-0000-0000-0000-000000000001', 'Consultation', CURRENT_DATE, 40, 'active'),
('q0000000-0000-0000-0000-000000000003', 'd1000000-0000-0000-0000-000000000008', 'Laboratory', CURRENT_DATE, 18, 'active'),
('q0000000-0000-0000-0000-000000000004', 'd1000000-0000-0000-0000-000000000010', 'Billing', CURRENT_DATE, 32, 'active')
ON CONFLICT (department_id, service_type, queue_date) DO NOTHING;

-- 6. QUEUE ENTRIES (Cardiology Live Demo Scenario)
INSERT INTO queue_entries (id, queue_id, patient_id, token_number, token_code, status, estimated_wait_minutes, counter_number, joined_at, called_at, serving_at) VALUES
('e0000000-0000-0000-0000-000000000001', 'q0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000002', 21, 'C-21', 'serving', 0, 'Room 204', NOW() - INTERVAL '40 minutes', NOW() - INTERVAL '10 minutes', NOW() - INTERVAL '8 minutes'),
('e0000000-0000-0000-0000-000000000002', 'q0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000003', 22, 'C-22', 'called', 5, 'Room 204', NOW() - INTERVAL '35 minutes', NOW() - INTERVAL '2 minutes', NULL),
('e0000000-0000-0000-0000-000000000003', 'q0000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 27, 'C-27', 'waiting', 35, NULL, NOW() - INTERVAL '15 minutes', NULL, NULL)
ON CONFLICT (id) DO NOTHING;

-- 7. DEMO BILLS & PAYMENTS
INSERT INTO bills (id, patient_id, bill_number, consultation_fee, lab_fee, pharmacy_fee, registration_fee, other_charges, total_amount, payment_status) VALUES
('bil00000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'INV-2026-0891', 500.00, 300.00, 0.00, 100.00, 0.00, 900.00, 'unpaid'),
('bil00000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000002', 'INV-2026-0890', 500.00, 0.00, 250.00, 100.00, 0.00, 850.00, 'paid')
ON CONFLICT (id) DO NOTHING;

-- 8. DEMO LAB ORDERS
INSERT INTO lab_orders (id, patient_id, doctor_id, test_name, status, ordered_at, sample_collected_at, processing_at, report_ready_at, report_reference) VALUES
('lab00000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'doc00000-0000-0000-0000-000000000001', 'Complete Blood Count (CBC) & Lipid Profile', 'processing', NOW() - INTERVAL '2 hours', NOW() - INTERVAL '90 minutes', NOW() - INTERVAL '30 minutes', NULL, 'LAB-REP-CBC-8812'),
('lab00000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000002', 'doc00000-0000-0000-0000-000000000002', 'Serum Creatinine & Blood Urea', 'report_ready', NOW() - INTERVAL '1 day', NOW() - INTERVAL '23 hours', NOW() - INTERVAL '22 hours', NOW() - INTERVAL '20 hours', 'LAB-REP-CRE-7741')
ON CONFLICT (id) DO NOTHING;

-- 9. NOTIFICATIONS
INSERT INTO notifications (id, user_id, title, message, type, is_read) VALUES
('not00000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'Token C-27 Active', 'You joined Cardiology Queue. Estimated wait time is approximately 35 mins.', 'queue', false),
('not00000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 'Lab Order Initiated', 'Dr. Arun Kumar has ordered Complete Blood Count (CBC). Please visit the Laboratory on Ground Floor.', 'lab', false),
('not00000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 'Pending Invoice INV-2026-0891', 'An invoice of ₹900 is ready for digital clearance in the Billing section.', 'billing', true)
ON CONFLICT (id) DO NOTHING;

-- 10. COMPLETED QUEUE ENTRIES FOR WAITING HISTORY
INSERT INTO queue_entries (id, queue_id, patient_id, token_number, token_code, status, estimated_wait_minutes, joined_at, called_at, serving_at, completed_at, counter_number) VALUES
('e0000000-0000-0000-0000-000000000010', 'q0000000-0000-0000-0000-000000000002', 'c0000000-0000-0000-0000-000000000001', 14, 'GM-14', 'completed', 20, NOW() - INTERVAL '7 days 4 hours', NOW() - INTERVAL '7 days 3 hours 45 mins', NOW() - INTERVAL '7 days 3 hours 43 mins', NOW() - INTERVAL '7 days 3 hours 25 mins', 'Room 101'),
('e0000000-0000-0000-0000-000000000011', 'q0000000-0000-0000-0000-000000000003', 'c0000000-0000-0000-0000-000000000001', 8, 'LAB-08', 'completed', 15, NOW() - INTERVAL '14 days 3 hours', NOW() - INTERVAL '14 days 2 hours 48 mins', NOW() - INTERVAL '14 days 2 hours 45 mins', NOW() - INTERVAL '14 days 2 hours 30 mins', 'Counter 2')
ON CONFLICT (id) DO NOTHING;

-- 11. FEEDBACK
INSERT INTO feedback (id, patient_id, department_id, queue_entry_id, overall_rating, waiting_rating, staff_rating, doctor_rating, facility_rating, comment) VALUES
('fb000000-0000-0000-0000-000000000001', 'c0000000-0000-0000-0000-000000000001', 'd1000000-0000-0000-0000-000000000001', 'e0000000-0000-0000-0000-000000000010', 5, 4, 5, 5, 5, 'Quick digital token process. Dr. Priya was very attentive and compassionate!')
ON CONFLICT (id) DO NOTHING;
