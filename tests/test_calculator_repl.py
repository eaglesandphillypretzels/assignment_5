import unittest
from unittest.mock import patch, MagicMock, call
import sys
from io import StringIO
from decimal import Decimal

from app.calculator_repl import calculator_repl
from app.exceptions import OperationError, ValidationError

class TestCalculatorRepl(unittest.TestCase):

    def setUp(self):
        """Set up test fixtures."""
        self.held_output = StringIO()
        self.sys_stdout = sys.stdout
        sys.stdout = self.held_output

    def tearDown(self):
        """Clean up test fixtures."""
        sys.stdout = self.sys_stdout
        self.held_output.close()

    def _get_output(self):
        """Helper to get captured stdout."""
        return self.held_output.getvalue()

# Helper to run REPL with mocked dependencies

def _run_repl_with_mocks(self, inputs, calc_instance=None, factory_instance=None):
    """
    Runs calculator_repl with patched dependencies.
    Returns the mock object for assertion if needed.
    """
    with patch('app.calculator_repl.Calculator') as mock_calc_class, \
        patch ('app,calculator_repl.OperationFactory') as mock_factory, \
        patch ('app.calculator_repl.LoggingObserver'), \
        patch ('app.calculator_repl.AutoSaveObserver'):

        if calc_instance is None:
            calc_instance = MagicMock()
            mock_calc_class.return_value = calc_instance

        if factory_instance is Nonr:
            factory_instance = MagicMock()
            mock_factory.create_operation.return_value = factory_instance

        with patch('builtins.input', side_effect=inputs):
            calculator_repl()

        return calc_instance, factory_instance
    
# Parameterized Simple Commands

def test_simple_commands(self):

    test_cases = [
        {
            "name": "help_command"
            "inputs": ["help", "exit"]
            "assert_in": ["Available commands:", "Goodbye!"],
            "setup_mock": lambda m: None,
            "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {   
        }
    ]