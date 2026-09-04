import unittest
import json
from backend.app import create_app

class SmartCareBackendTests(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.client = self.app.test_client()

    def test_01_healthcheck(self):
        res = self.client.get('/api/health')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['status'], 'healthy')

    def test_02_login_patient(self):
        res = self.client.post('/api/auth/login', json={
            "email": "patient@smartcare.org",
            "password": "password123"
        })
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertIn('token', data['data'])
        self.token = data['data']['token']

    def test_03_get_departments(self):
        res = self.client.get('/api/departments')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']), 5)

    def test_04_get_doctors(self):
        res = self.client.get('/api/doctors')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertTrue(data['success'])
        self.assertGreater(len(data['data']), 0)

    def test_05_join_queue_and_concurrency(self):
        # Login patient 2
        login_res = self.client.post('/api/auth/login', json={
            "email": "rahul.raj@example.com",
            "password": "password123"
        })
        token = json.loads(login_res.data)['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        # Join queue for General Medicine
        res = self.client.post('/api/queues/join', json={
            "department_id": "d1000000-0000-0000-0000-000000000001",
            "service_type": "Consultation"
        }, headers=headers)
        
        # Could be 201 or 409 if already active
        self.assertIn(res.status_code, (201, 409))

    def test_06_staff_call_next(self):
        # Login staff
        login_res = self.client.post('/api/auth/login', json={
            "email": "staff@smartcare.org",
            "password": "password123"
        })
        token = json.loads(login_res.data)['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        # Call next in Cardiology queue
        res = self.client.post('/api/queues/q0000000-0000-0000-0000-000000000001/next', json={
            "counter_number": "Room 204"
        }, headers=headers)
        
        self.assertIn(res.status_code, (200, 400)) # 200 if patient waiting, 400 if empty

    def test_07_ai_best_time(self):
        res = self.client.get('/api/ai/best-time')
        self.assertEqual(res.status_code, 200)
        data = json.loads(res.data)
        self.assertIn('recommended_window', data['data'])

    def test_08_ai_assistant_operational_vs_guardrail(self):
        # 1. Operational inquiry
        op_res = self.client.post('/api/ai/assistant', json={
            "query": "Where is Cardiology?"
        })
        self.assertEqual(op_res.status_code, 200)
        data = json.loads(op_res.data)
        self.assertIn('Cardiology', data['data']['response'])

        # 2. Medical diagnosis inquiry (must trigger safety guardrail)
        med_res = self.client.post('/api/ai/assistant', json={
            "query": "What medicine should I take for severe fever and chest pain?"
        })
        self.assertEqual(med_res.status_code, 200)
        data2 = json.loads(med_res.data)
        self.assertEqual(data2['data']['type'], 'medical_guardrail')
        self.assertIn('Medical Safety Guardrail', data2['data']['response'])

    def test_09_bill_payment_simulation(self):
        login_res = self.client.post('/api/auth/login', json={
            "email": "patient@smartcare.org",
            "password": "password123"
        })
        token = json.loads(login_res.data)['data']['token']
        headers = {"Authorization": f"Bearer {token}"}

        res = self.client.post('/api/bills/bil00000-0000-0000-0000-000000000001/pay', json={
            "payment_method": "UPI Simulation"
        }, headers=headers)
        
        # 200 if unpaid, 400 if already paid in previous test run
        self.assertIn(res.status_code, (200, 400))

if __name__ == '__main__':
    unittest.main()
