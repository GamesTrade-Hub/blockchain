import unittest
import json

from src.blockchain.server import app
from tests.testing_tools import BlockchainTestTools


class TestMining(BlockchainTestTools):
    def setUp(self):
        super(TestMining, self).setUp()

    def test_first_block(self):
        response = self.app.get("/chain")
        self.assertEqual(json.loads(response.get_data())["length"], 1)
        self.assertEqual(200, response.status_code)

    def test_new_block_fail(self):
        self.app.post("/block/new", json={})
        response = self.app.post("/block/new", json={})
        self.assertEqual(401, response.status_code)

    def test_mining_chain_size(self):
        response = self.app.get("/chain")
        bc_len = json.loads(response.get_data())["length"]

        response = self.app.get("/nodes/list")
        self.assertEqual(200, response.status_code)

        self.new_transaction(
            sender=self.token_admin_pb,
            recipient=self.user_1_public_key,
            amount=50,
            token="ETH",
            private_key=self.token_admin_pv,
            check_block_created=True,
        )

        response = self.app.get("/nodes/resolve", follow_redirects=True)
        self.assertEqual(response.status_code, 200)

        response = self.app.get("/chain")
        self.assertEqual(bc_len + 1, json.loads(response.get_data())["length"])

    def test_invalid_register(self):
        response = self.app.post("/nodes/register", json={})
        self.assertEqual(400, response.status_code)


if __name__ == "__main__":
    unittest.main()
