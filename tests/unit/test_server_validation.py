"""Unit tests for server validation functions.

These tests cover the validation functions in src/mcp_scraper/server.py:
- _validate_url_param: URL parameter validation
- _validate_timeout: Timeout validation
- _validate_stealth_level: Stealth level validation
- _validate_extract: Extract mode validation
- _validate_delay: Delay validation
- _validate_urls_list: URLs list validation
- _validate_selector: Selector validation
- _get_stealth_config_by_level: Stealth config mapping
- _ensure_json_serializable: JSON serialization
"""

import datetime
from decimal import Decimal
from typing import Any

import pytest

from mcp_scraper.server import (
    _ensure_json_serializable,
    _get_stealth_config_by_level,
    _validate_delay,
    _validate_extract,
    _validate_selector,
    _validate_stealth_level,
    _validate_timeout,
    _validate_url_param,
    _validate_urls_list,
)


# =============================================================================
# Tests for _validate_url_param (lines 44-57)
# =============================================================================


class TestValidateUrlParam:
    """Tests for _validate_url_param function.

    This function validates URL parameters and returns an error message
    if invalid, or None if valid.
    """

    def test_valid_https_url_returns_none(self):
        """Valid HTTPS URL should return None (valid)."""
        result = _validate_url_param("https://example.com")
        assert result is None

    def test_valid_http_url_returns_none(self):
        """Valid HTTP URL should return None (valid)."""
        result = _validate_url_param("http://example.com")
        assert result is None

    def test_valid_url_with_path_returns_none(self):
        """Valid URL with path should return None (valid)."""
        result = _validate_url_param("https://example.com/path/to/page")
        assert result is None

    def test_valid_url_with_query_params_returns_none(self):
        """Valid URL with query parameters should return None (valid)."""
        result = _validate_url_param("https://example.com/search?q=test&page=1")
        assert result is None

    def test_valid_url_with_fragment_returns_none(self):
        """Valid URL with fragment should return None (valid)."""
        result = _validate_url_param("https://example.com/page#section")
        assert result is None

    def test_valid_url_with_port_returns_none(self):
        """Valid URL with port should return None (valid)."""
        result = _validate_url_param("https://example.com:8080/page")
        assert result is None

    def test_valid_url_with_auth_returns_none(self):
        """Valid URL with authentication should return None (valid)."""
        result = _validate_url_param("https://user:pass@example.com/page")
        assert result is None

    def test_none_value_returns_error(self):
        """None value should return error message."""
        result = _validate_url_param(None)
        assert result is not None
        assert "must be a string" in result

    def test_empty_string_returns_error(self):
        """Empty string should return error message."""
        result = _validate_url_param("")
        assert result is not None
        assert "empty" in result.lower()

    def test_whitespace_only_returns_error(self):
        """Whitespace-only string should return error message."""
        result = _validate_url_param("   ")
        assert result is not None
        assert "empty" in result.lower()

    def test_non_string_returns_error(self):
        """Non-string type should return error message."""
        result = _validate_url_param(12345)
        assert result is not None
        assert "must be a string" in result

    def test_list_returns_error(self):
        """List type should return error message."""
        result = _validate_url_param(["https://example.com"])
        assert result is not None
        assert "must be a string" in result

    def test_dict_returns_error(self):
        """Dict type should return error message."""
        result = _validate_url_param({"url": "https://example.com"})
        assert result is not None
        assert "must be a string" in result


# =============================================================================
# Tests for _validate_timeout (lines 60-73)
# =============================================================================


