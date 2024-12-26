import unittest
from anonymizer import PhoneAnonymizer

class TestPhoneAnonymizer(unittest.TestCase):
    def test_north_american_numbers(self):
        """Test North American phone number formats."""
        test_cases = [
            (
                "‪+1 (587) 998‑1598‬",  # With unicode control chars
                "+1****1598",
                None
            ),
            (
                "+1 (210) 749‑5758",    # Standard format
                "+1****5758",
                "John Doe"
            ),
            (
                "+1 (443) 739-6663",    # With regular hyphen
                "+1****6663",
                None
            )
        ]
        
        for phone, expected_anon, username in test_cases:
            anon_phone, display = PhoneAnonymizer.anonymize(phone, username)
            self.assertEqual(anon_phone, expected_anon)
            if username:
                self.assertEqual(display, f"[👤] {username}")
            else:
                self.assertTrue(display.startswith("[🎭] "))

    def test_international_numbers(self):
        """Test various international phone number formats."""
        test_cases = [
            (
                "‪+44 7464 758875‬",     # UK format
                "+44****8875",
                None
            ),
            (
                "+91 80885 89616",      # Indian format
                "+91****9616",
                "Alice"
            ),
            (
                "+234 811 635 8644",    # Nigerian format
                "+234****8644",
                None
            ),
            (
                "+30 697 550 3831",     # Greek format
                "+30****3831",
                "Bob"
            ),
            (
                "+353 86 868 2859",     # Irish format
                "+353****2859",
                None
            )
        ]
        
        for phone, expected_anon, username in test_cases:
            anon_phone, display = PhoneAnonymizer.anonymize(phone, username)
            self.assertEqual(anon_phone, expected_anon)
            if username:
                self.assertEqual(display, f"[👤] {username}")
            else:
                self.assertTrue(display.startswith("[🎭] "))

    def test_additional_international_formats(self):
        """Test additional international phone number formats not in common list."""
        test_cases = [
            ("+86 123 4567 8901", "+86****8901"),  # China
            ("+971 50 123 4567", "+971****4567"),  # UAE
            ("+81 90 1234 5678", "+81****5678"),   # Japan
            ("+7 916 123 4567", "+7****4567"),     # Russia
            ("+972 50 123 4567", "+972****4567"),  # Israel
            ("+359 2 123 4567", "+359****4567"),   # Bulgaria
            ("+55 11 1234 5678", "+55****5678"),   # Brazil
            ("+380 44 123 4567", "+380****4567"),  # Ukraine
        ]
        
        for phone, expected_anon in test_cases:
            anon_phone, display = PhoneAnonymizer.anonymize(phone, None)
            self.assertEqual(anon_phone, expected_anon)
            self.assertTrue(display.startswith("[🎭] "))

    def test_unicode_control_characters(self):
        """Test handling of unicode control characters in phone numbers."""
        # Phone number with various unicode control characters
        phone = "‪\u200e+44\u200f \u202a7464\u202c \u202d758875\u202e‬"
        expected_anon = "+44****8875"
        
        anon_phone, display = PhoneAnonymizer.anonymize(phone, None)
        self.assertEqual(anon_phone, expected_anon)
        self.assertTrue(display.startswith("[🎭] "))

    def test_username_with_control_chars(self):
        """Test handling of unicode control characters in usernames."""
        phone = "+1234567890"
        username = "‪\u200eJohn\u200f \u202aDoe\u202c"
        expected_name = "John Doe"
        
        _, display = PhoneAnonymizer.anonymize(phone, username)
        self.assertEqual(display, f"[👤] {expected_name}")

    def test_short_numbers(self):
        """Test handling of unusually short numbers."""
        test_cases = [
            ("123", "**3", None),
            ("1234", "***4", "Short"),
            ("12345", "****5", None)
        ]
        
        for phone, expected_anon, username in test_cases:
            anon_phone, display = PhoneAnonymizer.anonymize(phone, username)
            self.assertEqual(anon_phone, expected_anon)
            if username:
                self.assertEqual(display, f"[👤] {username}")
            else:
                self.assertTrue(display.startswith("[🎭] "))

    def test_various_separators(self):
        """Test handling of various separator characters in phone numbers."""
        test_cases = [
            ("+1-234-567-8900", "+1****8900"),
            ("+1‑234‑567‑8900", "+1****8900"),  # With unicode hyphens
            ("+1 234 567 8900", "+1****8900"),
            ("+1.234.567.8900", "+1****8900"),
        ]
        
        for phone, expected_anon in test_cases:
            anon_phone, _ = PhoneAnonymizer.anonymize(phone)
            self.assertEqual(anon_phone, expected_anon)

    def test_generated_names_uniqueness(self):
        """Test that generated names are likely to be different."""
        phone = "+1234567890"
        seen_names = set()
        
        # Generate 50 names and check for reasonable uniqueness
        for _ in range(50):
            _, display = PhoneAnonymizer.anonymize(phone)
            seen_names.add(display)
        
        # With our word combinations, we should get good variety
        # Even with 50 generations, we should have at least 40 unique names
        self.assertGreater(len(seen_names), 40)
        
        # Verify all generated names follow our format
        for name in seen_names:
            self.assertTrue(name.startswith("[🎭] "))
            self.assertGreater(len(name), 5)

if __name__ == '__main__':
    unittest.main()