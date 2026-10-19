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

