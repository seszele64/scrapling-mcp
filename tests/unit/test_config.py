"""Unit tests for the stealth module.

This module contains comprehensive unit tests for the StealthConfig dataclass
in src/mcp_scraper/stealth.py and its preset functions.

Tests cover:
- StealthConfig: default values, custom values, to_scrapling_options()
- Preset functions: get_minimal_stealth, get_standard_stealth, get_maximum_stealth
"""

import pytest

from mcp_scraper.stealth import (
    StealthConfig,
    get_minimal_stealth,
    get_standard_stealth,
    get_maximum_stealth,
)


# ============================================================================
# StealthConfig Tests
# ============================================================================


class TestStealthConfigDefaults:
    """Tests for StealthConfig default values."""

    def test_default_values_all_fields(self):
        """Test that StealthConfig has correct default values for all fields."""
        config = StealthConfig()

        # Core stealth settings (from stealth.py AGENTS.md spec)
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is True
        assert config.humanize_duration == 1.5
        assert config.geoip is False
        assert config.os_randomize is True
        assert config.block_webrtc is True
        assert config.allow_webgl is False  # stealth.py uses False, not True
        assert config.google_search is True
        assert config.block_images is False
        assert config.block_ads is True
        assert config.disable_resources is False
        assert config.network_idle is False
        assert config.load_dom is False
        assert config.wait_selector is None
        assert config.wait_selector_state is None
        assert config.timeout == 30  # stealth.py uses seconds, not milliseconds
        assert config.proxy is None

    def test_default_optional_fields(self):
        """Test default values for optional fields."""
        config = StealthConfig()

        assert config.wait_selector is None
        assert config.wait_selector_state is None
        assert config.proxy is None


class TestStealthConfigCustomValues:
    """Tests for StealthConfig with custom value assignment."""

    def test_custom_boolean_values(self):
        """Test assigning custom boolean values to StealthConfig."""
        config = StealthConfig(
            headless=False,
            solve_cloudflare=True,
            humanize=False,
            geoip=True,
            os_randomize=False,
            block_webrtc=False,
            allow_webgl=True,
            google_search=False,
            block_images=True,
            block_ads=False,
            disable_resources=True,
            network_idle=True,
            load_dom=True,
        )

        assert config.headless is False
        assert config.solve_cloudflare is True
        assert config.humanize is False
        assert config.geoip is True
        assert config.os_randomize is False
        assert config.block_webrtc is False
        assert config.allow_webgl is True
        assert config.google_search is False
        assert config.block_images is True
        assert config.block_ads is False
        assert config.disable_resources is True
        assert config.network_idle is True
        assert config.load_dom is True

    def test_custom_numeric_values(self):
        """Test assigning custom numeric values to StealthConfig."""
        config = StealthConfig(
            humanize_duration=2.5,
            timeout=60,  # seconds
        )

        assert config.humanize_duration == 2.5
        assert config.timeout == 60

    def test_custom_string_values(self):
        """Test assigning custom string values to StealthConfig."""
        config = StealthConfig(
            wait_selector="div.content",
            wait_selector_state="attached",
            proxy="http://my-proxy:8080",
        )

        assert config.wait_selector == "div.content"
        assert config.wait_selector_state == "attached"
        assert config.proxy == "http://my-proxy:8080"