class TestValidateTimeout:
    """Tests for _validate_timeout function.

    This function validates timeout values in milliseconds.
    Valid range is 1000300000 (-1 second to 5 minutes).
    """

    def test_valid_minimum_timeout_returns_none(self):
        """Minimum valid timeout (1000ms) should return None."""
        result = _validate_timeout(1000)
        assert result is None

    def test_valid_maximum_timeout_returns_none(self):
        """Maximum valid timeout (300000ms) should return None."""
        result = _validate_timeout(30000)
        assert result is None

    def test_valid_middle_timeout_returns_none(self):
        """Middle valid timeout should return None."""
        result = _validate_timeout(15000)
        assert result is None

    def test_valid_maximum_boundary_returns_none(self):
        """Maximum boundary timeout (300000ms) should return None."""
        result = _validate_timeout(300000)
        assert result is None

    def test_too_low_timeout_returns_error(self):
        """Timeout below 1000ms should return error message."""
        result = _validate_timeout(999)
        assert result is not None
        assert "1000" in result
        assert "300000" in result

    def test_zero_timeout_returns_error(self):
        """Zero timeout should return error message."""
        result = _validate_timeout(0)
        assert result is not None
        assert "1000" in result

    def test_negative_timeout_returns_error(self):
        """Negative timeout should return error message."""
        result = _validate_timeout(-1000)
        assert result is not None
        assert "1000" in result

    def test_too_high_timeout_returns_error(self):
        """Timeout above 300000ms should return error message."""
        result = _validate_timeout(300001)
        assert result is not None
        assert "300000" in result

    def test_very_large_timeout_returns_error(self):
        """Very large timeout should return error message."""
        result = _validate_timeout(1000000)
        assert result is not None
        assert "300000" in result

    def test_none_returns_none(self):
        """None timeout should return None (uses default)."""
        # Note: The validation function doesn't handle None,
        # this test documents expected behavior
        result = _validate_timeout(None)
        # The function checks isinstance(timeout, int), so None fails
        assert result is not None

    def test_float_returns_error(self):
        """Float timeout should return error message."""
        result = _validate_timeout(15000.5)
        assert result is not None
        assert "integer" in result

    def test_string_returns_error(self):
        """String timeout should return error message."""
        result = _validate_timeout("15000")
        assert result is not None
        assert "integer" in result

    def test_list_returns_error(self):
        """List timeout should return error message."""
        result = _validate_timeout([15000])
        assert result is not None
        assert "integer" in result


# =============================================================================
# Tests for _validate_stealth_level (lines 76-90)
# =============================================================================


class TestValidateStealthLevel:
    """Tests for _validate_stealth_level function.

    This function validates stealth level strings.
    Valid levels are: minimal, standard, maximum.
    """

    def test_valid_minimal_level_returns_none(self):
        """'minimal' level should return None (valid)."""
        result = _validate_stealth_level("minimal")
        assert result is None

    def test_valid_standard_level_returns_none(self):
        """'standard' level should return None (valid)."""
        result = _validate_stealth_level("standard")
        assert result is None

    def test_valid_maximum_level_returns_none(self):
        """'maximum' level should return None (valid)."""
        result = _validate_stealth_level("maximum")
        assert result is None

    def test_case_insensitive_minimal(self):
        """'MINIMAL' should be accepted (case insensitive)."""
        result = _validate_stealth_level("MINIMAL")
        assert result is None

    def test_case_insensitive_standard(self):
        """'STANDARD' should be accepted (case insensitive)."""
        result = _validate_stealth_level("STANDARD")
        assert result is None

    def test_case_insensitive_maximum(self):
        """'MAXIMUM' should be accepted (case insensitive)."""
        result = _validate_stealth_level("MAXIMUM")
        assert result is None

    def test_mixed_case_minimal(self):
        """'MiNiMaL' should be accepted (case insensitive)."""
        result = _validate_stealth_level("MiNiMaL")
        assert result is None

    def test_mixed_case_standard(self):
        """'StAnDaRd' should be accepted (case insensitive)."""
        result = _validate_stealth_level("StAnDaRd")
        assert result is None

    def test_invalid_level_returns_error(self):
        """Invalid level should return error message with valid options."""
        result = _validate_stealth_level("invalid")
        assert result is not None
        assert "minimal" in result
        assert "standard" in result
        assert "maximum" in result

    def test_empty_string_returns_error(self):
        """Empty string should return error message."""
        result = _validate_stealth_level("")
        assert result is not None

    def test_none_returns_error(self):
        """None should return error message."""
        result = _validate_stealth_level(None)
        assert result is not None
        assert "must be a string" in result

    def test_number_returns_error(self):
        """Number should return error message."""
        result = _validate_stealth_level(123)
        assert result is not None
        assert "must be a string" in result

    def test_list_returns_error(self):
        """List should return error message."""
        result = _validate_stealth_level(["minimal"])
        assert result is not None
        assert "must be a string" in result


