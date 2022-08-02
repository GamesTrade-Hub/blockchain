import unittest
import json

from blockchain.server import app


class TestNodes(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.get('/start')

    def test_mining_chain_result(self):
        response = self.app.get('/get_new_private_key')
        private_key = json.loads(response.get_data())['key']
        self.assertEqual(201, response.status_code)

        response = self.app.get('/get_new_public_key', json={"private_key": private_key})
        self.assertEqual(201, response.status_code)

        response = self.app.get('/get_new_public_key')
        self.assertEqual(400, response.status_code)

        response = self.app.get('/get_new_public_key', json={})
        self.assertEqual(400, response.status_code)

        response = self.app.post('/transaction/new', json={"sender": "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470", "recipient": "20814445768936213437274626353616804800165280588630009899878751548100521042725A19241468249812662668563130259817649756265743308017717653468619451285872265293", "amount": 50, "token": "ETH", "private_key": "96281203938515529592468945178611699390852145171871882015412702005631509756531"})
        self.assertEqual(201, response.status_code)


if __name__ == '__main__':
    unittest.main()
