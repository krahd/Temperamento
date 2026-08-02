"""Temperamento reference implementation."""

from .compiler import compile_musicxml, compile_score
from .interpreter import Interpreter, RuntimeResult
from .notation import program_to_musicxml, write_musicxml
from .toscript import parse_tos, parse_tos_plus, to_tos_plus
from .universality import (
    DecrementJump,
    Halt,
    Increment,
    compile_two_counter_machine,
)

__all__ = [
    "DecrementJump",
    "Halt",
    "Increment",
    "Interpreter",
    "RuntimeResult",
    "compile_musicxml",
    "compile_score",
    "compile_two_counter_machine",
    "parse_tos",
    "parse_tos_plus",
    "program_to_musicxml",
    "to_tos_plus",
    "write_musicxml",
]
__version__ = "0.5.0"
