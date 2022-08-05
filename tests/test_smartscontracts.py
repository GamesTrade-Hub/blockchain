import unittest

from tests.testing_tools import BlockchainTestTools


class TestValidSmartContract(BlockchainTestTools):
    def setUp(self):
        self._app = super().setUp()

    def test_smarts_contracts_exchange(self):
        self.empty_wallet(self.user_1_private_key, self.user_1_public_key, "snowy")
        self.empty_wallet(self.user_2_private_key, self.user_2_public_key, "snowy")

        self.give_to_user(self.user_1_public_key, 50, "snowy")
        self.give_to_user(self.user_2_public_key, 10, "snowy")

        # Check if the balance is correct
        self.check_balance_is_correct(self.user_1_public_key, "snowy", 50)
        self.check_balance_is_correct(self.user_2_public_key, "snowy", 10)

        # User 1 send 50 to user 2 if user 2 send 10
        self.new_transaction(
            sender=self.user_1_public_key,
            recipient=self.user_2_public_key,
            amount=50,
            token="snowy",
            private_key=self.user_1_private_key,
            smart_contract={
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_1_public_key,
                "sender": self.user_2_public_key,
                "amount": 10,
                "token": "snowy",
            },
            check_block_not_created=True,
        )

        # Check if the balance is correct
        self.check_balance_is_correct(self.user_1_public_key, "snowy", 50)
        self.check_balance_is_correct(self.user_2_public_key, "snowy", 10)

        # User 2 send 10 to user 1 if user 1 send 50 to user 2
        self.new_transaction(
            sender=self.user_2_public_key,
            recipient=self.user_1_public_key,
            amount=10,
            token="snowy",
            private_key=self.user_2_private_key,
            smart_contract={
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_2_public_key,
                "sender": self.user_1_public_key,
                "amount": 50,
                "token": "snowy",
            },
            check_block_created=True,
        )

        # Check if the balance is correct
        self.assertEqual(self.get_balance_token(self.user_1_public_key, "snowy"), 10)
        self.assertEqual(self.get_balance_token(self.user_2_public_key, "snowy"), 50)

    def test_smarts_contracts_exchange_2(self):
        self.empty_wallet(self.user_1_private_key, self.user_1_public_key, "snowy")
        self.empty_wallet(self.user_2_private_key, self.user_2_public_key, "snowy")

        self.give_to_user(self.user_1_public_key, 100, "snowy")
        self.give_to_user(self.user_2_public_key, 100, "snowy")

        # Check if the balance is correct
        self.check_balance_is_correct(self.user_1_public_key, "snowy", 100)
        self.check_balance_is_correct(self.user_2_public_key, "snowy", 100)

        # User 2 send 10 to user 1 if user 1 send 50 to user 2
        self.new_transaction(
            sender=self.user_2_public_key,
            recipient=self.user_1_public_key,
            amount=20,
            token="snowy",
            private_key=self.user_2_private_key,
            smart_contract={
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_2_public_key,
                "sender": self.user_1_public_key,
                "amount": 60,
                "token": "snowy",
            },
            check_block_not_created=True,
        )

        # Check if the balance is correct
        self.assertEqual(self.get_balance_token(self.user_1_public_key, "snowy"), 100)
        self.assertEqual(self.get_balance_token(self.user_2_public_key, "snowy"), 100)

        # User 1 send 50 to user 2 if user 2 send 10
        self.new_transaction(
            sender=self.user_1_public_key,
            recipient=self.user_2_public_key,
            amount=60,
            token="snowy",
            private_key=self.user_1_private_key,
            smart_contract={
                "type": "OTHER_TX_CHECK",
                "recipient": self.user_1_public_key,
                "sender": self.user_2_public_key,
                "amount": 20,
                "token": "snowy",
            },
            check_block_created=True,
        )

        # Check if the balance is correct
        self.assertEqual(self.get_balance_token(self.user_1_public_key, "snowy"), 60)
        self.assertEqual(self.get_balance_token(self.user_2_public_key, "snowy"), 140)

    def test_error(self):
        response = self.app.post(
            "/transaction/new",
            json={
                "sender": self.user_1_public_key,
                "recipient": self.user_2_public_key,
                "amount": 10,
                "private_key": self.user_1_private_key,
                "token": "snowy",
                "smart_contract": {  # Is invalid because recipient is missing
                    "type": "OTHER_TX_CHECK",
                    "sender": self.user_2_public_key,
                    "amount": 50,
                    "token": "snowy",
                },
            },
        )
        self.assertEqual(response.status_code, 401)


if __name__ == "__main__":
    unittest.main()
