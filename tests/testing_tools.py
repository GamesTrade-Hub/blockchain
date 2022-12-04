import os
import unittest
from typing import Optional

from flask.testing import FlaskClient

from src.blockchain.server import app
import json
import time


class BlockchainTestTools(unittest.TestCase):
    def setUp(self):
        self._app = app.test_client()
        self.gth_public_key = "798f62356605804e81754ba5ba552c813df77ec193a5c71426655ab34919b9a827604971e16d26f2e8d7d9926f8e8d7d44acd9db9eb2b11f80ed45ec335c9ab09e6c9b7d2b5d294cab7ea6d052d470bda0c03713c0e28311531df330092b94a4aa9ebd0df6cf0425383e6d3c9249c4501c8071e7a3da0a162c684894dec43681e637d26ba11a419fed162af02555ef7f8f750a986bac5a302491dc87b2f515db336573822de39ff2191e00GTH"
        self.gth_private_key = os.environ["PV_GTH"]
        self.token_admin_pb = "d7501dd42e4137b564605a5ca18cdbc7e58ee8dcc23d87f31593b3a60f2b7b05f0f5ec553ec61544a60d4543044b1c24f7820e45106e79db80ad25a5fd21c437d8e847ac3c0f7bd0d5071fbcb28240a300c6aee1ba86870bfa38f2fe9a9f74fa0463c7a7712a2d4ad4263fb98a632b25b9808d51975e95462eb0df9c6006e97ffcbb7e5da1b7d62d2eb7070adf20fe5d2666ea14399c3b9a24a387db6553a8feff21faeee9f40dcaab0a00ADMINPASS"
        self.token_admin_pv = os.environ["PV_ADMIN"]
        self.user_1_public_key = "a76338db18ffb9e278399cf7625b3efbe724f8d629ce934dabaef32ea4c524615614a84a4b1593f309da027d17b5fc5f28b37d232b201d820022f0eea3e86b056705f94fc01f0b17b73714bb08dd0260a70c515918e7aa84f8238d802730d7b686a108f51df6881fe80baa4ca19895b56a00856d6bbf33fe9ce0c4963654b65611f93a1331d97924ecb9ce625662529985e5dcb94a3321c2d69897db7dedf38a805ec8c5a20d7af56c0800casual"
        self.user_2_public_key = "0f8a9138a5cf7522af811c8157eaddfcbdfcc2cb426e1ad968b5e0d5f896bbd8a6ba1d36fc8ebb6ee0eb5e418951da8719d6eac55d7fc9a38017d96e655cf1073322e845a28c8370bcc1ac7326b185e9718a4c28373688b8b0836912b5450b028ec028cd59ab6d27654482a210b6506d75009abaf3ad6a9842353cc9780974ac416e0e5aca156d0a1c8dfb8d025bbf1125f884aed4c67412b585c7f42af1c6d8cab5c065d221b904e60500casual"
        self.user_1_private_key = "208870bc2357467125079a396e9bf73e0cc96d9435a484ba07458262c146a026d20d7722518f628177550afa06152b65bddea771aaa3595d9c"
        self.user_2_private_key = "0055d79bcce3e5e330c745129a9112aba2c9ad2024ea68976ce89ad1c6251275d1c526d6a40be008a47e629b48b8f623d83796ecdfab2bca06"
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
        new_balance: float = self.get_balance_token(user_public_key, token)
        self.assertEqual(new_balance, 0)

    def give_to_user(self, user_id, amount, token):
        self.new_transaction(
            sender=self.token_admin_pb,
            recipient=user_id,
            amount=amount,
            token=token,
            private_key=self.token_admin_pv,
        )

    def new_transaction(
        self,
        sender,
        recipient,
        amount,
        token,
        private_key,
        smart_contract: Optional[dict] = None,
        check_block_created: bool = False,
        check_block_not_created: bool = False,
    ):
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