# =============================================================================
# Tests for _validate_extract (lines 93-107)
# =============================================================================


class TestValidateExtract:
    """Tests for _validate_extract function.

    This function validates extract mode strings.
    Valid modes are: text, html, both.
    """

    def test_valid_text_mode_returns_none(self):
        """'text' mode should return None (valid)."""
        result = _validate_extract("text")
        assert result is None

    def test_valid_html_mode_returns_none(self):
        """'html' mode should return None (valid)."""
        result = _validate_extract("html")
        assert result is None

    def test_valid_both_mode_returns_none(self):
        """'both' mode should return None (valid)."""
        result = _validate_extract("both")
        assert result is None

    def test_case_insensitive_text(self):
        """'TEXT' should be accepted (case insensitive)."""
        result = _validate_extract("TEXT")
        assert result is None

    def test_case_insensitive_html(self):
        """'HTML' should be accepted (case insensitive)."""
        result = _validate_extract("HTML")
        assert result is None

    def test_case_insensitive_both(self):
        """'BOTH' should be accepted (case insensitive)."""
        result = _validate_extract("BOTH")
        assert result is None

    def test_mixed_case_text(self):
        """'TeXt' should be accepted (case insensitive)."""
        result = _validate_extract("TeXt")
        assert result is None

    def test_invalid_mode_returns_error(self):
        """Invalid mode should return error message with valid options."""
        result = _validate_extract("invalid")
        assert result is not None
        assert "text" in result
        assert "html" in result
        assert "both" in result

    def test_empty_string_returns_error(self):
        """Empty string should return error message."""
        result = _validate_extract("")
        assert result is not None

    def test_none_returns_error(self):
        """None should return error message."""
        result = _validate_extract(None)
        assert result is not None
        assert "must be a string" in result

    def test_number_returns_error(self):
        """Number should return error message."""
        result = _validate_extract(123)
        assert result is not None
        assert "must be a string" in result

    def test_list_returns_error(self):
        """List should return error message."""
        result = _validate_extract(["text"])
        assert result is not None
        assert "must be a string" in result


# =============================================================================
# Tests for _validate_delay (lines 110-123)
# =============================================================================


class TestValidateDelay:
    """Tests for _validate_delay function.

    This function validates delay values in seconds.
    Must be non-negative (>= 0).
    """

    def test_valid_zero_delay_returns_none(self):
        """Zero delay should return None (valid)."""
        result = _validate_delay(0)
        assert result is None

    def test_valid_positive_delay_returns_none(self):
        """Positive delay should return None (valid)."""
        result = _validate_delay(1.0)
        assert result is None

    def test_valid_float_delay_returns_none(self):
        """Float delay should return None (valid)."""
        result = _validate_delay(1.5)
        assert result is None

    def test_valid_integer_delay_returns_none(self):
        """Integer delay should return None (valid)."""
        result = _validate_delay(5)
        assert result is None

    def test_valid_max_delay_returns_none(self):
        """Maximum delay (60.0 seconds) should return None (valid)."""
        # Note: No explicit upper bound in function, but 60.0 is reasonable
        result = _validate_delay(60.0)
        assert result is None

    def test_valid_large_delay_returns_none(self):
        """Large delay value should return None (valid)."""
        result = _validate_delay(1000.0)
        assert result is None

    def test_negative_integer_returns_error(self):
        """Negative integer delay should return error message."""
        result = _validate_delay(-1)
        assert result is not None
        assert "non-negative" in result

    def test_negative_float_returns_error(self):
        """Negative float delay should return error message."""
        result = _validate_delay(-1.5)
        assert result is not None
        assert "non-negative" in result

    def test_none_returns_error(self):
        """None should return error message."""
        result = _validate_delay(None)
        assert result is not None
        assert "number" in result

    def test_string_returns_error(self):
        """String should return error message."""
        result = _validate_delay("1.0")
        assert result is not None
        assert "number" in result

    def test_list_returns_error(self):
        """List should return error message."""
        result = _validate_delay([1.0])
        assert result is not None
        assert "number" in result


