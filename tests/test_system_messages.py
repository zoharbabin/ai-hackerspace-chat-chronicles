import unittest
from main import clean_message, SYSTEM_MESSAGE_PATTERNS

class TestSystemMessages(unittest.TestCase):
    def setUp(self):
        """Set up test cases with various Unicode control characters."""
        # Common Unicode control characters found in WhatsApp messages
        self.control_chars = {
            'LRM': '\u200e',     # Left-to-Right Mark
            'RLM': '\u200f',     # Right-to-Left Mark
            'LRE': '\u202a',     # Left-to-Right Embedding
            'RLE': '\u202b',     # Right-to-Left Embedding
            'PDF': '\u202c',     # Pop Directional Formatting
            'LRO': '\u202d',     # Left-to-Right Override
            'RLO': '\u202e',     # Right-to-Left Override
            'ZWS': '\u200b',     # Zero Width Space
            'ZWNJ': '\u200c',    # Zero Width Non-Joiner
            'ZWJ': '\u200d',     # Zero Width Joiner
            'BOM': '\ufeff',     # Byte Order Mark
        }

    def test_group_management_messages(self):
        """Test cleaning and detection of group management messages."""
        test_cases = [
            # Group creation
            (
                f"{self.control_chars['LRM']}[24/08/2024, 21:35:29] {self.control_chars['RLM']}+1 (917) 488-2434: {self.control_chars['LRE']}Alice created this group{self.control_chars['PDF']}",
                "[24/08/2024, 21:35:29] +1 (917) 488-2434: Alice created this group"
            ),
            # Group join
            (
                f"{self.control_chars['LRM']}[24/08/2024, 21:36:00] {self.control_chars['RLM']}+44 7911 123456: {self.control_chars['LRE']}Bob joined using this group's invite link{self.control_chars['PDF']}",
                "[24/08/2024, 21:36:00] +44 7911 123456: Bob joined using this group's invite link"
            ),
            # Member addition (with multiple control characters)
            (
                f"{self.control_chars['LRM']}{self.control_chars['ZWS']}[24/08/2024, 21:35:29] {self.control_chars['RLM']}+1 (917) 488-2434: {self.control_chars['LRE']}Ben Alterzon added {self.control_chars['RLM']}+1{self.control_chars['PDF']} (917) 488-2434{self.control_chars['PDF']}",
                "[24/08/2024, 21:35:29] +1 (917) 488-2434: Ben Alterzon added +1 (917) 488-2434"
            )
        ]
        self._run_test_cases(test_cases)

    def test_security_messages(self):
        """Test cleaning and detection of security-related messages."""
        test_cases = [
            # Security code change
            (
                f"{self.control_chars['LRM']}[28/08/2024, 19:49:55] {self.control_chars['RLM']}+972 58-799-5895: {self.control_chars['LRE']}Your security code with {self.control_chars['RLM']}+972{self.control_chars['PDF']} 58-799-5895 changed.{self.control_chars['PDF']}",
                "[28/08/2024, 19:49:55] +972 58-799-5895: Your security code with +972 58-799-5895 changed."
            ),
            # Encryption notice (system message without sender)
            (
                f"{self.control_chars['LRM']}Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen.{self.control_chars['PDF']}",
                "Messages and calls are end-to-end encrypted. No one outside of this chat can read or listen."
            )
        ]
        self._run_test_cases(test_cases)

    def test_phone_number_messages(self):
        """Test cleaning and detection of phone number related messages."""
        test_cases = [
            # Phone number change
            (
                f"{self.control_chars['LRM']}[24/08/2024, 21:40:00] {self.control_chars['RLM']}+1 (917) 488-2434: {self.control_chars['LRE']}Charlie changed their phone number{self.control_chars['PDF']}",
                "[24/08/2024, 21:40:00] +1 (917) 488-2434: Charlie changed their phone number"
            )
        ]
        self._run_test_cases(test_cases)

    def test_message_deletion(self):
        """Test cleaning and detection of deleted message notifications."""
        test_cases = [
            # Deleted message
            (
                f"{self.control_chars['LRM']}[24/08/2024, 22:00:00] {self.control_chars['RLM']}+1 (917) 488-2434: {self.control_chars['LRE']}This message was deleted{self.control_chars['PDF']}",
                "[24/08/2024, 22:00:00] +1 (917) 488-2434: This message was deleted"
            )
        ]
        self._run_test_cases(test_cases)

    def test_edge_cases(self):
        """Test edge cases and unusual message formats."""
        test_cases = [
            # Multiple consecutive control characters
            (
                f"{self.control_chars['LRM']}{self.control_chars['ZWS']}{self.control_chars['LRE']}[24/08/2024, 21:35:29] +1 (917) 488-2434: This message was deleted{self.control_chars['PDF']}{self.control_chars['PDF']}{self.control_chars['PDF']}",
                "[24/08/2024, 21:35:29] +1 (917) 488-2434: This message was deleted"
            ),
            # Mixed directional control characters
            (
                f"{self.control_chars['LRM']}{self.control_chars['RLM']}[24/08/2024, 21:35:29] +1 (917) 488-2434: {self.control_chars['LRE']}{self.control_chars['RLE']}Alice created this group{self.control_chars['PDF']}{self.control_chars['PDF']}",
                "[24/08/2024, 21:35:29] +1 (917) 488-2434: Alice created this group"
            ),
            # Zero-width characters between normal characters
            (
                f"[24/08/2024, 21:35:29] +1 (917) 488-2434: A{self.control_chars['ZWS']}l{self.control_chars['ZWNJ']}i{self.control_chars['ZWJ']}ce created this group",
                "[24/08/2024, 21:35:29] +1 (917) 488-2434: Alice created this group"
            )
        ]
        self._run_test_cases(test_cases)

    def _run_test_cases(self, test_cases):
        """Helper method to run test cases with consistent validation."""
        for input_msg, expected_clean in test_cases:
            # Test message cleaning
            cleaned = clean_message(input_msg)
            self.assertEqual(cleaned, expected_clean,
                           f"Clean message failed.\nExpected: {expected_clean}\nGot: {cleaned}")

            # Extract just the message content after the colon
            message_content = cleaned.split(': ', 1)[1] if ': ' in cleaned else cleaned
            
            # Test system message detection
            is_system = any(pattern.match(message_content) for pattern in SYSTEM_MESSAGE_PATTERNS)
            self.assertTrue(is_system, f"Failed to detect system message: {message_content}")

            # Verify no control characters remain
            for char in self.control_chars.values():
                self.assertNotIn(char, cleaned,
                               f"Found control character {hex(ord(char))} in cleaned message")

if __name__ == '__main__':
    unittest.main()