"""
Custom test runner with clean output and warning suppression
"""
import os
import sys
import unittest
import warnings
from typing import cast

# Suppress all warnings
warnings.filterwarnings("ignore")
os.environ['PYTHONWARNINGS'] = 'ignore'

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from tests.test_application import TestRoomScheduleApplication


class MinimalTestResult(unittest.TextTestResult):
    """Custom test result class for formatted output"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.test_results: list = []
    
    def addSuccess(self, test):
        super().addSuccess(test)
        test_name = test._testMethodName.replace('test_', '').replace('_', ' ').title()
        test_doc = test._testMethodDoc
        if test_doc:
            # Extract the first line of description
            desc = test_doc.strip().split('\n')[1].strip() if '\n' in test_doc else test_doc.strip()
        else:
            desc = "No description"
        self.test_results.append((test_name, desc, "✅ SUCCESS"))
    
    def addError(self, test, err):
        super().addError(test, err)
        test_name = test._testMethodName.replace('test_', '').replace('_', ' ').title()
        self.test_results.append((test_name, "Runtime error occurred", "❌ ERROR"))
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        test_name = test._testMethodName.replace('test_', '').replace('_', ' ').title()
        self.test_results.append((test_name, "Assertion failed", "❌ FAIL"))


class MinimalTestRunner(unittest.TextTestRunner):
    """Custom test runner with minimal output"""
    resultclass = MinimalTestResult
    
    def run(self, test):
        # Redirect stdout/stderr during test execution
        result = super().run(test)
        result = cast(MinimalTestResult, result)
        
        # Print formatted results
        print("\n" + "="*100)
        print("TEST EXECUTION SUMMARY")
        print("="*100)
        
        for i, (name, desc, status) in enumerate(result.test_results, 1):
            print(f"Test {i} | {name} | {desc} | {status}")
        
        print("="*100)
        passed = result.testsRun - len(result.failures) - len(result.errors)
        failed = len(result.failures) + len(result.errors)
        
        status_icon = "✅" if result.wasSuccessful() else "❌"
        print(f"{status_icon} Total: {result.testsRun} | Passed: {passed} | Failed: {failed}")
        print("="*100 + "\n")
        
        return result


if __name__ == "__main__":
    # Suppress warnings at runtime
    import warnings
    warnings.simplefilter("ignore")
    
    # Load and run tests
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestRoomScheduleApplication)
    
    # Run with custom runner (silent during execution)
    runner = MinimalTestRunner(verbosity=0, stream=open(os.devnull, 'w'))
    result = runner.run(suite)
    
    # Exit with appropriate code
    sys.exit(0 if result.wasSuccessful() else 1)
