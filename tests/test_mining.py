import unittest
from src import app
import json


class TestMining(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_first_node(self):
        response = self.app.get('/chain')
        self.assertEqual(json.loads(response.get_data())['length'], 1)
        self.assertEqual(response.status_code, 200)

    def test_mining(self):
        response = self.app.post('/create_block')
        print("test_mining", response.get_data())
        self.assertEqual(response.status_code, 200)

        self.app.get('/mine', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

    def test_mining_chain_result(self):
        response = self.app.get('/chain')
        bc_len = json.loads(response.get_data())['length']

        response = self.app.post('/create_block')
        print("create_block response", json.loads(response.get_data()))

        self.app.get('/mine', follow_redirects=True)

        response = self.app.get('/chain')
        self.assertEqual(json.loads(response.get_data())['length'], 1 + bc_len)


if __name__ == '__main__':
    unittest.main()