class TestStealthConfigToScraplingOptions:
    """Tests for StealthConfig.to_scrapling_options() method."""

    def test_to_scrapling_options_default_config(self):
        """Test to_scrapling_options() returns correct dictionary for default config."""
        config = StealthConfig()
        result = config.to_scrapling_options()

        assert isinstance(result, dict)
        assert result["headless"] is True
        assert result["humanize"] is True
        # Converted to milliseconds
        assert result["timeout"] == 30000

    def test_to_scrapling_options_custom_config(self):
        """Test to_scrapling_options() returns correct dictionary for custom config."""
        config = StealthConfig(
            headless=False,
            solve_cloudflare=True,
            timeout=60,
            proxy="http://proxy:8080",
            wait_selector="body",
            wait_selector_state="visible",
        )
        result = config.to_scrapling_options()

        assert result["headless"] is False
        assert "stealth" in result
        assert result["stealth"] is True  # solve_cloudflare=True -> stealth=True
        # Converted to milliseconds
        assert result["timeout"] == 60000
        assert result["proxy"] == "http://proxy:8080"
        assert result["wait_selector"] == "body"
        assert result["wait_selector_state"] == "visible"

    def test_to_scrapling_options_block_webrtc(self):
        """Test that block_webrtc is included in options."""
        config = StealthConfig(block_webrtc=True)
        result = config.to_scrapling_options()

        assert "block_webrtc" in result
        assert result["block_webrtc"] is True

    def test_to_scrapling_options_allow_webgl(self):
        """Test that allow_webgl=False results in webgl=False in options."""
        config = StealthConfig(allow_webgl=False)
        result = config.to_scrapling_options()

        assert "webgl" in result
        assert result["webgl"] is False

    def test_to_scrapling_options_google_search(self):
        """Test that google_search=True results in browser=chrome."""
        config = StealthConfig(google_search=True)
        result = config.to_scrapling_options()

        assert "browser" in result
        assert result["browser"] == "chrome"

    def test_to_scrapling_options_block_images(self):
        """Test that block_images is included in options."""
        config = StealthConfig(block_images=True)
        result = config.to_scrapling_options()

        assert "block_images" in result
        assert result["block_images"] is True

    def test_to_scrapling_options_disable_resources(self):
        """Test that disable_resources is included in options."""
        config = StealthConfig(disable_resources=True)
        result = config.to_scrapling_options()

        assert "disable_resources" in result
        assert result["disable_resources"] is True

    def test_to_scrapling_options_network_idle(self):
        """Test that network_idle is included in options."""
        config = StealthConfig(network_idle=True)
        result = config.to_scrapling_options()

        assert "network_idle" in result
        assert result["network_idle"] is True

    def test_to_scrapling_options_load_dom(self):
        """Test that load_dom is included in options."""
        config = StealthConfig(load_dom=True)
        result = config.to_scrapling_options()

        assert "load_dom" in result
        assert result["load_dom"] is True

    def test_to_scrapling_options_humanize_duration(self):
        """Test that humanize_duration is included in options."""
        config = StealthConfig(humanize_duration=2.0)
        result = config.to_scrapling_options()

        assert "humanize_duration" in result
        assert result["humanize_duration"] == 2.0

    def test_to_scrapling_options_geoip(self):
        """Test that geoip is included in options when True."""
        config = StealthConfig(geoip=True)
        result = config.to_scrapling_options()

        assert "geoip" in result
        assert result["geoip"] is True

    def test_to_scrapling_options_os_randomize(self):
        """Test that os_randomize is included in options when True."""
        config = StealthConfig(os_randomize=True)
        result = config.to_scrapling_options()

        assert "os_randomize" in result
        assert result["os_randomize"] is True

    def test_to_scrapling_options_preserves_all_fields(self):
        """Test that to_scrapling_options() includes all relevant config fields when True."""
        config = StealthConfig(
            headless=False,
            solve_cloudflare=True,
            humanize=False,
            humanize_duration=2.0,
            geoip=True,
            os_randomize=True,  # Must be True to be included
            block_webrtc=True,  # Must be True to be included
            allow_webgl=False,  # False results in webgl=False
            google_search=False,  # False won't add browser=chrome
            block_images=True,
            block_ads=False,
            disable_resources=True,
            network_idle=True,
            load_dom=True,
            wait_selector="div.content",
            wait_selector_state="attached",
            timeout=45,
            proxy="http://test:8080",
        )
        result = config.to_scrapling_options()

        # Core fields that should be present (set to non-default values)
        assert "headless" in result
        assert "humanize" in result
        assert "timeout" in result
        assert "stealth" in result  # solve_cloudflare=True
        assert "proxy" in result
        assert "block_webrtc" in result
        assert "webgl" in result  # allow_webfl=False
        assert "block_images" in result
        assert "disable_resources" in result
        assert "network_idle" in result
        assert "load_dom" in result
        assert "wait_selector" in result
        assert "wait_selector_state" in result
        assert "humanize_duration" in result
        assert "geoip" in result
        assert "os_randomize" in result
        # google_search=False means browser=chrome won't be added
        assert "browser" not in result


class TestStealthConfigEdgeCases:
    """Tests for edge cases in StealthConfig."""

    def test_none_string_values(self):
        """Test that None values are handled correctly for string fields."""
        config = StealthConfig(
            wait_selector=None,
            wait_selector_state=None,
            proxy=None,
        )

        result = config.to_scrapling_options()
        # None values should not be included in options
        assert "wait_selector" not in result
        assert "wait_selector_state" not in result
        assert "proxy" not in result

    def test_zero_timeout(self):
        """Test that timeout can be set to 0."""
        config = StealthConfig(timeout=0)
        assert config.timeout == 0

    def test_negative_timeout(self):
        """Test that negative timeout is accepted (no validation at dataclass level)."""
        config = StealthConfig(timeout=-100)
        assert config.timeout == -100

    def test_fractional_humanize_duration(self):
        """Test fractional values for humanize_duration."""
        config = StealthConfig(humanize_duration=0.5)
        assert config.humanize_duration == 0.5

    def test_large_timeout_value(self):
        """Test large timeout value."""
        config = StealthConfig(timeout=300)
        assert config.timeout == 300


