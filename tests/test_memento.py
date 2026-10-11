import pytest
from decimal import Decimal
from app.calculator_memento import CalculatorMemento
from app.calculation import Calculation

#-----------------------------------------------
# Test cases for the CalculatorMemento class
#-----------------------------------------------

# Test to cover calculator_memento.py, line 34
def test_memento_to_dict():
    """
    Test the to_dict method of CalculatorMemento.
    This test verifies that the to_dict method correctly serializes the memento's state into a dictionary format.
    """
    # Create a Calculator instance and perform a calculation
    calc = Calculation(operation='Addition', operand1=Decimal('2'), operand2=Decimal('3'))
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    assert 'history' in data
    assert 'timestamp' in data

# Test to cover calculator_memento.py, line 53
def test_memento_from_dict():
    """
    Test the from_dict method of CalculatorMemento.
    This test verifies that the from_dict method correctly reconstructs a CalculatorMemento instance from a dictionary.
    """
    calc = Calculation(operation='Addition', operand1=Decimal('2'), operand2=Decimal('3'))
    memento = CalculatorMemento(history=[calc])
    data = memento.to_dict()
    restored_memento = CalculatorMemento.from_dict(data)
    assert len(restored_memento.history) == 1
    assert restored_memento.history[0].operation == 'Addition'


    