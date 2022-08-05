import unittest
import json

from src.blockchain.server import app


class TestKeys(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()

    def test_private_key(self):
        response = self.app.get("/get_new_private_key")
        private_key = json.loads(response.get_data())["key"]
        self.assertEqual(201, response.status_code)

    def test_public_key(self):
        response = self.app.get("/get_new_private_key")
        private_key = json.loads(response.get_data())["key"]
        self.assertEqual(201, response.status_code)

        response = self.app.get(
            "/get_new_public_key", json={"private_key": private_key}
        )
        self.assertEqual(201, response.status_code)


if __name__ == "__main__":
    unittest.main()