# ============================================================================
# Preset Function Tests
# ============================================================================


class TestGetMinimalStealth:
    """Tests for get_minimal_stealth() function."""

    def test_minimal_returns_stealth_config(self):
        """Test that get_minimal_stealth() returns a StealthConfig instance."""
        config = get_minimal_stealth()
        assert isinstance(config, StealthConfig)

    def test_minimal_headless(self):
        """Test minimal profile headless setting."""
        config = get_minimal_stealth()
        assert config.headless is True

    def test_minimal_solve_cloudflare(self):
        """Test minimal profile solve_cloudflare setting."""
        config = get_minimal_stealth()
        assert config.solve_cloudflare is False

    def test_minimal_humanize(self):
        """Test minimal profile humanize setting."""
        config = get_minimal_stealth()
        assert config.humanize is False

    def test_minimal_geoip(self):
        """Test minimal profile geoip setting."""
        config = get_minimal_stealth()
        assert config.geoip is False

    def test_minimal_os_randomize(self):
        """Test minimal profile os_randomize setting."""
        config = get_minimal_stealth()
        assert config.os_randomize is False

    def test_minimal_block_webrtc(self):
        """Test minimal profile block_webrtc setting."""
        config = get_minimal_stealth()
        assert config.block_webrtc is False

    def test_minimal_allow_webgl(self):
        """Test minimal profile allow_webgl setting."""
        config = get_minimal_stealth()
        assert config.allow_webgl is False

    def test_minimal_google_search(self):
        """Test minimal profile google_search setting."""
        config = get_minimal_stealth()
        assert config.google_search is False

    def test_minimal_block_images(self):
        """Test minimal profile block_images setting."""
        config = get_minimal_stealth()
        assert config.block_images is True

    def test_minimal_disable_resources(self):
        """Test minimal profile disable_resources setting."""
        config = get_minimal_stealth()
        assert config.disable_resources is True

    def test_minimal_timeout(self):
        """Test minimal profile timeout setting (in seconds)."""
        config = get_minimal_stealth()
        assert config.timeout == 15

    def test_minimal_proxy(self):
        """Test minimal profile proxy setting."""
        config = get_minimal_stealth()
        assert config.proxy is None


class TestGetStandardStealth:
    """Tests for get_standard_stealth() function."""

    def test_standard_returns_stealth_config(self):
        """Test that get_standard_stealth() returns a StealthConfig instance."""
        config = get_standard_stealth()
        assert isinstance(config, StealthConfig)

    def test_standard_headless(self):
        """Test standard profile headless setting."""
        config = get_standard_stealth()
        assert config.headless is True

    def test_standard_solve_cloudflare(self):
        """Test standard profile solve_cloudflare setting."""
        config = get_standard_stealth()
        assert config.solve_cloudflare is False

    def test_standard_humanize(self):
        """Test standard profile humanize setting."""
        config = get_standard_stealth()
        assert config.humanize is True

    def test_standard_humanize_duration(self):
        """Test standard profile humanize_duration setting."""
        config = get_standard_stealth()
        assert config.humanize_duration == 1.5

    def test_standard_geoip(self):
        """Test standard profile geoip setting."""
        config = get_standard_stealth()
        assert config.geoip is False

    def test_standard_os_randomize(self):
        """Test standard profile os_randomize setting."""
        config = get_standard_stealth()
        assert config.os_randomize is True

    def test_standard_block_webrtc(self):
        """Test standard profile block_webrtc setting."""
        config = get_standard_stealth()
        assert config.block_webrtc is True

    def test_standard_allow_webgl(self):
        """Test standard profile allow_webgl setting."""
        config = get_standard_stealth()
        assert config.allow_webgl is False

    def test_standard_google_search(self):
        """Test standard profile google_search setting."""
        config = get_standard_stealth()
        assert config.google_search is True

    def test_standard_block_images(self):
        """Test standard profile block_images setting."""
        config = get_standard_stealth()
        assert config.block_images is False

    def test_standard_block_ads(self):
        """Test standard profile block_ads setting."""
        config = get_standard_stealth()
        assert config.block_ads is True

    def test_standard_disable_resources(self):
        """Test standard profile disable_resources setting."""
        config = get_standard_stealth()
        assert config.disable_resources is False

    def test_standard_timeout(self):
        """Test standard profile timeout setting (in seconds)."""
        config = get_standard_stealth()
        assert config.timeout == 30

    def test_standard_proxy(self):
        """Test standard profile proxy setting."""
        config = get_standard_stealth()
        assert config.proxy is None


