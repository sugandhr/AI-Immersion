-- ==============================================================================
-- SmartCare Queue AI - PostgreSQL Functions & Triggers
-- Concurrency-safe token generation, atomic queue management, and real-time alerts
-- ==============================================================================

-- 1. Automatic updated_at Trigger Function
CREATE OR REPLACE FUNCTION update_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_profiles_updated
    BEFORE UPDATE ON profiles
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE OR REPLACE TRIGGER trg_doctors_updated
    BEFORE UPDATE ON doctors
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE OR REPLACE TRIGGER trg_queues_updated
    BEFORE UPDATE ON queues
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

CREATE OR REPLACE TRIGGER trg_appointments_updated
    BEFORE UPDATE ON appointments
    FOR EACH ROW EXECUTE FUNCTION update_timestamp();

-- ------------------------------------------------------------------------------
-- 2. CONCURRENCY-SAFE ATOMIC TOKEN GENERATOR
-- Uses FOR UPDATE row-locking on the queues table to prevent race conditions
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION generate_queue_token(
    p_department_id UUID,
    p_service_type VARCHAR,
    p_patient_id UUID,
    p_doctor_id UUID DEFAULT NULL
)
RETURNS TABLE (
    entry_id UUID,
    queue_id UUID,
    token_number INTEGER,
    token_code VARCHAR,
    estimated_wait INTEGER,
    patients_ahead BIGINT,
    status VARCHAR
) AS $$
DECLARE
    v_queue_id UUID;
    v_next_token INTEGER;
    v_prefix VARCHAR(5);
    v_token_code VARCHAR(30);
    v_active_doctors INTEGER;
    v_avg_consultation INTEGER;
    v_patients_ahead BIGINT;
    v_estimated_wait INTEGER;
    v_entry_id UUID;
BEGIN
    -- Check if patient already has an active waiting or serving entry in this queue
    SELECT qe.id INTO v_entry_id
    FROM queue_entries qe
    JOIN queues q ON q.id = qe.queue_id
    WHERE qe.patient_id = p_patient_id
      AND q.department_id = p_department_id
      AND q.service_type = p_service_type
      AND q.queue_date = CURRENT_DATE
      AND qe.status IN ('waiting', 'called', 'serving')
    LIMIT 1;

    IF v_entry_id IS NOT NULL THEN
        RAISE EXCEPTION 'Patient already has an active token in this queue.';
    END IF;

    -- Retrieve or initialize today's queue for this department & service
    -- Uses INSERT ... ON CONFLICT to avoid duplicate queue master rows
    INSERT INTO queues (department_id, service_type, queue_date, current_token_number, status)
    VALUES (p_department_id, p_service_type, CURRENT_DATE, 0, 'active')
    ON CONFLICT (department_id, service_type, queue_date) DO NOTHING;

    -- Lock the queue record for this department/service for update
    SELECT q.id, q.current_token_number INTO v_queue_id, v_next_token
    FROM queues q
    WHERE q.department_id = p_department_id
      AND q.service_type = p_service_type
      AND q.queue_date = CURRENT_DATE
    FOR UPDATE;

    -- Calculate next token number atomically
    v_next_token := v_next_token + 1;

    -- Update current token number on master queue
    UPDATE queues
    SET current_token_number = v_next_token,
        updated_at = NOW()
    WHERE id = v_queue_id;

    -- Retrieve department prefix for token formatting (e.g. C, GM, O, P)
    SELECT code_prefix INTO v_prefix
    FROM departments
    WHERE id = p_department_id;

    IF v_prefix IS NULL THEN
        v_prefix := 'Q';
    END IF;

    v_token_code := v_prefix || '-' || LPAD(v_next_token::TEXT, 2, '0');

    -- Count active doctors in this department
    SELECT COUNT(*), COALESCE(AVG(average_consultation_minutes)::INTEGER, 15)
    INTO v_active_doctors, v_avg_consultation
    FROM doctors
    WHERE department_id = p_department_id
      AND status = 'available';

    IF v_active_doctors = 0 THEN
        v_active_doctors := 1;
    END IF;

    -- Count waiting patients ahead
    SELECT COUNT(*) INTO v_patients_ahead
    FROM queue_entries
    WHERE queue_entries.queue_id = v_queue_id
      AND queue_entries.status = 'waiting';

    -- AI Wait-time estimation formula
    -- Estimated Wait = (Patients Ahead * Avg Service Time) / Active Doctors
    v_estimated_wait := CEIL((v_patients_ahead * v_avg_consultation)::NUMERIC / v_active_doctors);
    IF v_estimated_wait < 5 THEN
        v_estimated_wait := 5; -- Base baseline buffer
    END IF;

    -- Insert new queue entry
    INSERT INTO queue_entries (
        queue_id,
        patient_id,
        doctor_id,
        token_number,
        token_code,
        status,
        estimated_wait_minutes
    )
    VALUES (
        v_queue_id,
        p_patient_id,
        p_doctor_id,
        v_next_token,
        v_token_code,
        'waiting',
        v_estimated_wait
    )
    RETURNING queue_entries.id INTO v_entry_id;

    -- Auto notification for queue join
    INSERT INTO notifications (user_id, title, message, type)
    VALUES (
        p_patient_id,
        'Queue Joined: ' || v_token_code,
        'You have joined the queue. Your token is ' || v_token_code || '. Estimated waiting time is ' || v_estimated_wait || ' minutes (' || v_patients_ahead || ' patients ahead).',
        'queue'
    );

    RETURN QUERY
    SELECT 
        v_entry_id,
        v_queue_id,
        v_next_token,
        v_token_code,
        v_estimated_wait,
        v_patients_ahead,
        'waiting'::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- ------------------------------------------------------------------------------
-- 3. TRIGGER FOR NOTIFYING PATIENT WHEN TOKEN IS CALLED
-- ------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION notify_token_called()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'called' AND OLD.status <> 'called' THEN
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (
            NEW.patient_id,
            'Token ' || NEW.token_code || ' Called!',
            'Your token ' || NEW.token_code || ' is now being called! Please proceed immediately to ' || COALESCE(NEW.counter_number, 'the consultation counter') || '.',
            'queue'
        );
    ELSIF NEW.status = 'completed' AND OLD.status <> 'completed' THEN
        INSERT INTO notifications (user_id, title, message, type)
        VALUES (
            NEW.patient_id,
            'Visit Completed',
            'Your consultation for token ' || NEW.token_code || ' has been completed. Thank you for choosing SmartCare!',
            'queue'
        );
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE OR REPLACE TRIGGER trg_queue_entry_status_notify
    AFTER UPDATE ON queue_entries
    FOR EACH ROW EXECUTE FUNCTION notify_token_called();
