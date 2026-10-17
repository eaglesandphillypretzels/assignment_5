import datetime
from pathlib import Path
import pandas as pd
import pytest
from unittest.mock import Mock, patch, PropertyMock
from decimal import Decimal
from tempfile import TemporaryDirectory
from app.calculator import Calculator
from app.calculator_repl import calculator_repl
from app.calculator_config import CalculatorConfig
from app.exceptions import OperationError, ValidationError
from app.history import LoggingObserver, AutoSaveObserver
from app.operations import OperationFactory

# Fixture to initialize Calculator with a temporary directory for file paths
@pytest.fixture
def calculator():
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)

        # Patch properties to use the temporary directory paths
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
            
            # Set return values to use paths within the temporary directory
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"
            
            # Return an instance of Calculator with the mocked config
            yield Calculator(config=config)

# Test Calculator Initialization

def test_calculator_initialization(calculator):
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []
    assert calculator.operation_strategy is None

@patch('app.calculator.Calculator.load_history')
@patch('app.calculator.logging.warning')
def test_calculator_init_default_config_and_load_history_warning_once(mock_warning, mock_load_history):
    """Covers lines 103-106: Exception handling in __init__"""
    mock_load_history.side_effect = Exception("Disk read error")
    
    with TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        config = CalculatorConfig(base_dir=temp_path)
        
        with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
             patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file, \
             patch.object(CalculatorConfig, 'history_dir', new_callable=PropertyMock) as mock_history_dir, \
             patch.object(CalculatorConfig, 'history_file', new_callable=PropertyMock) as mock_history_file:
            
            mock_log_dir.return_value = temp_path / "logs"
            mock_log_file.return_value = temp_path / "logs/calculator.log"
            mock_history_dir.return_value = temp_path / "history"
            mock_history_file.return_value = temp_path / "history/calculator_history.csv"
            
            calc = Calculator(config=config)
            
            # Verify the warning was logged
            mock_warning.assert_called_with("Could not load existing history: Disk read error")
            assert isinstance(calc.config, CalculatorConfig)

@patch('app.calculator.logging.info')
def test_logging_setup(logging_info_mock):
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        
        # Instantiate calculator to trigger logging
        calculator = Calculator(CalculatorConfig())
        logging_info_mock.assert_any_call("Calculator initialized with configuration")

@patch('builtins.print')
@patch('app.calculator.os.makedirs')
def test_setup_logging_exception(mock_makedirs, mock_print):
    """Covers exception handling in _setup_logging"""
    mock_makedirs.side_effect = PermissionError("Access denied")
    
    with patch.object(CalculatorConfig, 'log_dir', new_callable=PropertyMock) as mock_log_dir, \
         patch.object(CalculatorConfig, 'log_file', new_callable=PropertyMock) as mock_log_file:
        mock_log_dir.return_value = Path('/tmp/logs')
        mock_log_file.return_value = Path('/tmp/logs/calculator.log')
        
        with pytest.raises(PermissionError):
            Calculator(CalculatorConfig())
            
        mock_print.assert_called_with("Error setting up logging: Access denied")

# Adding and Removing Observers Test

def test_add_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    assert observer in calculator.observers

def test_remove_observer(calculator):
    observer = LoggingObserver()
    calculator.add_observer(observer)
    calculator.remove_observer(observer)
    assert observer not in calculator.observers

def test_observer_notification(calculator):
    observer = Mock()
    calculator.add_observer(observer)
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    
    assert observer.update.call_count == 1
    called_calc = observer.update.call_args[0][0]
    assert called_calc.operand1 == Decimal('2')
    assert called_calc.operand2 == Decimal('3')
    assert called_calc.result == Decimal('5')

# Test Setting Operations

