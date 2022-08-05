import unittest
from src.blockchain.server import app
import json
import time


class TestWallet(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_balance(self):
        response = self.app.get("/status")
        self.assertEqual(response.status_code, 200)
        response = self.app.post(
            "/transaction/new",
            json={
                "sender": "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470",
                "recipient": "45924479284721020088255655764259838493632121191345267194632595708284069229257A64353570746271633642239099441557900798355211921538755593764691886599926285870",
                "amount": 50,
                "token": "BNB",
                "private_key": "96281203938515529592468945178611699390852145171871882015412702005631509756531",
            },
        )
        self.assertEqual(response.status_code, 201)
        time.sleep(1)  # Need this to be sure that last transaction is included

        response = self.app.post("/block/new", json={})
        self.assertEqual(response.status_code, 200)
        self.app.get("/mine", follow_redirects=True)

        response = self.app.get(
            "/get_balance",
            json={
                "user_id": "45924479284721020088255655764259838493632121191345267194632595708284069229257A64353570746271633642239099441557900798355211921538755593764691886599926285870"
            },
        )
        self.assertEqual(json.loads(response.get_data())["BNB"], 50)

        response = self.app.post(
            "/get_balance_by_token",
            json={
                "user_id": "45924479284721020088255655764259838493632121191345267194632595708284069229257A64353570746271633642239099441557900798355211921538755593764691886599926285870",
                "token": "BNB",
            },
        )
        self.assertEqual(json.loads(response.get_data())["balance"], 50)

    def test_error(self):
        response = self.app.post("/transaction/new", json={})
        self.assertEqual(response.status_code, 400)
        response = self.app.post("/get_balance_by_token", json={})
        self.assertEqual(response.status_code, 400)
        response = self.app.get("/get_balance", json={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
