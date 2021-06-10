import unittest
from src import app
import json


class TestMining(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.mine_count = 10

    def test_first_node(self):
        response = self.app.get('/chain')
        self.assertEqual(json.loads(response.get_data())['length'], 1)

    def test_mining(self):
        for i in range(self.mine_count):
            response = self.app.get('/mine', follow_redirects=True)
            self.assertEqual(response.status_code, 200)

    def test_mining_chain_result(self):
        response = self.app.get('/chain')
        bc_len = json.loads(response.get_data())['length']
        for i in range(self.mine_count):
            self.app.get('/mine', follow_redirects=True)
        response = self.app.get('/chain')
        self.assertEqual(json.loads(response.get_data())['length'], self.mine_count + bc_len)


if __name__ == '__main__':
    unittest.main()
