import unittest
from unittest.mock import patch, MagicMock
import sys
from io import StringIO

from app.calculator_repl import calculator_repl


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

    def _run_repl_with_mocks(self, inputs, calc_instance=None, factory_instance=None):
        """
        Runs calculator_repl with patched dependencies.
        Returns the mock object for assertion if needed.
        """
        with patch('app.calculator_repl.Calculator') as mock_calc_class, \
            patch('app.calculator_repl.OperationFactory') as mock_factory, \
            patch('app.calculator_repl.LoggingObserver'), \
            patch('app.calculator_repl.AutoSaveObserver'):

            if calc_instance is None:
                calc_instance = MagicMock()
                mock_calc_class.return_value = calc_instance

            if factory_instance is None:
                factory_instance = MagicMock()
                mock_factory.create_operation.return_value = factory_instance

            with patch('builtins.input', side_effect=inputs):
                calculator_repl()

            return calc_instance, factory_instance

    def test_simple_commands(self):
        test_cases = [
            {
                "name": "help_command",
                "inputs": ["help", "exit"],
                "assert_in": ["Available commands:", "Goodbye!"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {
                "name": "exit_command_success",
                "inputs": ["exit"],
                "assert_in": ["History saved successfully.", "Goodbye!"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {
                "name": "exit_command_save_fail",
                "inputs": ["exit"],
                "assert_in": ["Warning: Could not save history: Disk full", "Goodbye!"],
                "setup_mock": lambda m: setattr(m, 'save_history', MagicMock(side_effect=Exception("Disk full"))),
                "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {
                "name": "history_empty",
                "inputs": ["history", "exit"],
                "assert_in": ["No calculations in history"],
                "setup_mock": lambda m: setattr(m, 'show_history', MagicMock(return_value=[])),
                "check_mock": lambda m: m.show_history.assert_called_once()
            },
            {
                "name": "history_with_data",
                "inputs": ["history", "exit"],
                "assert_in": ["1. 1 + 1 = 2"],
                "setup_mock": lambda m: setattr(m, 'show_history', MagicMock(return_value=["1 + 1 = 2"])),
                "check_mock": lambda m: m.show_history.assert_called_once()
            },
            {
                "name": "clear_history",
                "inputs": ["clear", "exit"],
                "assert_in": ["History cleared"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: m.clear_history.assert_called_once()
            },
            {
                "name": "undo_success",
                "inputs": ["undo", "exit"],
                "assert_in": ["Operation undone"],
                "setup_mock": lambda m: setattr(m, 'undo', MagicMock(return_value=True)),
                "check_mock": lambda m: m.undo.assert_called_once()
            },
            {
                "name": "undo_fail",
                "inputs": ["undo", "exit"],
                "assert_in": ["Nothing to undo"],
                "setup_mock": lambda m: setattr(m, 'undo', MagicMock(return_value=False)),
                "check_mock": lambda m: m.undo.assert_called_once()
            },
            {
                "name": "redo_success",
                "inputs": ["redo", "exit"],
                "assert_in": ["Operation redone"],
                "setup_mock": lambda m: setattr(m, 'redo', MagicMock(return_value=True)),
                "check_mock": lambda m: m.redo.assert_called_once()
            },
            {
                "name": "redo_fail",
                "inputs": ["redo", "exit"],
                "assert_in": ["Nothing to redo"],
                "setup_mock": lambda m: setattr(m, 'redo', MagicMock(return_value=False)),
                "check_mock": lambda m: m.redo.assert_called_once()
            },
            {
                "name": "save_success",
                "inputs": ["save", "exit"],
                "assert_in": ["History saved successfully"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {
                "name": "save_fail",
                "inputs": ["save", "exit"],
                "assert_in": ["Error saving history: IO Error"],
                "setup_mock": lambda m: setattr(m, 'save_history', MagicMock(side_effect=Exception("IO Error"))),
                "check_mock": lambda m: m.save_history.assert_called_once()
            },
            {
                "name": "load_success",
                "inputs": ["load", "exit"],
                "assert_in": ["History loaded successfully"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: m.load_history.assert_called_once()
            },
            {
                "name": "load_fail",
                "inputs": ["load", "exit"],
                "assert_in": ["Error loading history: File not found"],
                "setup_mock": lambda m: setattr(m, 'load_history', MagicMock(side_effect=Exception("File not found"))),
                "check_mock": lambda m: m.load_history.assert_called_once()
            },
            {
                "name": "unknown_command",
                "inputs": ["foobar", "exit"],
                "assert_in": ["Unknown command: 'foobar'"],
                "setup_mock": lambda m: None,
                "check_mock": lambda m: True
            }
        ]

        for case in test_cases:
            with self.subTest(msg=case["name"]):
                self.held_output.seek(0)
                self.held_output.truncate(0)

                calc_mock = MagicMock()
                case["setup_mock"](calc_mock)

                self._run_repl_with_mocks(case["inputs"], calc_instance=calc_mock)

                output = self._get_output()
                for expected_str in case["assert_in"]:
                    self.assertIn(expected_str, output)

                case["check_mock"](calc_mock)
