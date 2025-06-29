#!/usr/bin/env python3
"""
Test runner script for Finviz MCP Server comprehensive test suite.
Provides convenient interface to run all test categories.
"""

import os
import sys
import subprocess
import argparse
import time
from pathlib import Path
from typing import List, Optional


class TestRunner:
    """Test runner for Finviz MCP Server tests."""

    def __init__(self):
        self.project_root = Path(__file__).parent
        self.tests_dir = self.project_root / "tests"
        
    def run_command(self, command: List[str], description: str) -> bool:
        """Run a command and return success status."""
        print(f"\n{'='*60}")
        print(f"Running: {description}")
        print(f"Command: {' '.join(command)}")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            result = subprocess.run(
                command,
                cwd=self.project_root,
                capture_output=False,
                text=True,
                check=True
            )
            
            elapsed = time.time() - start_time
            print(f"\n✅ {description} completed successfully in {elapsed:.2f}s")
            return True
            
        except subprocess.CalledProcessError as e:
            elapsed = time.time() - start_time
            print(f"\n❌ {description} failed after {elapsed:.2f}s")
            print(f"Exit code: {e.returncode}")
            return False
        except KeyboardInterrupt:
            print(f"\n⚠️  {description} interrupted by user")
            return False

    def run_e2e_tests(self) -> bool:
        """Run E2E screener tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_e2e_screeners.py", "-v", "--tb=short"],
            "E2E Screener Tests"
        )

    def run_parameter_tests(self) -> bool:
        """Run parameter combination tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_parameter_combinations.py", "-v", "--tb=short"],
            "Parameter Combination Tests"
        )

    def run_error_tests(self) -> bool:
        """Run error handling tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_error_handling.py", "-v", "--tb=short"],
            "Error Handling Tests"
        )

    def run_integration_tests(self) -> bool:
        """Run MCP integration tests."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_mcp_integration.py", "-v", "--tb=short"],
            "MCP Integration Tests"
        )

    def run_all_tests(self) -> bool:
        """Run all test suites."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short"],
            "All Tests"
        )

    def run_tests_with_coverage(self) -> bool:
        """Run tests with coverage reporting."""
        coverage_commands = [
            (["python", "-m", "pytest", "tests/", "--cov=src", "--cov-report=html", "--cov-report=term"], 
             "Tests with Coverage"),
        ]
        
        success = True
        for command, description in coverage_commands:
            if not self.run_command(command, description):
                success = False
                
        if success:
            print(f"\n📊 Coverage report generated in: {self.project_root}/htmlcov/index.html")
            
        return success

    def run_performance_tests(self) -> bool:
        """Run performance benchmarks."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/", "-v", "--tb=short", "-k", "performance or concurrent or large"],
            "Performance Tests"
        )

    def run_smoke_tests(self) -> bool:
        """Run smoke tests (quick validation)."""
        return self.run_command(
            ["python", "-m", "pytest", "tests/test_e2e_screeners.py::TestFinvizScreenersE2E::test_earnings_screener_basic", "-v"],
            "Smoke Tests"
        )

    def lint_code(self) -> bool:
        """Run code linting."""
        lint_commands = [
            (["python", "-m", "flake8", "src/", "tests/"], "Flake8 Linting"),
            (["python", "-m", "black", "--check", "src/", "tests/"], "Black Code Formatting Check"),
        ]
        
        success = True
        for command, description in lint_commands:
            if not self.run_command(command, description):
                success = False
                
        return success

    def type_check(self) -> bool:
        """Run type checking."""
        return self.run_command(
            ["python", "-m", "mypy", "src/"],
            "MyPy Type Checking"
        )

    def install_test_dependencies(self) -> bool:
        """Install test dependencies."""
        return self.run_command(
            ["pip", "install", "-e", ".[dev]"],
            "Installing Test Dependencies"
        )

    def print_summary(self, results: dict):
        """Print test summary."""
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        
        total_tests = len(results)
        passed_tests = sum(1 for success in results.values() if success)
        failed_tests = total_tests - passed_tests
        
        for test_name, success in results.items():
            status = "✅ PASS" if success else "❌ FAIL"
            print(f"{status} {test_name}")
            
        print(f"\nTotal: {total_tests}, Passed: {passed_tests}, Failed: {failed_tests}")
        
        if failed_tests == 0:
            print("🎉 All tests passed!")
        else:
            print(f"⚠️  {failed_tests} test suite(s) failed")


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Finviz MCP Server Test Runner")
    
    parser.add_argument(
        "test_type",
        nargs="?",
        choices=[
            "all", "e2e", "params", "errors", "integration", 
            "coverage", "performance", "smoke", "lint", "types", "install"
        ],
        default="all",
        help="Type of tests to run (default: all)"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    parser.add_argument(
        "--fail-fast", "-x",
        action="store_true",
        help="Stop on first failure"
    )

    args = parser.parse_args()
    
    runner = TestRunner()
    results = {}
    
    # Check if tests directory exists
    if not runner.tests_dir.exists():
        print(f"❌ Tests directory not found: {runner.tests_dir}")
        sys.exit(1)
    
    print("🧪 Finviz MCP Server Test Runner")
    print(f"📁 Project root: {runner.project_root}")
    print(f"📁 Tests directory: {runner.tests_dir}")
    
    try:
        if args.test_type == "install":
            success = runner.install_test_dependencies()
            sys.exit(0 if success else 1)
            
        elif args.test_type == "smoke":
            results["Smoke Tests"] = runner.run_smoke_tests()
            
        elif args.test_type == "e2e":
            results["E2E Tests"] = runner.run_e2e_tests()
            
        elif args.test_type == "params":
            results["Parameter Tests"] = runner.run_parameter_tests()
            
        elif args.test_type == "errors":
            results["Error Handling Tests"] = runner.run_error_tests()
            
        elif args.test_type == "integration":
            results["Integration Tests"] = runner.run_integration_tests()
            
        elif args.test_type == "coverage":
            results["Coverage Tests"] = runner.run_tests_with_coverage()
            
        elif args.test_type == "performance":
            results["Performance Tests"] = runner.run_performance_tests()
            
        elif args.test_type == "lint":
            results["Linting"] = runner.lint_code()
            
        elif args.test_type == "types":
            results["Type Checking"] = runner.type_check()
            
        else:  # "all"
            test_suites = [
                ("E2E Tests", runner.run_e2e_tests),
                ("Parameter Tests", runner.run_parameter_tests),
                ("Error Handling Tests", runner.run_error_tests),
                ("Integration Tests", runner.run_integration_tests),
            ]
            
            for name, test_func in test_suites:
                results[name] = test_func()
                
                if args.fail_fast and not results[name]:
                    print(f"\n⚠️  Stopping due to --fail-fast (failed: {name})")
                    break
    
    except KeyboardInterrupt:
        print("\n⚠️  Test run interrupted by user")
        sys.exit(1)
    
    # Print summary
    runner.print_summary(results)
    
    # Exit with error code if any tests failed
    if any(not success for success in results.values()):
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()