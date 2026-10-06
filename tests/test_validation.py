import pytest

from client import validate_inputs


class TestValidInputs:
    def test_single_lowercase_word(self):
        validate_inputs(["hello"])

    def test_multiple_lowercase_words(self):
        validate_inputs(["hello", "world"])

    def test_single_letter(self):
        validate_inputs(["a"])

    def test_full_alphabet(self):
        validate_inputs(["abcdefghijklmnopqrstuvwxyz"])


class TestUppercaseRejected:
    def test_fully_uppercase(self):
        with pytest.raises(ValueError):
            validate_inputs(["HELLO"])

    def test_mixed_case(self):
        with pytest.raises(ValueError):
            validate_inputs(["Hello"])

    def test_single_uppercase_letter(self):
        with pytest.raises(ValueError):
            validate_inputs(["heLlo"])


class TestNonAlphaRejected:
    def test_digit_in_string(self):
        with pytest.raises(ValueError):
            validate_inputs(["hello1"])

    def test_space_in_string(self):
        with pytest.raises(ValueError):
            validate_inputs(["he llo"])

    def test_special_character(self):
        with pytest.raises(ValueError):
            validate_inputs(["hello!"])

    def test_hyphen(self):
        with pytest.raises(ValueError):
            validate_inputs(["hello-world"])

    def test_only_digits(self):
        with pytest.raises(ValueError):
            validate_inputs(["123"])


class TestEmptyInputRejected:
    def test_empty_list(self):
        with pytest.raises(ValueError):
            validate_inputs([])


class TestMixedListRejected:
    def test_one_invalid_string_in_otherwise_valid_list(self):
        with pytest.raises(ValueError):
            validate_inputs(["hello", "Hello", "world"])

    def test_invalid_at_start(self):
        with pytest.raises(ValueError):
            validate_inputs(["Hello", "world"])

    def test_invalid_at_end(self):
        with pytest.raises(ValueError):
            validate_inputs(["hello", "world", "bad1"])
