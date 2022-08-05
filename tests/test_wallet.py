import unittest
from src.blockchain.server import app
import json
import time

from tests.testing_tools import BlockchainTestTools


class TestWallet(BlockchainTestTools):
    def setUp(self):
        super(TestWallet, self).setUp()

        self.new_transaction(
            sender=self.gth_public_key,
            recipient=self.user_2_public_key,
            amount=50,
            token="BNB",
            private_key=self.gth_private_key,
            check_block_created=True
        )

    def test_balance_generic_method(self):
        self.check_balance_is_correct(self.user_2_public_key, "BNB", 50)

    def check_balance_method_specific_token(self):
        response = self._app.get(
            "/get_balance",
            json={
                "user_id": self.user_2_public_key,
                "token": "BNB",
            },
        )
        self.assertEqual(json.loads(response.get_data()), 50, msg=response.get_data())

    def check_balance_method_all_tokens(self):
        response = self._app.get(
            "/get_balance",
            json={
                "user_id": self.user_2_public_key,
            },
        )
        self.assertEqual(json.loads(response.get_data())['BNB'], 50, msg=response.get_data())

    def test_error(self):
        response = self._app.post("/transaction/new", json={})
        self.assertEqual(response.status_code, 400)
        response = self._app.get("/get_balance", json={})
        self.assertEqual(response.status_code, 400)


if __name__ == "__main__":
    unittest.main()
