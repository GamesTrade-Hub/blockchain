import unittest
from typing import Optional

from flask.testing import FlaskClient

from src.blockchain.server import app
import json
import time


class BlockchainTestTools(unittest.TestCase):
    def setUp(self):
        self._app = app.test_client()
        self.gth_public_key = "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470"
        self.gth_private_key = "96281203938515529592468945178611699390852145171871882015412702005631509756531"
        self.user_1_public_key = "20814445768936213437274626353616804800165280588630009899878751548100521042725A19241468249812662668563130259817649756265743308017717653468619451285872265293"
        self.user_2_public_key = "45924479284721020088255655764259838493632121191345267194632595708284069229257A64353570746271633642239099441557900798355211921538755593764691886599926285870"
        self.user_1_private_key = "82071682867393694911507508357139147081659092296130835724380999832955540204790"
        self.user_2_private_key = "91731677430373908352199137307720571905361632738435022871770280430996789639289"
        return self._app

    @property
    def app(self) -> FlaskClient:
        return self._app

    def get_balance_token(self, user_id, token) -> float:
        response = self._app.get(
            "/get_balance", json={"user_id": user_id, "token": token}
        )
        return json.loads(response.get_data())

    def check_balance_is_correct(self, user_id, token, amount):
        balance: float = self.get_balance_token(user_id, token)
        self.assertEqual(balance, amount)

    def empty_wallet(self, user_private_key, user_public_key, token):
        balance: float = self.get_balance_token(user_public_key, token)
        if balance > 0:
            response = self._app.post(
                "/transaction/new",
                json={
                    "sender": user_public_key,
                    "recipient": self.gth_public_key,
                    "amount": balance,
                    "token": token,
                    "private_key": user_private_key,
                },
            )
            self.assertEqual(201, response.status_code)
            response = self._app.post("/block/new", json={})
            self.assertEqual(200, response.status_code)
        new_balance: float = self.get_balance_token(user_public_key, token)
        self.assertEqual(new_balance, 0)

    def give_to_user(self, user_id, amount, token):
        response = self._app.post(
            "/transaction/new",
            json={
                "sender": self.gth_public_key,
                "recipient": user_id,
                "amount": amount,
                "token": token,
                "private_key": self.gth_private_key,
            },
        )
        self.assertEqual(response.status_code, 201)
        self._app.post("/block/new", json={})

    def new_transaction(self, sender, recipient, amount, token, private_key, smart_contract: Optional[dict] = None,
                        check_block_created: bool = False, check_block_not_created: bool = False):
        response = self._app.post(
            "/transaction/new",
            json={
                "sender": sender,
                "recipient": recipient,
                "amount": amount,
                "token": token,
                "private_key": private_key,
                "smart_contract": smart_contract,
            },
        )
        print(f"{response.status_code} {response.get_data()=}")
        self.assertEqual(response.status_code, 201, msg=response.get_data())
        response = self._app.post("/block/new", json={})
        if check_block_created:
            self.assertEqual(response.status_code, 200, msg=response.get_data())
        if check_block_not_created:
            self.assertEqual(response.status_code, 401, msg=response.get_data())