def test_set_operation(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    assert calculator.operation_strategy == operation

# Test Performing Operations

def test_perform_operation_addition(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    result = calculator.perform_operation(2, 3)
    assert result == Decimal('5')

def test_perform_operation_validation_error(calculator):
    calculator.set_operation(OperationFactory.create_operation('add'))
    with pytest.raises(ValidationError):
        calculator.perform_operation('invalid', 3)

def test_perform_operation_operation_error(calculator):
    with pytest.raises(OperationError, match="No operation set"):
        calculator.perform_operation(2, 3)

@patch('app.calculator.logging.error')
def test_perform_operation_generic_exception(mock_logging_error, calculator):
    mock_operation = Mock()

    """Arrange"""
    mock_operation.execute.side_effect = RuntimeError("Unexpected hardware failure")
    calculator.set_operation(mock_operation)

    """Assert"""
    with pytest.raises(OperationError, match="Operation failed: Unexpected hardware failure"):
        calculator.perform_operation(2, 3)

    """Act"""
    # Verify the generic exception handler logged the error
    mock_logging_error.assert_called_with("Operation failed: Unexpected hardware failure")

# Test Undo/Redo Functionality

def test_undo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    assert calculator.history == []

def test_redo(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.undo()
    calculator.redo()
    assert len(calculator.history) == 1

def test_undo_empty_stack(calculator):
    result = calculator.undo()
    assert result is False

def test_redo_empty_stack(calculator):
    result = calculator.redo()
    assert result is False

# Test History Management (Save)

@patch('app.calculator.pd.DataFrame.to_csv')
def test_save_history(mock_to_csv, calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    calculator.save_history()
    mock_to_csv.assert_called_once()


@patch('app.calculator.pd.DataFrame')
@patch('app.calculator.logging.info')
def test_save_history_empty(mock_logging_info, mock_dataframe, calculator):
    calculator.history = []
    calculator.save_history() 

    mock_dataframe.assert_called_once_with(columns=['operation', 'operand1', 'operand2', 'result', 'timestamp'])
    mock_dataframe.return_value.to_csv.assert_called_once_with(calculator.config.history_file, index=False)
    mock_logging_info.assert_called_with("Empty history saved")

@patch('app.calculator.pd.DataFrame.to_csv')
@patch('app.calculator.logging.error')
def test_save_history_exception(mock_logging_error, mock_to_csv, calculator):
    
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)

    mock_to_csv.side_effect = IOError("Disk full")
    
    with pytest.raises(OperationError, match="Failed to save history: Disk full"):
        calculator.save_history()
        
    mock_logging_error.assert_called_with("Failed to save history: Disk full")

# Test History Management (Load)

@patch('app.calculator.pd.read_csv')
def test_load_history(mock_read_csv, calculator):
    calculator.config.history_file.exists = Mock(return_value=True)
    mock_read_csv.return_value = pd.DataFrame({
        'operation': ['Addition'],
        'operand1': ['2'],
        'operand2': ['3'],
        'result': ['5'],
        'timestamp': [datetime.datetime.now().isoformat()]
    })

    calculator.load_history()

    assert len(calculator.history) == 1
    assert calculator.history [0].operation == "Addition"
    assert calculator.history [0].operand1 == Decimal("2")
    assert calculator.history [0].operand2 == Decimal("3")
    assert calculator.history [0].result == Decimal("5")
    
@patch('app.calculator.logging.info')
def test_load_history_file_not_found(mock_logging_info, calculator):
    calculator.config.history_file.exists = Mock(return_value=False)
    calculator.load_history()
    mock_logging_info.assert_called_with("No history file found - starting with empty history")

@patch('app.calculator.pd.read_csv')
@patch('app.calculator.logging.info')
def test_load_history_empty_dataframe(mock_logging_info, mock_read_csv, calculator):
    calculator.config.history_file.exists = Mock(return_value=True)
    mock_read_csv.return_value = pd.DataFrame() # Empty dataframe
    
    calculator.load_history()
    mock_logging_info.assert_called_with("Loaded empty history file")

@patch('app.calculator.pd.read_csv')
def test_load_history_exception(mock_read_csv, calculator):
    calculator.config.history_file.exists = Mock(return_value=True)
    mock_read_csv.side_effect = Exception("Corrupted CSV")
    
    with pytest.raises(OperationError, match="Failed to load history: Corrupted CSV"):
        calculator.load_history()

# DataFrame History Retrieval Test

def test_get_history_dataframe(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    df = calculator.get_history_dataframe()
    assert not df.empty
    assert df.iloc[0]['operation'] == 'Addition'
    assert df.iloc[0]['operand1'] == '2'
    assert df.iloc[0]['operand2'] == '3'
    assert df.iloc[0]['result'] == '5'  

# Show History Function Test

def test_show_history(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    
    history_str = calculator.show_history()

    assert len(history_str) == 1
    assert "Addition(2, 3) = 5" in history_str[0] 
            
# Clear History Function Test
def test_clear_history(calculator):
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(2, 3)
    
    calculator.clear_history()
    
    assert calculator.history == []
    assert calculator.undo_stack == []
    assert calculator.redo_stack == []

# Max History Size Enforcement Test

def test_max_history_size(calculator):
    calculator.config.max_history_size = 2
    operation = OperationFactory.create_operation('add')
    calculator.set_operation(operation)
    calculator.perform_operation(1, 1)
    calculator.perform_operation(2, 2)
    calculator.perform_operation(3, 3)  # This should trigger removal of the oldest entry
    
    assert len(calculator.history) == 2
    assert calculator.history[0].operand1 == Decimal('2')  # The first entry should be removed

# REPL Commands Test (using patches for input/output handling)

@patch('builtins.input', side_effect=['exit'])
@patch('builtins.print')
def test_calculator_repl_exit(mock_print, mock_input):
    with patch('app.calculator.Calculator.save_history') as mock_save_history:
        calculator_repl()
        mock_save_history.assert_called_once()
        mock_print.assert_any_call("History saved successfully.")
        mock_print.assert_any_call("Goodbye!")

@patch('builtins.input', side_effect=['help', 'exit'])
@patch('builtins.print')
def test_calculator_repl_help(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nAvailable commands:")

@patch('builtins.input', side_effect=['add', '2', '3', 'exit'])
@patch('builtins.print')
def test_calculator_repl_addition(mock_print, mock_input):
    calculator_repl()
    mock_print.assert_any_call("\nResult: 5")