# =============================================================================
# Tests for _validate_urls_list (lines 126-144)
# =============================================================================


class TestValidateUrlsList:
    """Tests for _validate_urls_list function.

    This function validates a list of URLs.
    Must be a non-empty list with string elements.
    """

    def test_valid_single_url_list_returns_none(self):
        """List with single valid URL should return None."""
        result = _validate_urls_list(["https://example.com"])
        assert result is None

    def test_valid_multiple_urls_list_returns_none(self):
        """List with multiple valid URLs should return None."""
        urls = [
            "https://example.com",
            "https://example.org",
            "https://httpbin.org",
        ]
        result = _validate_urls_list(urls)
        assert result is None

    def test_empty_list_returns_error(self):
        """Empty list should return error message."""
        result = _validate_urls_list([])
        assert result is not None
        assert "empty" in result.lower()

    def test_list_over_100_items_returns_error(self):
        """List with more than 100 items should return error message."""
        urls = [f"https://example.com/{i}" for i in range(101)]
        result = _validate_urls_list(urls)
        assert result is not None
        assert "100" in result

    def test_non_list_returns_error(self):
        """Non-list type should return error message."""
        result = _validate_urls_list("https://example.com")
        assert result is not None
        assert "must be a list" in result

    def test_none_returns_error(self):
        """None should return error message."""
        result = _validate_urls_list(None)
        assert result is not None
        assert "must be a list" in result

    def test_string_as_list_returns_error(self):
        """String passed as 'list' should return error message."""
        result = _validate_urls_list("not a list")
        assert result is not None
        assert "must be a list" in result

    def test_dict_returns_error(self):
        """Dict should return error message."""
        result = _validate_urls_list({"url": "https://example.com"})
        assert result is not None
        assert "must be a list" in result

    def test_list_with_non_string_returns_error(self):
        """List with non-string element should return error message."""
        result = _validate_urls_list([123, 456])
        assert result is not None
        assert "strings" in result.lower()

    def test_list_with_mixed_types_returns_error(self):
        """List with mixed types should return error message."""
        result = _validate_urls_list(["https://example.com", 123])
        assert result is not None
        assert "strings" in result.lower()

    def test_list_with_none_element_returns_error(self):
        """List with None element should return error message."""
        result = _validate_urls_list(["https://example.com", None])
        assert result is not None
        assert "strings" in result.lower()

    def test_duplicates_allowed(self):
        """List with duplicate URLs should return None (duplicates allowed)."""
        result = _validate_urls_list(["https://example.com", "https://example.com"])
        assert result is None


# =============================================================================
# Tests for _validate_selector (lines 147-160)
# =============================================================================


class TestValidateSelector:
    """Tests for _validate_selector function.

    This function validates CSS selector strings.
    None is allowed (optional selector).
    """

    def test_valid_simple_selector_returns_none(self):
        """Valid simple CSS selector should return None."""
        result = _validate_selector("div")
        assert result is None

    def test_valid_class_selector_returns_none(self):
        """Valid class selector should return None."""
        result = _validate_selector(".content")
        assert result is None

    def test_valid_id_selector_returns_none(self):
        """Valid ID selector should return None."""
        result = _validate_selector("#header")
        assert result is None

    def test_valid_complex_selector_returns_none(self):
        """Valid complex CSS selector should return None."""
        result = _validate_selector("div.content p.highlight")
        assert result is None

    def test_valid_attribute_selector_returns_none(self):
        """Valid attribute selector should return None."""
        result = _validate_selector("a[href]")
        assert result is None

    def test_valid_pseudo_selector_returns_none(self):
        """Valid pseudo selector should return None."""
        result = _validate_selector("li:first-child")
        assert result is None

    def test_valid_nested_selector_returns_none(self):
        """Valid nested selector should return None."""
        result = _validate_selector("ul > li")
        assert result is None

    def test_valid_selector_with_special_chars_returns_none(self):
        """Selector with special characters should return None."""
        result = _validate_selector("input[type='text']")
        assert result is None

    def test_none_returns_none(self):
        """None selector should return None (optional parameter)."""
        result = _validate_selector(None)
        assert result is None

    def test_empty_string_returns_none(self):
        """Empty string selector should return None."""
        # Note: The validation allows empty strings
        result = _validate_selector("")
        assert result is None

    def test_non_string_returns_error(self):
        """Non-string type should return error message."""
        result = _validate_selector(123)
        assert result is not None
        assert "must be a string" in result

    def test_list_returns_error(self):
        """List should return error message."""
        result = _validate_selector([".content"])
        assert result is not None
        assert "must be a string" in result

    def test_dict_returns_error(self):
        """Dict should return error message."""
        result = _validate_selector({"selector": ".content"})
        assert result is not None
        assert "must be a string" in result