class TestGetMaximumStealth:
    """Tests for get_maximum_stealth() function."""

    def test_maximum_returns_stealth_config(self):
        """Test that get_maximum_stealth() returns a StealthConfig instance."""
        config = get_maximum_stealth()
        assert isinstance(config, StealthConfig)

    def test_maximum_headless(self):
        """Test maximum profile headless setting."""
        config = get_maximum_stealth()
        assert config.headless is True

    def test_maximum_solve_cloudflare(self):
        """Test maximum profile solve_cloudflare setting."""
        config = get_maximum_stealth()
        assert config.solve_cloudflare is True

    def test_maximum_humanize(self):
        """Test maximum profile humanize setting."""
        config = get_maximum_stealth()
        assert config.humanize is True

    def test_maximum_humanize_duration(self):
        """Test maximum profile humanize_duration setting."""
        config = get_maximum_stealth()
        assert config.humanize_duration == 1.5

    def test_maximum_geoip(self):
        """Test maximum profile geoip setting."""
        config = get_maximum_stealth()
        assert config.geoip is True

    def test_maximum_os_randomize(self):
        """Test maximum profile os_randomize setting."""
        config = get_maximum_stealth()
        assert config.os_randomize is True

    def test_maximum_block_webrtc(self):
        """Test maximum profile block_webrtc setting."""
        config = get_maximum_stealth()
        assert config.block_webrtc is True

    def test_maximum_allow_webgl(self):
        """Test maximum profile allow_webgl setting."""
        config = get_maximum_stealth()
        assert config.allow_webgl is False

    def test_maximum_google_search(self):
        """Test maximum profile google_search setting."""
        config = get_maximum_stealth()
        assert config.google_search is True

    def test_maximum_block_images(self):
        """Test maximum profile block_images setting."""
        config = get_maximum_stealth()
        assert config.block_images is False

    def test_maximum_block_ads(self):
        """Test maximum profile block_ads setting."""
        config = get_maximum_stealth()
        assert config.block_ads is True

    def test_maximum_disable_resources(self):
        """Test maximum profile disable_resources setting."""
        config = get_maximum_stealth()
        assert config.disable_resources is False

    def test_maximum_timeout(self):
        """Test maximum profile timeout setting (in seconds)."""
        config = get_maximum_stealth()
        assert config.timeout == 60

    def test_maximum_proxy(self):
        """Test maximum profile proxy setting."""
        config = get_maximum_stealth()
        assert config.proxy is None


class TestStealthProfilesComparison:
    """Tests comparing different stealth profiles."""

    def test_minimal_vs_standard_timeout_difference(self):
        """Test that minimal has shorter timeout than standard."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()
        assert minimal.timeout < standard.timeout

    def test_standard_vs_maximum_timeout_difference(self):
        """Test that standard has shorter timeout than maximum."""
        standard = get_standard_stealth()
        maximum = get_maximum_stealth()
        assert standard.timeout < maximum.timeout

    def test_minimal_no_humanize(self):
        """Test that minimal profile disables humanization."""
        minimal = get_minimal_stealth()
        assert minimal.humanize is False

    def test_standard_has_humanize(self):
        """Test that standard profile enables humanization."""
        standard = get_standard_stealth()
        assert standard.humanize is True

    def test_maximum_has_cloudflare(self):
        """Test that only maximum profile solves Cloudflare."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()
        maximum = get_maximum_stealth()

        assert minimal.solve_cloudflare is False
        assert standard.solve_cloudflare is False
        assert maximum.solve_cloudflare is True

    def test_profiles_are_independent(self):
        """Test that each preset function returns independent config objects."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()
        maximum = get_maximum_stealth()

        # Modify minimal
        minimal.timeout = 999

        # Others should be unchanged
        assert standard.timeout == 30
        assert maximum.timeout == 60

    def test_minimal_vs_standard_humanize_difference(self):
        """Test that minimal and standard have different humanize settings."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()

        assert minimal.humanize is False
        assert standard.humanize is True

    def test_maximum_has_geoip(self):
        """Test that only maximum profile enables geoip."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()
        maximum = get_maximum_stealth()

        assert minimal.geoip is False
        assert standard.geoip is False
        assert maximum.geoip is True

    def test_minimal_has_more_blocking(self):
        """Test that minimal profile has more resource blocking enabled."""
        minimal = get_minimal_stealth()
        standard = get_standard_stealth()

        # Minimal blocks more resources
        assert minimal.block_images is True
        assert standard.block_images is False
        assert minimal.disable_resources is True
        assert standard.disable_resources is False
