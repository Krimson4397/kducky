"""Tests for the DEFINE preprocessor (``src/ducky/preprocessor.py``)."""

import pytest

from ducky.preprocessor import Preprocessor, PreprocessorError


class TestPreprocessor:
    """Compile-time DEFINE constant substitution."""

    def make(self) -> Preprocessor:
        return Preprocessor()

    def preprocess(self, source: str) -> str:
        return self.make().preprocess(source)

    # ── Basic DEFINE substitution ─────────────────────────────────────

    def test_define_integer_value(self) -> None:
        """DEFINE #DELAY 2000 → DELAY 2000."""
        result = self.preprocess("DEFINE #DELAY 2000\nDELAY #DELAY\n")
        assert result == "\nDELAY 2000\n"

    def test_define_multi_word_value(self) -> None:
        """DEFINE #TEXT Hello World → STRINGLN Hello World."""
        result = self.preprocess("DEFINE #TEXT Hello World\nSTRINGLN #TEXT\n")
        assert result == "\nSTRINGLN Hello World\n"

    def test_define_in_string_body(self) -> None:
        """#NAME is substituted inside STRING body text."""
        result = self.preprocess(
            'DEFINE #URL example.com\nSTRING https://#URL/path\n'
        )
        assert result == "\nSTRING https://example.com/path\n"

    def test_define_multiple_refs_one_line(self) -> None:
        """Multiple #NAME references on the same line."""
        result = self.preprocess(
            'DEFINE #HOST a\nDEFINE #PORT 8080\nSTRING #HOST:#PORT\n'
        )
        assert result == "\n\nSTRING a:8080\n"

    def test_define_empty_value(self) -> None:
        """DEFINE #X with no value yields empty string for #X."""
        result = self.preprocess("DEFINE #X\nSTRING #X\n")
        assert result == "\nSTRING \n"

    # ── DEFINE line removal ───────────────────────────────────────────

    def test_define_line_replaced_with_blank(self) -> None:
        """DEFINE lines are replaced with blank lines."""
        result = self.preprocess("DEFINE #X 1\nDELAY 100\n")
        assert result == "\nDELAY 100\n"

    def test_multiple_defines_become_blanks(self) -> None:
        """Multiple consecutive DEFINE lines all become blanks."""
        result = self.preprocess(
            "DEFINE #A 1\nDEFINE #B 2\nDEFINE #C 3\nSTRING done\n"
        )
        assert result == "\n\n\nSTRING done\n"

    # ── Case insensitivity ────────────────────────────────────────────

    def test_define_keyword_lowercase(self) -> None:
        """DEFINE keyword is case-insensitive (lowercase)."""
        result = self.preprocess("define #X 42\nDELAY #X\n")
        assert result == "\nDELAY 42\n"

    def test_define_keyword_mixed_case(self) -> None:
        """DEFINE keyword is case-insensitive (mixed case)."""
        result = self.preprocess("Define #X 99\nDELAY #X\n")
        assert result == "\nDELAY 99\n"

    # ── Quoted string protection ──────────────────────────────────────

    def test_hash_in_quoted_string_not_substituted(self) -> None:
        """#NAME inside \"...\" is NOT substituted."""
        result = self.preprocess(
            'DEFINE #X value\nSTRING "#X"\n'
        )
        assert result == '\nSTRING "#X"\n'

    def test_hash_in_expression_string_not_substituted(self) -> None:
        """#NAME inside quoted expression string is preserved."""
        result = self.preprocess(
            'DEFINE #X 42\nVAR $a = "#X"\n'
        )
        assert result == '\nVAR $a = "#X"\n'

    def test_escaped_quote_in_string(self) -> None:
        r"""Quoted string with \" escape still protects #NAME."""
        result = self.preprocess(
            'DEFINE #X 42\nVAR $a = "hello \\"#X\\""\n'
        )
        assert result == '\nVAR $a = "hello \\"#X\\""\n'

    def test_hash_at_start_of_quoted_string(self) -> None:
        """# at the very start of a quoted string is not substituted."""
        result = self.preprocess(
            'DEFINE #X 42\nVAR $a = "#"\n'
        )
        assert result == '\nVAR $a = "#"\n'

    # ── Error conditions ──────────────────────────────────────────────

    def test_undefined_constant_error(self) -> None:
        """Undefined #NAME raises PreprocessorError."""
        with pytest.raises(PreprocessorError, match="Undefined constant '#X'"):
            self.preprocess("DELAY #X\n")

    def test_define_without_hash(self) -> None:
        """DEFINE without # raises error."""
        with pytest.raises(PreprocessorError, match="Expected #NAME"):
            self.preprocess("DEFINE X 42\n")

    def test_define_hash_without_name(self) -> None:
        """DEFINE # without name raises error."""
        with pytest.raises(PreprocessorError, match="Expected #NAME"):
            self.preprocess("DEFINE #\n")

    def test_define_keyword_only(self) -> None:
        """Just DEFINE with nothing after raises error."""
        with pytest.raises(PreprocessorError, match="Expected #NAME"):
            self.preprocess("DEFINE\n")

    # ── Edge cases ────────────────────────────────────────────────────

    def test_hash_not_identifier_bypasses_substitution(self) -> None:
        """# not followed by alpha/_ is left as-is."""
        result = self.preprocess("DELAY #\n")
        assert result == "DELAY #\n"

    def test_partial_name_match(self) -> None:
        """#MYCONST should not match #MYCONSTANT."""
        with pytest.raises(PreprocessorError):
            self.preprocess("DEFINE #MYCONST 10\nDELAY #MYCONSTANT\n")

    def test_define_used_immediately_after(self) -> None:
        """#NAME usable on the very next line after DEFINE."""
        result = self.preprocess("DEFINE #X 5\nSTRING value=#X\n")
        assert result == "\nSTRING value=5\n"

    def test_define_not_usable_before_definition(self) -> None:
        """#NAME used before DEFINE line is undefined."""
        with pytest.raises(PreprocessorError, match="Undefined constant '#X'"):
            self.preprocess("STRING #X\nDEFINE #X 5\n")

    def test_preprocess_twice_clears_state(self) -> None:
        """Calling preprocess() on a second source clears old defines."""
        p = self.make()
        p.preprocess("DEFINE #X 1\nSTRING #X\n")
        # Second call with different source should not have #X defined
        with pytest.raises(PreprocessorError, match="Undefined constant '#X'"):
            p.preprocess("STRING #X\n")

    def test_blank_and_comment_lines_preserved(self) -> None:
        """Blank lines and REM lines are left unchanged."""
        result = self.preprocess(
            "DEFINE #X 1\n\nREM hello\nSTRING #X\n"
        )
        assert result == "\n\nREM hello\nSTRING 1\n"

    def test_no_defines_no_changes(self) -> None:
        """Source without DEFINE or # is returned unchanged."""
        source = "STRING hello\nDELAY 100\n"
        result = self.preprocess(source)
        assert result == source

    def test_multiple_define_values(self) -> None:
        """Several DEFINEs with different value types."""
        source = (
            "DEFINE #DELAY_VAL 500\n"
            "DEFINE #MSG Hello World\n"
            "DEFINE #COUNT 42\n"
            "DELAY #DELAY_VAL\n"
            "STRINGLN #MSG\n"
            "VAR $x = #COUNT\n"
        )
        result = self.preprocess(source)
        assert result == (
            "\n\n\n"
            "DELAY 500\n"
            "STRINGLN Hello World\n"
            "VAR $x = 42\n"
        )