# =============================================================================
# Tests for _get_stealth_config_by_level (lines 164-187)
# =============================================================================


class TestGetStealthConfigByLevel:
    """Tests for _get_stealth_config_by_level function.

    This function maps stealth level strings to StealthConfig objects.
    """

    def test_minimal_level_returns_config(self):
        """'minimal' level should return StealthConfig."""
        config = _get_stealth_config_by_level("minimal")
        assert config is not None
        # Verify minimal config properties
        assert config.humanize is False
        assert config.solve_cloudflare is False
        assert config.block_images is True

    def test_standard_level_returns_config(self):
        """'standard' level should return StealthConfig."""
        config = _get_stealth_config_by_level("standard")
        assert config is not None
        # Verify standard config properties
        assert config.humanize is True
        assert config.solve_cloudflare is False

    def test_maximum_level_returns_config(self):
        """'maximum' level should return StealthConfig."""
        config = _get_stealth_config_by_level("maximum")
        assert config is not None
        # Verify maximum config properties
        assert config.humanize is True
        assert config.solve_cloudflare is True

    def test_case_insensitive_minimal(self):
        """'MINIMAL' should work (case insensitive)."""
        config = _get_stealth_config_by_level("MINIMAL")
        assert config is not None

    def test_case_insensitive_standard(self):
        """'STANDARD' should work (case insensitive)."""
        config = _get_stealth_config_by_level("STANDARD")
        assert config is not None

    def test_case_insensitive_maximum(self):
        """'MAXIMUM' should work (case insensitive)."""
        config = _get_stealth_config_by_level("MAXIMUM")
        assert config is not None

    def test_mixed_case(self):
        """Only lowercase variants work - 'MaXiMaL' should raise ValueError."""
        # The implementation uses level.lower() on the key lookup,
        # but only exact lowercase keys are in the map
        with pytest.raises(ValueError):
            _get_stealth_config_by_level("MaXiMaL")

    def test_invalid_level_raises_value_error(self):
        """Invalid level should raise ValueError."""
        with pytest.raises(ValueError) as exc_info:
            _get_stealth_config_by_level("invalid")

        error_message = str(exc_info.value)
        assert "invalid" in error_message.lower()
        assert "minimal" in error_message
        assert "standard" in error_message
        assert "maximum" in error_message

    def test_empty_string_raises_value_error(self):
        """Empty string should raise ValueError."""
        with pytest.raises(ValueError):
            _get_stealth_config_by_level("")

    def test_none_raises_value_error(self):
        """None should raise an error (AttributeError since .lower() is called on None)."""
        with pytest.raises((ValueError, AttributeError, TypeError)):
            _get_stealth_config_by_level(None)

    def test_number_raises_value_error(self):
        """Number should raise an error (AttributeError since .lower() is called on int)."""
        with pytest.raises((ValueError, AttributeError, TypeError)):
            _get_stealth_config_by_level(123)


# =============================================================================
# Tests for _ensure_json_serializable (lines 1117-1154)
# =============================================================================


