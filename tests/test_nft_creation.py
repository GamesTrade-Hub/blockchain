import json
import os
import unittest
from src import app


class TestNFTCreation(unittest.TestCase):
    def setUp(self):
        self.ctx = app.app_context()
        self.ctx.push()
        self.client = app.test_client()
        self.gth_keys = {
            "public": "107586176969073111214138186621388472896166149958805892498797251438836201351897A74644521699183317518461259885566371696845701675874024848140772236522116872470",
            "private": os.environ.get("GTH_PRIVATE_KEY_TEST")
        }
        self.client_a_keys = {
            "public": "38432972238024851962163609910587920305303160517512456633372504071009136841752A22963103105905487550831827968376830879853793424696572571047463764104281739701",
            "private": "75237105199308912530117775203298758014410171640449738360284520682729982323908"
        }

    def test_nft_creation(self):
        response = self.client.post(
            "/transaction/create_nft",
            data=json.dumps({
                "recipient": self.client_a_keys["public"],
                "sender": self.gth_keys["public"],
                "private_key": self.gth_keys["private"]
            }),
            content_type="application/json"
        )
        response_json = json.loads(response.get_data(as_text=True))
        print(response_json)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response_json["message"], "Transaction will be added, Reason: ok")
        self.assertEqual(len(response_json["token"]), 40)

    def test_missing_keys(self):
        response = self.client.post(
            "/transaction/create_nft",
            data=json.dumps({
            }),
            content_type="application/json"
        )
        self.assertEqual(response.status_code, 400)


if __name__ == '__main__':
    unittest.main()
