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