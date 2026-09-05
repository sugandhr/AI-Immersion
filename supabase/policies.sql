-- ==============================================================================
-- SmartCare Queue AI - Row Level Security (RLS) Policies
-- Enforces strict role-based access control directly in PostgreSQL.
-- Patients can NEVER read or modify other patients' private records.
-- Idempotent script: Safe to execute repeatedly (DROP POLICY IF EXISTS).
-- ==============================================================================

-- Enable RLS on all tables (safe to run multiple times)
ALTER TABLE profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE doctors ENABLE ROW LEVEL SECURITY;
ALTER TABLE queues ENABLE ROW LEVEL SECURITY;
ALTER TABLE queue_entries ENABLE ROW LEVEL SECURITY;
ALTER TABLE appointments ENABLE ROW LEVEL SECURITY;
ALTER TABLE lab_orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE bills ENABLE ROW LEVEL SECURITY;
ALTER TABLE payments ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE hospital_locations ENABLE ROW LEVEL SECURITY;
ALTER TABLE priority_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedback ENABLE ROW LEVEL SECURITY;

-- ------------------------------------------------------------------------------
-- Helper Security Functions: Get Authenticated User Profile & Role
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.current_profile_id()
RETURNS UUID AS $$
    SELECT id FROM public.profiles WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

CREATE OR REPLACE FUNCTION public.current_user_role()
RETURNS VARCHAR AS $$
    SELECT role FROM public.profiles WHERE auth_user_id = auth.uid() LIMIT 1;
$$ LANGUAGE sql STABLE SECURITY DEFINER;

-- ==============================================================================
-- 1. PROFILES POLICIES
-- ==============================================================================
-- Users can view their own profile
DROP POLICY IF EXISTS "Users can view own profile" ON profiles;
CREATE POLICY "Users can view own profile"
    ON profiles FOR SELECT
    USING (auth.uid() = auth_user_id OR current_user_role() IN ('staff', 'doctor', 'admin'));

-- Users can update their own profile
DROP POLICY IF EXISTS "Users can update own profile" ON profiles;
CREATE POLICY "Users can update own profile"
    ON profiles FOR UPDATE
    USING (auth.uid() = auth_user_id)
    WITH CHECK (auth.uid() = auth_user_id);

-- System/Admins can insert and manage all profiles
DROP POLICY IF EXISTS "Admins manage profiles" ON profiles;
CREATE POLICY "Admins manage profiles"
    ON profiles FOR ALL
    USING (current_user_role() = 'admin');

-- Allow authenticated users to insert their initial profile upon registration
DROP POLICY IF EXISTS "Users can insert own profile" ON profiles;
CREATE POLICY "Users can insert own profile"
    ON profiles FOR INSERT
    WITH CHECK (auth.uid() = auth_user_id);

-- ==============================================================================
-- 2. DEPARTMENTS POLICIES (Public read, staff/admin manage)
-- ==============================================================================
DROP POLICY IF EXISTS "Anyone can view active departments" ON departments;
CREATE POLICY "Anyone can view active departments"
    ON departments FOR SELECT
    USING (active = TRUE OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Staff and admin manage departments" ON departments;
CREATE POLICY "Staff and admin manage departments"
    ON departments FOR ALL
    USING (current_user_role() IN ('staff', 'admin'));

-- ==============================================================================
-- 3. DOCTORS POLICIES (Public read, staff/admin/doctor manage)
-- ==============================================================================
DROP POLICY IF EXISTS "Anyone can view doctors" ON doctors;
CREATE POLICY "Anyone can view doctors"
    ON doctors FOR SELECT
    USING (TRUE);

DROP POLICY IF EXISTS "Doctors can update their own status" ON doctors;
CREATE POLICY "Doctors can update their own status"
    ON doctors FOR UPDATE
    USING (profile_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Admins manage doctors" ON doctors;
CREATE POLICY "Admins manage doctors"
    ON doctors FOR ALL
    USING (current_user_role() = 'admin');

-- ==============================================================================
-- 4. QUEUES POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "Anyone can view daily queue summary" ON queues;
CREATE POLICY "Anyone can view daily queue summary"
    ON queues FOR SELECT
    USING (TRUE);

DROP POLICY IF EXISTS "Staff manage queues" ON queues;
CREATE POLICY "Staff manage queues"
    ON queues FOR ALL
    USING (current_user_role() IN ('staff', 'admin'));

-- ==============================================================================
-- 5. QUEUE ENTRIES POLICIES
-- ==============================================================================
-- Patients can view their own queue entries; Staff/Doctors/Admins can view all entries for operational counters
DROP POLICY IF EXISTS "Patients view own queue entries or staff view all" ON queue_entries;
CREATE POLICY "Patients view own queue entries or staff view all"
    ON queue_entries FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'doctor', 'admin'));