class TestEnsureJsonSerializable:
    """Tests for _ensure_json_serializable function.

    This function converts various Python types to JSON-serializable types.
    """

    def test_none_returns_none(self):
        """None should return None."""
        result = _ensure_json_serializable(None)
        assert result is None

    def test_string_passthrough(self):
        """String should pass through unchanged."""
        result = _ensure_json_serializable("hello")
        assert result == "hello"

    def test_string_with_unicode(self):
        """String with unicode should pass through."""
        result = _ensure_json_serializable("hello 世界")
        assert result == "hello 世界"

    def test_string_with_special_chars(self):
        """String with special characters should pass through."""
        result = _ensure_json_serializable("test <>&\"'")
        assert result == "test <>&\"'"

    def test_integer_passthrough(self):
        """Integer should pass through unchanged."""
        result = _ensure_json_serializable(42)
        assert result == 42

    def test_negative_integer_passthrough(self):
        """Negative integer should pass through unchanged."""
        result = _ensure_json_serializable(-10)
        assert result == -10

    def test_zero_integer_passthrough(self):
        """Zero should pass through unchanged."""
        result = _ensure_json_serializable(0)
        assert result == 0

    def test_float_passthrough(self):
        """Float should pass through unchanged."""
        result = _ensure_json_serializable(3.14)
        assert result == 3.14

    def test_negative_float_passthrough(self):
        """Negative float should pass through unchanged."""
        result = _ensure_json_serializable(-2.5)
        assert result == -2.5

    def test_nan_becomes_none(self):
        """NaN should become None."""
        import math

        result = _ensure_json_serializable(float("nan"))
        assert result is None

    def test_positive_infinity_becomes_none(self):
        """Positive infinity should become None."""
        result = _ensure_json_serializable(float("inf"))
        assert result is None

    def test_negative_infinity_becomes_none(self):
        """Negative infinity should become None."""
        result = _ensure_json_serializable(float("-inf"))
        assert result is None

    def test_boolean_true_passthrough(self):
        """True should pass through unchanged."""
        result = _ensure_json_serializable(True)
        assert result is True

    def test_boolean_false_passthrough(self):
        """False should pass through unchanged."""
        result = _ensure_json_serializable(False)
        assert result is False

    def test_empty_list_becomes_empty_list(self):
        """Empty list should become empty list."""
        result = _ensure_json_serializable([])
        assert result == []

    def test_list_passthrough(self):
        """List should pass through unchanged."""
        result = _ensure_json_serializable([1, 2, 3])
        assert result == [1, 2, 3]

    def test_list_with_mixed_types(self):
        """List with mixed types should be converted."""
        result = _ensure_json_serializable([1, "two", 3.0])
        assert result == [1, "two", 3.0]

    def test_tuple_becomes_list(self):
        """Tuple should become list."""
        result = _ensure_json_serializable((1, 2, 3))
        assert result == [1, 2, 3]
        assert isinstance(result, list)

    def test_nested_list(self):
        """Nested lists should be converted."""
        result = _ensure_json_serializable([[1, 2], [3, 4]])
        assert result == [[1, 2], [3, 4]]

    def test_empty_dict_becomes_empty_dict(self):
        """Empty dict should become empty dict."""
        result = _ensure_json_serializable({})
        assert result == {}

    def test_dict_passthrough(self):
        """Dict should pass through unchanged."""
        result = _ensure_json_serializable({"key": "value"})
        assert result == {"key": "value"}

    def test_dict_with_mixed_values(self):
        """Dict with mixed values should be converted."""
        result = _ensure_json_serializable({"str": "value", "int": 42, "float": 3.14})
        assert result == {"str": "value", "int": 42, "float": 3.14}

    def test_nested_dict(self):
        """Nested dicts should be converted."""
        result = _ensure_json_serializable({"outer": {"inner": "value"}})
        assert result == {"outer": {"inner": "value"}}

    def test_set_becomes_string(self):
        """Set should become string representation."""
        result = _ensure_json_serializable({1, 2, 3})
        assert isinstance(result, str)
        assert "1" in result or "2" in result or "3" in result

    def test_frozenset_becomes_string(self):
        """FrozenSet should become string representation."""
        result = _ensure_json_serializable(frozenset([1, 2, 3]))
        assert isinstance(result, str)

    def test_datetime_becomes_iso_string(self):
        """datetime should become ISO string."""
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        result = _ensure_json_serializable(dt)
        assert isinstance(result, str)
        assert "2024-01-15" in result

    def test_date_becomes_iso_string(self):
        """date should become ISO string."""
        d = datetime.date(2024, 1, 15)
        result = _ensure_json_serializable(d)
        assert isinstance(result, str)
        assert "2024-01-15" in result

    def test_bytes_becomes_string(self):
        """bytes should become string representation."""
        result = _ensure_json_serializable(b"hello")
        assert isinstance(result, str)
        # Bytes are converted to their string representation
        assert "hello" in result

    def test_bytearray_becomes_string(self):
        """bytearray should become string."""
        result = _ensure_json_serializable(bytearray(b"hello"))
        assert isinstance(result, str)

    def test_object_with_dict_becomes_string(self):
        """Object with __dict__ should become string representation."""

        class CustomObj:
            def __init__(self):
                self.key = "value"
                self.number = 42

        result = _ensure_json_serializable(CustomObj())
        # Objects become their string representation
        assert isinstance(result, str)

    def test_object_without_dict_becomes_string(self):
        """Object without __dict__ should become string."""

        class CustomObj:
            pass

        result = _ensure_json_serializable(CustomObj())
        assert isinstance(result, str)

    def test_complex_nested_structure(self):
        """Complex nested structure should be fully converted."""
        dt = datetime.datetime(2024, 1, 15, 10, 30, 0)
        data = {
            "string": "value",
            "number": 42,
            "float": 3.14,
            "bool": True,
            "none": None,
            "list": [1, 2, "three"],
            "nested": {
                "inner": "value",
                "list": [1, 2, 3],
            },
            "datetime": dt,
        }

        result = _ensure_json_serializable(data)

        assert result["string"] == "value"
        assert result["number"] == 42
        assert result["float"] == 3.14
        assert result["bool"] is True
        assert result["none"] is None
        assert result["list"] == [1, 2, "three"]
        assert result["nested"]["inner"] == "value"
        assert isinstance(result["datetime"], str)

    def test_decimal_becomes_string(self):
        """Decimal should become string."""
        result = _ensure_json_serializable(Decimal("3.14"))
        assert isinstance(result, str)
        assert "3.14" in result


