import unittest
from src import app
import json


class TestNodes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.get('/start')

    def test_mining_chain_result(self):
        response = self.app.get('/chain')
        bc_len = json.loads(response.get_data())['length']

        response = self.app.post('/nodes/register', json={})
        self.assertEqual(response.status_code, 400)
        response = self.app.post('/nodes/register', json={"nodes": ["127.0.0.1:5002"]})
        self.assertEqual(response.status_code, 201)
        response = self.app.get('/nodes/list')
        self.assertEqual(response.status_code, 200)
        response = self.app.post('/transaction/new', json={"sender": "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470", "recipient": "20814445768936213437274626353616804800165280588630009899878751548100521042725A19241468249812662668563130259817649756265743308017717653468619451285872265293", "amount": 50, "token": "ETH", "private_key": "96281203938515529592468945178611699390852145171871882015412702005631509756531"})
        self.assertEqual(response.status_code, 201)

        self.app.post('/create_block')

        self.app.get('/mine', follow_redirects=True)

        response = self.app.get('/nodes/resolve', follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.app.get('/chain')
        self.assertEqual(json.loads(response.get_data())['length'], 1 + bc_len)


if __name__ == '__main__':
    unittest.main()
