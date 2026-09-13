import unittest
from code.data_loader import DataLoader

class TestDataLoader(unittest.TestCase):
    def setUp(self):
        self.loader = DataLoader()

    def test_load_all(self):
        self.loader.load_all()
        self.assertGreater(len(self.loader.requests), 0)
        self.assertGreater(len(self.loader.profiles), 0)
        self.assertGreater(len(self.loader.events), 0)
        self.assertGreater(len(self.loader.payment_options), 0)
        
    def test_relationships(self):
        self.loader.load_all()
        errors = self.loader.validate_relationships()
        self.assertEqual(len(errors), 0, f"Relationship errors found: {errors}")

if __name__ == "__main__":
    unittest.main()
