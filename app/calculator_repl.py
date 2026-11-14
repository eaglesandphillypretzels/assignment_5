########################
# Calculator REPL       #
########################

from decimal import Decimal
import logging

from app.calculator import Calculator
from app.exceptions import OperationError, ValidationError
from app.history import AutoSaveObserver, LoggingObserver
from app.operations import OperationFactory
from colorama import Fore, just_fix_windows_console

just_fix_windows_console()

def calculator_repl():
    """
    Command-line interface for the calculator.

    Implements a Read-Eval-Print Loop (REPL) that continuously prompts the user
    for commands, processes arithmetic operations, and manages calculation history.
    """
    try:
        # Initialize the Calculator instance
        calc = Calculator()

        # Register observers for logging and auto-saving history
        calc.add_observer(LoggingObserver())
        calc.add_observer(AutoSaveObserver(calc))
        
        print(Fore.MAGENTA + "Calculator started. Type 'help' for commands.")

        while True:
            try:
                # Prompt the user for a command
                command = input(Fore.LIGHTMAGENTA_EX + "\nEnter command: ").lower().strip()

                if command == 'help':
                    # Display available commands
                    print(Fore.WHITE + "\nAvailable commands:")
                    print("  add, subtract, multiply, divide, power, root, modulus, absolute difference - Perform calculations")
                    print("  history - Show calculation history")
                    print("  clear - Clear calculation history")
                    print("  undo - Undo the last calculation")
                    print("  redo - Redo the last undone calculation")
                    print("  save - Save calculation history to file")
                    print("  load - Load calculation history from file")
                    print("  exit - Exit the calculator")
                    continue

                if command == 'exit':
                    # Attempt to save history before exiting
                    try:
                        calc.save_history()
                        print(Fore.LIGHTBLUE_EX + "History saved successfully.")
                    except Exception as e:
                        print(Fore.LIGHTRED_EX + f"Warning: Could not save history: {e}")
                    print(Fore.LIGHTBLUE_EX + "Goodbye!")
                    break

                if command == 'history':
                    # Display calculation history
                    history = calc.show_history()
                    if not history:
                        print(Fore.YELLOW + "No calculations in history")
                    else:
                        print(Fore.YELLOW + "\nCalculation History:")
                        for i, entry in enumerate(history, 1):
                            print(f"{i}. {entry}")
                    continue

                if command == 'clear':
                    # Clear calculation history
                    calc.clear_history()
                    print(Fore.YELLOW + "History cleared")
                    continue

                if command == 'undo':
                    # Undo the last calculation
                    if calc.undo():
                        print(Fore.CYAN + "Operation undone")
                    else:
                        print("Nothing to undo")
                    continue

                if command == 'redo':
                    # Redo the last undone calculation
                    if calc.redo():
                        print(Fore.CYAN + "Operation redone")
                    else:
                        print(Fore.CYAN + "Nothing to redo")
                    continue

                if command == 'save':
                    # Save calculation history to file
                    try:
                        calc.save_history()
                        print(Fore.YELLOW + "History saved successfully")
                    except Exception as e:
                        print(Fore.LIGHTRED_EX + f"Error saving history: {e}")
                    continue

                if command == 'load':
                    # Load calculation history from file
                    try:
                        calc.load_history()
                        print(Fore.YELLOW + "History loaded successfully")
                    except Exception as e:
                        print(Fore.LIGHTRED_EX + f"Error loading history: {e}")
                    continue

                if command in ['add', 'subtract', 'multiply', 'divide', 'power', 'root', 'modulus', 'modulo', '%', 'absolute difference', 'absdiff', 'percent']:
                    # Perform the specified arithmetic operation
                    try:
                        print(Fore.LIGHTCYAN_EX + "\nEnter numbers (or 'cancel' to abort):")
                        a = input("First number: ")
                        if a.lower() == 'cancel':
                            print("Operation cancelled")
                            continue
                        b = input("Second number: ")
                        if b.lower() == 'cancel':
                            print("Operation cancelled")
                            continue

                        # Create the appropriate operation instance using the Factory pattern
                        operation = OperationFactory.create_operation(command)
                        calc.set_operation(operation)

                        # Perform the calculation
                        result = calc.perform_operation(a, b)

                        # Normalize the result if it's a Decimal
                        if isinstance(result, Decimal):
                            result = result.normalize()

                        print(Fore.GREEN + f"\nResult: {result}")
                    except (ValidationError, OperationError) as e:
                        # Handle known exceptions related to validation or operation errors
                        print(Fore.LIGHTRED_EX + f"Error: {e}")
                    except Exception as e:
                        # Handle any unexpected exceptions
                        print(Fore.LIGHTRED_EX + f"Unexpected error: {e}")
                    continue

                # Handle unknown commands
                print(Fore.LIGHTRED_EX + f"Unknown command: '{command}'. Type 'help' for available commands.")

            except KeyboardInterrupt:
                # Handle Ctrl+C interruption gracefully
                print(Fore.LIGHTRED_EX + "\nOperation cancelled")
                continue
            except EOFError:
                # Handle end-of-file (e.g., Ctrl+D) gracefully
                print(Fore.LIGHTYELLOW_EX + "\nInput terminated. Exiting...")
                break
            except Exception as e:
                # Handle any other unexpected exceptions
                print(Fore.LIGHTRED_EX + f"Error: {e}")
                continue

    except Exception as e:
        # Handle fatal errors during initialization
        print(Fore.LIGHTRED_EX + f"Fatal error: {e}")
        logging.error(f"Fatal error in calculator REPL: {e}")
        raise
