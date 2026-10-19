import pytest
from unittest.mock import patch, MagicMock
from decimal import Decimal
from app.calculator_repl import calculator_repl
from app.exceptions import OperationError, ValidationError

# History Save Test
"""Covers lines 54-55: printing out successful history save message"""
def test_history_saved(capsys):
    with patch('builtins.input', side_effect=['save', 'exit']):
        calculator_repl()
    captured = capsys.readouterr()
    assert "History saved successfully" in captured.out
