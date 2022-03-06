import unittest
from src import app
import json
import time


class TestSmartContract(unittest.TestCase):
    def setUp(self):
        self.gth_public_key = '107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470'
        self.gth_private_key = "96281203938515529592468945178611699390852145171871882015412702005631509756531"
        self.user_1_public_key = "20814445768936213437274626353616804800165280588630009899878751548100521042725A19241468249812662668563130259817649756265743308017717653468619451285872265293"
        self.user_2_public_key = "45924479284721020088255655764259838493632121191345267194632595708284069229257A64353570746271633642239099441557900798355211921538755593764691886599926285870"
        self.user_1_private_key = "82071682867393694911507508357139147081659092296130835724380999832955540204790"
        self.user_2_private_key = "91731677430373908352199137307720571905361632738435022871770280430996789639289"
        
        self.app = app.test_client()

    def test_smarts_contracts(self):
        # GTH send 50 to user 1
        self.app.post('/transaction/new', json={
            "sender": self.gth_public_key,
            "recipient": self.user_1_public_key,
            "amount": 50, "token": "snowy",
            "private_key": self.gth_private_key})
        # GTH send 10 to user 2
        self.app.post('/transaction/new', json={
            "sender": self.gth_public_key,
            "recipient": self.user_2_public_key,
            "amount": 10, "token": "snowy",
            "private_key": self.gth_private_key})
        self.app.post('/create_block')
        self.app.get('/mine', follow_redirects=True)
        print('======= setup ended ========')
        print("user 1", self.app.get('/get_balance', json={'user_id': self.user_1_public_key}).get_data())
        print("user 2", self.app.get('/get_balance', json={'user_id': self.user_2_public_key}).get_data())
        print('============================')

        # User 1 send 50 to user 2 if user 2 send 10
        response = self.app.post('/transaction/new', json={
            "sender": self.user_1_public_key,
            "recipient": self.user_2_public_key,
            "amount": 50,
            "private_key": self.user_1_private_key,
            "token": "snowy",
            "sc": {
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_1_public_key,
                "sender": self.user_2_public_key,
                "amount": 10,
                "token": "snowy"
            }
        })

        self.assertEqual(response.status_code, 201)

        # User 2 send 10 to user 1 if user 1 send 50 to user 2
        response = self.app.post('/transaction/new', json={
            "sender": self.user_2_public_key,
            "recipient": self.user_1_public_key,
            "amount": 10,
            "private_key": self.user_2_private_key,
            "token": "snowy",
            "sc": {
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_2_public_key,
                "sender": self.user_1_public_key,
                "amount": 50,
                "token": "snowy"
            }
        })
        self.assertEqual(response.status_code, 201)

        response = self.app.post('/create_block')
        self.assertEqual(response.status_code, 200)
        self.app.get('/mine', follow_redirects=True)

        print("===== test smarts contracts END ======")
        print("user 1", self.app.get('/get_balance', json={'user_id': self.user_1_public_key}).get_data())
        print("user 2", self.app.get('/get_balance', json={'user_id': self.user_2_public_key}).get_data())
        print('======================================')

        response = self.app.get('/get_balance', json={'user_id': self.user_2_public_key})
        self.assertEqual(json.loads(response.get_data())['snowy'], 50)

        response = self.app.post('/get_balance_by_token', json={'user_id': self.user_2_public_key, 'token': 'snowy'})
        self.assertEqual(json.loads(response.get_data())['balance'], 50)

    def test_error(self):
        response = self.app.post('/transaction/new', json={
            "sender": self.user_1_public_key,
            "recipient": self.user_2_public_key,
            "amount": 10,
            "private_key": self.user_1_private_key,
            "token": "snowy",
            "sc": {
                "type": "OTHER_TX_CHECK",
                "sender": self.user_2_public_key,
                "amount": 50,
                "token": "snowy"
            }
        })
        self.assertEqual(response.status_code, 401)


if __name__ == '__main__':
    unittest.main()
