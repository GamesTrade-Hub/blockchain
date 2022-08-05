import json
import os
import unittest

from src.blockchain.server import app
from tests.testing_tools import BlockchainTestTools


class TestNFTCreation(BlockchainTestTools):
    def setUp(self):
        super(TestNFTCreation, self).setUp()

    def test_nft_creation(self):
        token_name = "ETH"

        response = self.app.post(
            "/create_nft",
            json={
                "recipient": self.user_1_public_key,
                "sender": self.gth_public_key,
                "gth_private_key": self.gth_private_key,
                "token": token_name,
            },
        )
        response_json = json.loads(response.get_data(as_text=True))
        self.assertEqual(
            201,
            response.status_code,
            msg=f"NFT creation failed {response_json['message'] if 'message' in response_json else ''}",
        )
        print(f"{response_json['id']=}")
        self.assertTrue(response_json["id"].startswith("nft_"))
        self.assertTrue(response_json["id"].endswith(token_name))

    def test_missing_keys(self):
        response = self.app.post("/create_nft", json={})
        print(f"{response.get_data(as_text=True)=}")
        self.assertEqual(401, response.status_code)

    def test_wrong_arguments(self):
        response = self.app.post(
            "/create_nft",
            json={
                "recipient": self.gth_public_key,
                "sender": self.gth_public_key,
                "gth_private_key": self.gth_private_key,
            },
        )
        self.assertEqual(401, response.status_code)


if __name__ == "__main__":
    unittest.main()
