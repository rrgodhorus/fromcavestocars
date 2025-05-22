#!/usr/bin/python3
"""
Test runner script for the fromcavestocars application.
Discovers and runs all tests in the tests directory.
"""

import unittest
import sys
import os

# Ensure that the parent directory is in the path so we can import modules
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def run_tests():
    """Discover and run all tests."""
    # Discover tests in the tests directory
    test_loader = unittest.TestLoader()
    test_suite = test_loader.discover('tests', pattern='test_*.py')
    
    # Run tests
    test_runner = unittest.TextTestRunner(verbosity=2)
    result = test_runner.run(test_suite)
    
    # Return non-zero exit code if any tests failed
    return 0 if result.wasSuccessful() else 1

if __name__ == '__main__':
    sys.exit(run_tests())