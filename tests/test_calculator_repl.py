import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from app.calculator_repl import calculator_repl
from app.exceptions import OperationError, ValidationError

# Testing Simple Commands

@pytest.mark.parametrize("command,expected_output", [
    ("help", "Available commands:"),
    ("clear", "History cleared"),
    ("history", "No calculations in history"),
])
def test_simple_commands(command, expected_output, capsys):
    """Test simple commands that don't require additional input"""
    with patch('builtins.input', side_effect=[command, 'exit']):
        calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing Exit Command Variations

@pytest.mark.parametrize("save_side_effect,expected_output", [
    (None, "History saved successfully"),
    (Exception("Save failed"), "Warning: Could not save history"),
])
def test_exit_command(save_side_effect, expected_output, capsys):
    """Test exit command with different save outcomes"""
    with patch('app.calculator.Calculator.save_history', side_effect=save_side_effect):
        with patch('builtins.input', return_value='exit'):
            calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing History with Calculation Entries

def test_history_with_entries(capsys):
    """Test history command when there are calculations"""
    mock_history = ["1 + 1 = 2", "2 * 3 = 6"]
    
    with patch('app.calculator.Calculator.show_history', return_value=mock_history):
        with patch('builtins.input', side_effect=['history', 'exit']):
            calculator_repl()
    
    captured = capsys.readouterr()
    assert "Calculation History:" in captured.out
    assert "1. 1 + 1 = 2" in captured.out
    assert "2. 2 * 3 = 6" in captured.out

# Testing Undo/Redo Commands

@pytest.mark.parametrize("command,undo_redo_return,expected_output", [
    ("undo", True, "Operation undone"),
    ("undo", False, "Nothing to undo"),
    ("redo", True, "Operation redone"),
    ("redo", False, "Nothing to redo"),
])
def test_undo_redo_commands(command, undo_redo_return, expected_output, capsys):
    """Test undo and redo commands with different outcomes"""
    with patch(f'app.calculator.Calculator.{command}', return_value=undo_redo_return):
        with patch('builtins.input', side_effect=[command, 'exit']):
            calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing Save/Load Commands with Errors (Exceptions)

@pytest.mark.parametrize("command,method,side_effect,expected_output", [
    ("save", "save_history", Exception("Disk full"), "Error saving history"),
    ("load", "load_history", Exception("File not found"), "Error loading history"),
])
def test_save_load_errors(command, method, side_effect, expected_output, capsys):
    """Test save and load commands when errors occur"""
    with patch(f'app.calculator.Calculator.{method}', side_effect=side_effect):
        with patch('builtins.input', side_effect=[command, 'exit']):
            calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing Arithmetic Operations

@pytest.mark.parametrize("operation,inputs,expected_output", [
    # Successful operation with Decimal result
    ("add", ["1.5", "2.5"], "Result: 4"),
    # Cancel at first input
    ("subtract", ["cancel"], "Operation cancelled"),
    # Cancel at second input
    ("multiply", ["5", "cancel"], "Operation cancelled"),
])
def test_arithmetic_operations(operation, inputs, expected_output, capsys):
    """Test arithmetic operations with various scenarios"""
    with patch('app.operations.OperationFactory.create_operation') as mock_factory:
        mock_operation = MagicMock()
        mock_factory.return_value = mock_operation
        
        # Mock perform_operation to return a Decimal
        with patch('app.calculator.Calculator.perform_operation', return_value=Decimal("4.0")):
            with patch('builtins.input', side_effect=inputs + ['exit']):
                calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing Exception Handling in Operations

@pytest.mark.parametrize("exception_class,expected_output", [
    (ValidationError("Invalid input"), "Error: Invalid input"),
    (OperationError("Division by zero"), "Error: Division by zero"),
    (Exception("Unexpected"), "Unexpected error: Unexpected"),
])
def test_operation_exceptions(exception_class, expected_output, capsys):
    """Test exception handling during arithmetic operations"""
    with patch('app.operations.OperationFactory.create_operation'):
        with patch('app.calculator.Calculator.perform_operation', side_effect=exception_class):
            with patch('builtins.input', side_effect=['add', '1', '2', 'exit']):
                calculator_repl()
    
    captured = capsys.readouterr()
    assert expected_output in captured.out

# Testing Keyboard Interrupts, End-of-File (EOF)

def test_keyboard_interrupt(capsys):
    """Test handling of Ctrl+C"""
    with patch('builtins.input', side_effect=[KeyboardInterrupt(), 'exit']):
        calculator_repl()
    
    captured = capsys.readouterr()
    assert "Operation cancelled" in captured.out

def test_eof_error(capsys):
    """Test handling of Ctrl+D (EOF)"""
    with patch('builtins.input', side_effect=EOFError()):
        calculator_repl()
    
    captured = capsys.readouterr()
    assert "Input terminated. Exiting..." in captured.out