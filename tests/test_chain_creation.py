import unittest
import sys
sys.path.insert(0, '../src')
from src.blockchain.blockchain_manager import BlockchainManager


class TestChainCreation(unittest.TestCase):
    def setUp(self):
        self.blm = BlockchainManager()

    def test_blockchain_correctly_created_len(self):
        self.assertEqual(len(self.blm.chain), 1)

    def test_blockchain_correctly_created_first_block_index(self):
        self.assertEqual(self.blm.chain.last_block.index, 1)

    def test_blockchain_correctly_created_first_block_transactions(self):
        self.assertEqual(len(self.blm.chain.transactions), 0)

    def test_blockchain_correctly_created_first_block_previous_hash(self):
        self.assertEqual(self.blm.chain.last_block.previous_hash, "0000")


if __name__ == "__main__":
    unittest.main()
