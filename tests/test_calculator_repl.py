import unittest
from unittest.mock import patch, MagicMock, call
import sys
from io import StringIO
from decimal import Decimal

from app.calculator_repl import calculator_repl
from app.exceptions import OperationError, ValidationError
