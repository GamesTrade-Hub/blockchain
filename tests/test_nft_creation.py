import json
import os
import unittest

from src.blockchain.server import app


class TestNFTCreation(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.gth_keys = {
            "public": "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470",
            "private": "96281203938515529592468945178611699390852145171871882015412702005631509756531",
        }
        self.client_a_keys = {
            "public": "38432972238024851962163609910587920305303160517512456633372504071009136841752A22963103105905487550831827968376830879853793424696572571047463764104281739701",
            "private": "75237105199308912530117775203298758014410171640449738360284520682729982323908",
        }

    def test_nft_creation(self):
        token_name = "ETH"
        response = self.client.post(
            "/create_nft",
            json={
                "recipient": self.client_a_keys["public"],
                "sender": self.gth_keys["public"],
                "gth_private_key": self.gth_keys["private"],
                "token": token_name,
            },
        )
        response_json = json.loads(response.get_data(as_text=True))
        print(f"{response_json=}")
        self.assertEqual(
            201,
            response.status_code,
            msg=f"NFT creation failed {response_json['message'] if 'message' in response_json else ''}",
        )
        print(f"{response_json['id']=}")
        self.assertTrue(response_json["id"].startswith("nft_"))
        self.assertTrue(response_json["id"].endswith(token_name))

    def test_missing_keys(self):
        response = self.client.post("/create_nft", json={})
        print(f"{response.get_data(as_text=True)=}")
        self.assertEqual(401, response.status_code)

    def test_wrong_arguments(self):
        response = self.client.post(
            "/create_nft",
            json={
                "recipient": self.gth_keys["public"],
                "sender": self.gth_keys["public"],
                "gth_private_key": self.gth_keys["private"],
            },
        )
        self.assertEqual(401, response.status_code)


if __name__ == "__main__":
    unittest.main()