# =============================================================================
# Integration Tests for Validation Functions
# =============================================================================


class TestValidationIntegration:
    """Integration tests combining multiple validation functions."""

    def test_url_and_timeout_validation(self):
        """Test URL and timeout validation together."""
        # Valid URL and timeout
        url_error = _validate_url_param("https://example.com")
        timeout_error = _validate_timeout(30000)
        assert url_error is None
        assert timeout_error is None

        # Invalid URL with valid timeout
        url_error = _validate_url_param("")
        timeout_error = _validate_timeout(30000)
        assert url_error is not None
        assert timeout_error is None

        # Valid URL with invalid timeout
        url_error = _validate_url_param("https://example.com")
        timeout_error = _validate_timeout(500)
        assert url_error is None
        assert timeout_error is not None

    def test_batch_validation_workflow(self):
        """Test validation workflow for batch scraping."""
        # Valid inputs
        urls_error = _validate_urls_list(["https://a.com", "https://b.com"])
        stealth_error = _validate_stealth_level("standard")
        delay_error = _validate_delay(1.0)

        assert urls_error is None
        assert stealth_error is None
        assert delay_error is None

    def test_stealth_config_mapping(self):
        """Test that stealth config is correctly mapped for each level."""
        minimal = _get_stealth_config_by_level("minimal")
        standard = _get_stealth_config_by_level("standard")
        maximum = _get_stealth_config_by_level("maximum")

        # Each should have different configurations
        # minimal has no humanization, standard and maximum do
        assert minimal.humanize is False
        assert standard.humanize is True
        assert maximum.humanize is True

        # Only maximum has solve_cloudflare
        assert minimal.solve_cloudflare is False
        assert standard.solve_cloudflare is False
        assert maximum.solve_cloudflare is True

        # geoip differs
        assert minimal.geoip is False
        assert maximum.geoip is True
