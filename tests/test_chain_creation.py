import unittest
from src import Blockchain


class TestChainCreation(unittest.TestCase):
    def setUp(self):
        self.blockchain = Blockchain()

    def test_blockchain_correctly_created_len(self):
        self.assertEqual(len(self.blockchain.chain), 1)

    def test_blockchain_correctly_created_first_block_index(self):
        self.assertEqual(self.blockchain.last_block['index'], 1)

    def test_blockchain_correctly_created_first_block_transactions(self):
        self.assertEqual(len(self.blockchain.last_block['transactions']), 0)

    def test_blockchain_correctly_created_first_block_proof(self):
        self.assertEqual(self.blockchain.last_block['nonce'], 100)

    def test_blockchain_correctly_created_first_block_previous_hash(self):
        self.assertEqual(self.blockchain.last_block['previous_hash'], "1")


if __name__ == '__main__':
    unittest.main()
