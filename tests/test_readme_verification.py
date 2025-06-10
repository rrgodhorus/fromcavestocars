#!/usr/bin/env python3
"""
Test to verify README.md character count and basic file integrity.
This test ensures the README.md file exists and maintains expected characteristics.
"""

import os
import unittest

class ReadmeVerificationTests(unittest.TestCase):
    """Tests to verify README.md file characteristics."""

    def setUp(self):
        """Set up test by locating README.md file."""
        self.readme_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'README.md')

    def test_readme_exists(self):
        """Test that README.md file exists."""
        self.assertTrue(os.path.exists(self.readme_path), "README.md file should exist")

    def test_readme_character_count(self):
        """Test that README.md has the expected number of characters."""
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        char_count = len(content)
        expected_char_count = 3932
        
        self.assertEqual(char_count, expected_char_count, 
                        f"README.md should contain exactly {expected_char_count} characters, "
                        f"but found {char_count}")

    def test_readme_not_empty(self):
        """Test that README.md is not empty."""
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertGreater(len(content.strip()), 0, "README.md should not be empty")

    def test_readme_has_title(self):
        """Test that README.md contains the expected title."""
        with open(self.readme_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        self.assertIn("From Caves To Cars", content, 
                     "README.md should contain the project title 'From Caves To Cars'")

if __name__ == '__main__':
    unittest.main()