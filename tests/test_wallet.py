import unittest
from src import app
import json
import time


class TestMining(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.get('/start')

    def test_balance(self):
        response = self.app.get('/status')
        self.assertEqual(response.status_code, 201)
        response = self.app.post('/transaction/new', json={"sender": "Cyprien", "recipient": "William", "amount": 50})
        self.assertEqual(response.status_code, 201)
        response = self.app.post('/transaction/new', json={"sender": "William", "recipient": "Cyprien", "amount": 30})
        self.assertEqual(response.status_code, 201)
        response = self.app.post('/transaction/new', json={"sender": "William", "recipient": "Cyprien", "amount": 1})
        self.assertEqual(response.status_code, 201)
        time.sleep(1)  # Need this to be sure that last transaction is included

        response = self.app.post('/create_block')
        self.assertEqual(response.status_code, 200)
        self.app.get('/mine', follow_redirects=True)

        response = self.app.get('/get_balance', json={'user_id': 'William'})
        self.assertEqual(json.loads(response.get_data())['balance'], 19)


if __name__ == '__main__':
    unittest.main()