-- Patients can join queue for themselves
DROP POLICY IF EXISTS "Patients can join queue" ON queue_entries;
CREATE POLICY "Patients can join queue"
    ON queue_entries FOR INSERT
    WITH CHECK (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

-- Patients can cancel their own waiting queue entry
DROP POLICY IF EXISTS "Patients cancel own entry" ON queue_entries;
CREATE POLICY "Patients cancel own entry"
    ON queue_entries FOR UPDATE
    USING (patient_id = current_profile_id() AND status = 'waiting')
    WITH CHECK (patient_id = current_profile_id() AND status = 'cancelled');

-- Staff/Doctors can call, skip, serve, complete queue entries
DROP POLICY IF EXISTS "Staff and doctors update queue entries" ON queue_entries;
CREATE POLICY "Staff and doctors update queue entries"
    ON queue_entries FOR UPDATE
    USING (current_user_role() IN ('staff', 'doctor', 'admin'));

-- ==============================================================================
-- 6. APPOINTMENTS POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "View appointments" ON appointments;
CREATE POLICY "View appointments"
    ON appointments FOR SELECT
    USING (
        patient_id = current_profile_id() 
        OR doctor_id IN (SELECT id FROM doctors WHERE profile_id = current_profile_id())
        OR current_user_role() IN ('staff', 'admin')
    );

DROP POLICY IF EXISTS "Patients can book appointments" ON appointments;
CREATE POLICY "Patients can book appointments"
    ON appointments FOR INSERT
    WITH CHECK (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Patients and staff update appointments" ON appointments;
CREATE POLICY "Patients and staff update appointments"
    ON appointments FOR UPDATE
    USING (
        patient_id = current_profile_id() 
        OR doctor_id IN (SELECT id FROM doctors WHERE profile_id = current_profile_id())
        OR current_user_role() IN ('staff', 'admin')
    );

-- ==============================================================================
-- 7. LAB ORDERS POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "Patients view own lab orders" ON lab_orders;
CREATE POLICY "Patients view own lab orders"
    ON lab_orders FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'doctor', 'admin'));

DROP POLICY IF EXISTS "Staff and doctors manage lab orders" ON lab_orders;
CREATE POLICY "Staff and doctors manage lab orders"
    ON lab_orders FOR ALL
    USING (current_user_role() IN ('staff', 'doctor', 'admin'));

-- ==============================================================================
-- 8. BILLS & PAYMENTS POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "Patients view own bills" ON bills;
CREATE POLICY "Patients view own bills"
    ON bills FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Staff manage bills" ON bills;
CREATE POLICY "Staff manage bills"
    ON bills FOR ALL
    USING (current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Patients view own payments" ON payments;
CREATE POLICY "Patients view own payments"
    ON payments FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Patients insert payments for their own bills" ON payments;
CREATE POLICY "Patients insert payments for their own bills"
    ON payments FOR INSERT
    WITH CHECK (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

-- ==============================================================================
-- 9. NOTIFICATIONS POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "Users view own notifications" ON notifications;
CREATE POLICY "Users view own notifications"
    ON notifications FOR SELECT
    USING (user_id = current_profile_id());

DROP POLICY IF EXISTS "Users update own notifications" ON notifications;
CREATE POLICY "Users update own notifications"
    ON notifications FOR UPDATE
    USING (user_id = current_profile_id());

DROP POLICY IF EXISTS "System and staff insert notifications" ON notifications;
CREATE POLICY "System and staff insert notifications"
    ON notifications FOR INSERT
    WITH CHECK (TRUE);

-- ==============================================================================
-- 10. HOSPITAL LOCATIONS POLICIES (Public read)
-- ==============================================================================
DROP POLICY IF EXISTS "Anyone can view hospital locations" ON hospital_locations;
CREATE POLICY "Anyone can view hospital locations"
    ON hospital_locations FOR SELECT
    USING (TRUE);

DROP POLICY IF EXISTS "Admin manage hospital locations" ON hospital_locations;
CREATE POLICY "Admin manage hospital locations"
    ON hospital_locations FOR ALL
    USING (current_user_role() = 'admin');

-- ==============================================================================
-- 11. PRIORITY REQUESTS POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "View priority requests" ON priority_requests;
CREATE POLICY "View priority requests"
    ON priority_requests FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));

DROP POLICY IF EXISTS "Patients submit priority requests" ON priority_requests;
CREATE POLICY "Patients submit priority requests"
    ON priority_requests FOR INSERT
    WITH CHECK (patient_id = current_profile_id());

DROP POLICY IF EXISTS "Staff review priority requests" ON priority_requests;
CREATE POLICY "Staff review priority requests"
    ON priority_requests FOR UPDATE
    USING (current_user_role() IN ('staff', 'admin'));

-- ==============================================================================
-- 12. FEEDBACK POLICIES
-- ==============================================================================
DROP POLICY IF EXISTS "Patients create feedback" ON feedback;
CREATE POLICY "Patients create feedback"
    ON feedback FOR INSERT
    WITH CHECK (patient_id = current_profile_id());

DROP POLICY IF EXISTS "Patients view own feedback or staff view all" ON feedback;
CREATE POLICY "Patients view own feedback or staff view all"
    ON feedback FOR SELECT
    USING (patient_id = current_profile_id() OR current_user_role() IN ('staff', 'admin'));
