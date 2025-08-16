from django.test import TestCase
from django.contrib.auth.models import User
from SmartApp.models import Asset
from SmartApp.asset_assistant import handle_asset_query

class AssetAssistantSynonymTests(TestCase):
    def setUp(self):
        # Create test user
        self.user = User.objects.create_user(username='testuser', password='testpass')
        # Create assets with categories and departments
        Asset.objects.create(name='Dell Laptop', category='computers', department='EASA')
        Asset.objects.create(name='HP Desktop', category='hp', department='EASA')
        Asset.objects.create(name='MacBook', category='computers', department='Library')
        Asset.objects.create(name='HP Printer', category='hp', department='Library')

    def test_category_synonyms_computers(self):
        # Test synonyms for computers category
        synonyms = ['pc', 'laptop', 'notebook', 'desktop']
        for syn in synonyms:
            response = handle_asset_query(f"How many {syn} are in EASA?")
            self.assertIn("There are", response)
            self.assertIn("computers", response)

    def test_category_synonyms_hp(self):
        # Test synonyms for hp category
        synonyms = ['hp', 'hewlett packard']
        for syn in synonyms:
            response = handle_asset_query(f"How many {syn} are in Library?")
            self.assertIn("There are", response)
            self.assertIn("hp", response)

    def test_department_synonyms(self):
        # Test department synonyms
        response = handle_asset_query("How many computers are in school?")
        self.assertIn("There are", response)
        self.assertIn("EASA", response)

    def test_fuzzy_matching(self):
        # Test fuzzy matching for category and department
        response = handle_asset_query("How many computrs are in EASA?")
        self.assertIn("There are", response)
        self.assertIn("computers", response)

        response = handle_asset_query("How many computers are in Easa?")
        self.assertIn("There are", response)
        self.assertIn("EASA", response)

    def test_asset_listing(self):
        # Test listing assets in a department
        response = handle_asset_query("List assets in Library")
        self.assertIn("Assets in Library", response)
        self.assertIn("MacBook", response)
        self.assertIn("HP Printer", response)
