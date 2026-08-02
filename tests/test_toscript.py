from pathlib import Path

import pytest

from temperamento.errors import StaticError
from temperamento.toscript import parse_tos, parse_tos_plus, to_tos_plus


def test_parse_core_canonicalises_case_and_comments() -> None:
    program = parse_tos("push 7 # value\npush 5\nadd\nout\nend\n")
    assert program.to_tos() == "PUSH 7\nPUSH 5\nADD\nOUT\nEND\n"


def test_toscript_plus_lowers_constants_named_labels_and_sugar() -> None:
    program = parse_tos_plus(
        """
        let start = 3
        push start
        loop:
        dup
        output
        push 1
        sub
        dup
        jump-if loop
        pop
        end
        """
    )
    assert program.to_tos() == ("PUSH 3\nLBL 0\nDUP\nOUT\nPUSH 1\nSUB\nDUP\nJMC 0\nPOP\nEND\n")


def test_toscript_plus_print_lowers_to_unicode_output() -> None:
    program = parse_tos_plus('print "Hi\\n"\nend\n')
    assert program.to_tos() == "PUSH 72\nOUT\nPUSH 105\nOUT\nPUSH 10\nOUT\nEND\n"


def test_toscript_plus_pretty_print_round_trip() -> None:
    core = parse_tos("PUSH 2\nLBL 9\nDUP\nOUT\nPUSH 1\nSUB\nDUP\nJMC 9\nPOP\nEND\n")
    pretty = to_tos_plus(core)
    assert parse_tos_plus(pretty).to_tos() == core.to_tos()


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("NOPE\n", "unknown TOScript operation"),
        ("PUSH\n", "expects 1 operand"),
        ("PUSH -1\n", "must be non-negative"),
        ("JMP 1\n", "undefined label"),
        ("LBL 1\nLBL 1\n", "duplicate label"),
    ],
)
def test_core_rejects_invalid_programs(source: str, message: str) -> None:
    with pytest.raises(StaticError, match=message):
        parse_tos(source)


def test_plus_rejects_undefined_symbolic_label() -> None:
    with pytest.raises(StaticError, match="undefined label"):
        parse_tos_plus("jump missing\nend\n")


def test_file_errors_are_user_facing(tmp_path: Path) -> None:
    from temperamento.toscript import parse_tos_file

    with pytest.raises(StaticError, match="cannot read TOScript"):
        parse_tos_file(tmp_path / "missing.tos")


def test_core_file_success_and_empty_source(tmp_path: Path) -> None:
    from temperamento.toscript import parse_tos_file

    source = tmp_path / "program.tos"
    source.write_text("PUSH 1\nOUT\nEND\n", encoding="utf-8")
    assert parse_tos_file(source).source == str(source)
    with pytest.raises(StaticError, match="contains no instructions"):
        parse_tos("# comment only\n")


def test_core_rejects_non_decimal_operand() -> None:
    with pytest.raises(StaticError, match="decimal integer"):
        parse_tos("PUSH value\n")


@pytest.mark.parametrize(
    ("source", "message"),
    [
        ("let broken\nend\n", "expected `let NAME = INTEGER`"),
        ("let x = 1\nlet x = 2\nend\n", "duplicate constant"),
        ("bad label!:\nend\n", "invalid label name"),
        ("label\nend\n", "label expects one name"),
        ("label bad label\nend\n", "invalid label name"),
        ("same:\nsame:\nend\n", "duplicate label"),
        ("push\nend\n", "expects one argument"),
        ("jump\nend\n", "expects one argument"),
        ("print 12\nend\n", "quoted string"),
        ("print not-a-string\nend\n", "quoted string"),
        ("add 1\nend\n", "takes no arguments"),
        ("unknown\n", r"unknown TOScript\+ operation"),
        ("# empty\n", "contains no executable instructions"),
    ],
)
def test_plus_rejects_invalid_sources(source: str, message: str) -> None:
    with pytest.raises(StaticError, match=message):
        parse_tos_plus(source)


def test_plus_numeric_labels_aliases_and_output_value() -> None:
    program = parse_tos_plus(
        """
        label 0
        named:
        output 7
        jmp named
        """
    )
    assert program.to_tos() == "LBL 0\nLBL 1\nPUSH 7\nOUT\nJMP 1\n"
    assert to_tos_plus(program) == "0:\n1:\npush 7\noutput\njump 1\n"


def test_plus_file_success_and_error(tmp_path: Path) -> None:
    from temperamento.toscript import parse_tos_plus_file

    source = tmp_path / "program.tom"
    source.write_text("output 1\nend\n", encoding="utf-8")
    assert parse_tos_plus_file(source).source == str(source)
    with pytest.raises(StaticError, match=r"cannot read TOScript\+"):
        parse_tos_plus_file(tmp_path / "missing.tom")
