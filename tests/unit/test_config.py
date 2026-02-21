"""Unit tests for the config module.

This module contains comprehensive unit tests for the StealthConfig dataclass,
Settings class, and StealthProfiles class in src/mcp_scraper/config.py.

Tests cover:
- StealthConfig: default values, custom values, to_dict(), to_scrapling_options()
- Settings: default values, env var loading, validation
- StealthProfiles: minimal, standard, maximum, no_js methods
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from mcp_scraper.config import Settings, StealthConfig, StealthProfiles


# ============================================================================
# StealthConfig Tests
# ============================================================================


class TestStealthConfigDefaults:
    """Tests for StealthConfig default values."""

    def test_default_values_all_fields(self):
        """Test that StealthConfig has correct default values for all fields."""
        config = StealthConfig()

        # Core stealth settings (AGENTS.md spec)
        assert config.headless is True
        assert config.solve_cloudflare is False
        assert config.humanize is True
        assert config.humanize_duration == 1.5
        assert config.geoip is False
        assert config.os_randomize is True
        assert config.block_webrtc is True
        assert config.allow_webgl is True
        assert config.google_search is True
        assert config.block_images is False
        assert config.block_ads is True
        assert config.disable_resources is False
        assert config.network_idle is False
        assert config.load_dom is False
        assert config.wait_selector is None
        assert config.wait_selector_state is None
        assert config.timeout == 30000
        assert config.proxy is None

        # Legacy/additional settings
        assert config.enable_js is True
        assert config.randomize_user_agent is True
        assert config.use_browser_pool is False
        assert config.disable_images is False
        assert config.disable_css is False
        assert config.block_trackers is True
        assert config.simulate_human_behavior is False
        assert config.random_delay == (0.5, 2.0)
        assert config.viewport_size == (1920, 1080)
        assert config.timezone == "UTC"
        assert config.language == "en-US"
        assert config.accept_language == "en-US,en;q=0.9"

    def test_default_cookies_and_headers(self):
        """Test default values for cookies and extra_headers."""
        config = StealthConfig()

        assert config.cookies == []
        assert config.extra_headers == {}


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
            allow_webgl=False,
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
        assert config.allow_webgl is False
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
            timeout=60000,
        )

        assert config.humanize_duration == 2.5
        assert config.timeout == 60000

    def test_custom_string_values(self):
        """Test assigning custom string values to StealthConfig."""
        config = StealthConfig(
            wait_selector="div.content",
            wait_selector_state="attached",
            proxy="http://my-proxy:8080",
            timezone="America/Los_Angeles",
            language="de-DE",
            accept_language="de-DE,en;q=0.9",
        )

        assert config.wait_selector == "div.content"
        assert config.wait_selector_state == "attached"
        assert config.proxy == "http://my-proxy:8080"
        assert config.timezone == "America/Los_Angeles"
        assert config.language == "de-DE"
        assert config.accept_language == "de-DE,en;q=0.9"

    def test_custom_tuple_values(self):
        """Test assigning custom tuple values to StealthConfig."""
        config = StealthConfig(
            random_delay=(1.0, 3.0),
            viewport_size=(1366, 768),
        )

        assert config.random_delay == (1.0, 3.0)
        assert config.viewport_size == (1366, 768)

    def test_custom_list_and_dict_values(self):
        """Test assigning custom list and dict values to StealthConfig."""
        config = StealthConfig(
            cookies=[{"name": "session", "value": "abc123"}],
            extra_headers={"X-Custom-Header": "custom-value"},
        )

        assert config.cookies == [{"name": "session", "value": "abc123"}]
        assert config.extra_headers == {"X-Custom-Header": "custom-value"}


class TestStealthConfigToDict:
    """Tests for StealthConfig.to_dict() method."""

    def test_to_dict_default_config(self):
        """Test to_dict() returns correct dictionary for default config."""
        config = StealthConfig()
        result = config.to_dict()

        assert isinstance(result, dict)
        assert result["headless"] is True
        assert result["solve_cloudflare"] is False
        assert result["humanize"] is True
        assert result["humanize_duration"] == 1.5
        assert result["timeout"] == 30000

    def test_to_dict_custom_config(self):
        """Test to_dict() returns correct dictionary for custom config."""
        config = StealthConfig(
            headless=False,
            solve_cloudflare=True,
            timeout=60000,
            proxy="http://proxy:8080",
            wait_selector="body",
            wait_selector_state="visible",
        )
        result = config.to_dict()

        assert result["headless"] is False
        assert result["solve_cloudflare"] is True
        assert result["timeout"] == 60000
        assert result["proxy"] == "http://proxy:8080"
        assert result["wait_selector"] == "body"
        assert result["wait_selector_state"] == "visible"

    def test_to_dict_legacy_mappings(self):
        """Test that to_dict() includes legacy field mappings."""
        config = StealthConfig(
            enable_js=False,
            randomize_user_agent=False,
            use_browser_pool=True,
            disable_images=True,
            disable_css=True,
            block_trackers=False,
            simulate_human_behavior=True,
        )
        result = config.to_dict()

        # Legacy mappings should be included
        assert "javascript" in result
        assert result["javascript"] is False  # enable_js=False -> javascript=False
        assert "random_user_agent" in result
        assert result["random_user_agent"] is False
        assert "browser_pool" in result
        assert result["browser_pool"] is True
        assert "images" in result
        assert result["images"] is False  # disable_images=True -> images=False
        assert "css" in result
        assert result["css"] is False  # disable_css=True -> css=False
        assert "block_trackers" in result
        assert "human_behavior" in result

    def test_to_dict_tuple_values(self):
        """Test that to_dict() correctly handles tuple values."""
        config = StealthConfig(
            random_delay=(1.5, 4.0),
            viewport_size=(1024, 768),
        )
        result = config.to_dict()

        assert result["delay"] == (1.5, 4.0)
        assert result["viewport"] == (1024, 768)

    def test_to_dict_preserves_all_fields(self):
        """Test that to_dict() includes all config fields."""
        config = StealthConfig()
        result = config.to_dict()

        # Core fields
        expected_fields = [
            "headless",
            "solve_cloudflare",
            "humanize",
            "humanize_duration",
            "geoip",
            "os_randomize",
            "block_webrtc",
            "allow_webgl",
            "google_search",
            "block_images",
            "block_ads",
            "disable_resources",
            "network_idle",
            "load_dom",
            "wait_selector",
            "wait_selector_state",
            "timeout",
            "proxy",
            # Legacy mappings
            "javascript",
            "random_user_agent",
            "browser_pool",
            "images",
            "css",
            "block_trackers",
            "human_behavior",
            "delay",
            "viewport",
            "timezone",
            "locale",
            "accept_language",
            "cookies",
            "extra_headers",
        ]

        for field in expected_fields:
            assert field in result, f"Missing field: {field}"


class TestStealthConfigEdgeCases:
    """Tests for edge cases in StealthConfig."""

    def test_none_string_values(self):
        """Test that None values are handled correctly for string fields."""
        config = StealthConfig(
            wait_selector=None,
            wait_selector_state=None,
            proxy=None,
        )

        result = config.to_dict()
        assert result["wait_selector"] is None
        assert result["wait_selector_state"] is None
        assert result["proxy"] is None

    def test_empty_string_values(self):
        """Test that empty string values are handled correctly."""
        config = StealthConfig(
            timezone="",
            language="",
            accept_language="",
        )

        assert config.timezone == ""
        assert config.language == ""
        assert config.accept_language == ""

    def test_zero_timeout(self):
        """Test that timeout can be set to 0."""
        config = StealthConfig(timeout=0)
        assert config.timeout == 0

    def test_negative_timeout(self):
        """Test that negative timeout is accepted (no validation at dataclass level)."""
        # StealthConfig is a plain dataclass - it doesn't validate values at construction
        config = StealthConfig(timeout=-1000)
        assert config.timeout == -1000

    def test_fractional_humanize_duration(self):
        """Test fractional values for humanize_duration."""
        config = StealthConfig(humanize_duration=0.5)
        assert config.humanize_duration == 0.5

    def test_large_timeout_value(self):
        """Test large timeout value."""
        config = StealthConfig(timeout=300000)
        assert config.timeout == 300000


# ============================================================================
# Settings Tests
# ============================================================================


class TestSettingsDefaults:
    """Tests for Settings default values."""

    def test_default_values(self):
        """Test that Settings has correct default values."""
        settings = Settings()

        assert settings.proxy_url is None
        assert settings.default_timeout == 30
        assert settings.log_level == "INFO"
        assert settings.max_retries == 3


class TestSettingsEnvVarLoading:
    """Tests for Settings environment variable loading."""

    def test_load_proxy_url_from_env(self):
        """Test loading proxy_url from environment variable."""
        with patch.dict(os.environ, {"PROXY_URL": "http://test-proxy:8080"}):
            settings = Settings()
            assert settings.proxy_url == "http://test-proxy:8080"

    def test_load_timeout_from_env(self):
        """Test loading default_timeout from environment variable."""
        with patch.dict(os.environ, {"DEFAULT_TIMEOUT": "60"}):
            settings = Settings()
            assert settings.default_timeout == 60

    def test_load_log_level_from_env(self):
        """Test loading log_level from environment variable."""
        with patch.dict(os.environ, {"LOG_LEVEL": "DEBUG"}):
            settings = Settings()
            assert settings.log_level == "DEBUG"

    def test_load_max_retries_from_env(self):
        """Test loading max_retries from environment variable."""
        with patch.dict(os.environ, {"MAX_RETRIES": "5"}):
            settings = Settings()
            assert settings.max_retries == 5

    def test_case_insensitive_env_loading(self):
        """Test that environment variable loading is case insensitive."""
        with patch.dict(os.environ, {"proxy_url": "http://test:8080", "LOG_LEVEL": "warning"}):
            settings = Settings()
            assert settings.proxy_url == "http://test:8080"
            assert settings.log_level == "warning"

    def test_empty_env_values(self):
        """Test handling of empty environment variable values."""
        # When env var is empty string, pydantic tries to parse it and fails
        # This is expected behavior - empty string is not a valid integer
        with pytest.raises(ValidationError):
            with patch.dict(
                os.environ, {"PROXY_URL": "", "DEFAULT_TIMEOUT": "", "LOG_LEVEL": ""}, clear=True
            ):
                Settings()


class TestSettingsValidation:
    """Tests for Settings validation."""

    def test_proxy_url_valid_http(self):
        """Test valid HTTP proxy URL."""
        settings = Settings(proxy_url="http://proxy.example.com:8080")
        assert settings.proxy_url == "http://proxy.example.com:8080"

    def test_proxy_url_valid_socks5(self):
        """Test valid SOCKS5 proxy URL."""
        settings = Settings(proxy_url="socks5://proxy.example.com:1080")
        assert settings.proxy_url == "socks5://proxy.example.com:1080"

    def test_proxy_url_with_auth(self):
        """Test proxy URL with authentication."""
        settings = Settings(proxy_url="http://user:pass@proxy.example.com:8080")
        assert settings.proxy_url == "http://user:pass@proxy.example.com:8080"

    def test_timeout_minimum_value(self):
        """Test timeout minimum boundary (1 second)."""
        settings = Settings(default_timeout=1)
        assert settings.default_timeout == 1

    def test_timeout_maximum_value(self):
        """Test timeout maximum boundary (300 seconds)."""
        settings = Settings(default_timeout=300)
        assert settings.default_timeout == 300

    def test_timeout_below_minimum_raises_error(self):
        """Test that timeout below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(default_timeout=0)
        assert "default_timeout" in str(exc_info.value)

    def test_timeout_above_maximum_raises_error(self):
        """Test that timeout above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(default_timeout=301)
        assert "default_timeout" in str(exc_info.value)

    def test_timeout_invalid_type_raises_error(self):
        """Test that invalid timeout type raises ValidationError."""
        with pytest.raises(ValidationError):
            Settings(default_timeout="thirty")

    def test_log_level_valid_values(self):
        """Test valid log level values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = Settings(log_level=level)
            assert settings.log_level == level

    def test_log_level_lowercase(self):
        """Test that log level accepts lowercase values."""
        settings = Settings(log_level="debug")
        assert settings.log_level == "debug"

    def test_max_retries_minimum_value(self):
        """Test max_retries minimum boundary (0)."""
        settings = Settings(max_retries=0)
        assert settings.max_retries == 0

    def test_max_retries_maximum_value(self):
        """Test max_retries maximum boundary (10)."""
        settings = Settings(max_retries=10)
        assert settings.max_retries == 10

    def test_max_retries_below_minimum_raises_error(self):
        """Test that max_retries below minimum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(max_retries=-1)
        assert "max_retries" in str(exc_info.value)

    def test_max_retries_above_maximum_raises_error(self):
        """Test that max_retries above maximum raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(max_retries=11)
        assert "max_retries" in str(exc_info.value)


# ============================================================================
# StealthProfiles Tests
# ============================================================================


class TestStealthProfilesMinimal:
    """Tests for StealthProfiles.minimal() method."""

    def test_minimal_returns_stealth_config(self):
        """Test that minimal() returns a StealthConfig instance."""
        config = StealthProfiles.minimal()
        assert isinstance(config, StealthConfig)

    def test_minimal_headless(self):
        """Test minimal profile headless setting."""
        config = StealthProfiles.minimal()
        assert config.headless is True

    def test_minimal_solve_cloudflare(self):
        """Test minimal profile solve_cloudflare setting."""
        config = StealthProfiles.minimal()
        assert config.solve_cloudflare is False

    def test_minimal_humanize(self):
        """Test minimal profile humanize setting."""
        config = StealthProfiles.minimal()
        assert config.humanize is False

    def test_minimal_geoip(self):
        """Test minimal profile geoip setting."""
        config = StealthProfiles.minimal()
        assert config.geoip is False

    def test_minimal_os_randomize(self):
        """Test minimal profile os_randomize setting."""
        config = StealthProfiles.minimal()
        assert config.os_randomize is False

    def test_minimal_block_webrtc(self):
        """Test minimal profile block_webrtc setting."""
        config = StealthProfiles.minimal()
        assert config.block_webrtc is False

    def test_minimal_allow_webgl(self):
        """Test minimal profile allow_webgl setting."""
        config = StealthProfiles.minimal()
        assert config.allow_webgl is False

    def test_minimal_google_search(self):
        """Test minimal profile google_search setting."""
        config = StealthProfiles.minimal()
        assert config.google_search is False

    def test_minimal_block_images(self):
        """Test minimal profile block_images setting."""
        config = StealthProfiles.minimal()
        assert config.block_images is True

    def test_minimal_block_ads(self):
        """Test minimal profile block_ads setting."""
        config = StealthProfiles.minimal()
        assert config.block_ads is True

    def test_minimal_disable_resources(self):
        """Test minimal profile disable_resources setting."""
        config = StealthProfiles.minimal()
        assert config.disable_resources is True

    def test_minimal_network_idle(self):
        """Test minimal profile network_idle setting."""
        config = StealthProfiles.minimal()
        assert config.network_idle is False

    def test_minimal_load_dom(self):
        """Test minimal profile load_dom setting."""
        config = StealthProfiles.minimal()
        assert config.load_dom is False

    def test_minimal_timeout(self):
        """Test minimal profile timeout setting."""
        config = StealthProfiles.minimal()
        assert config.timeout == 15000

    def test_minimal_random_delay(self):
        """Test minimal profile random_delay setting."""
        config = StealthProfiles.minimal()
        assert config.random_delay == (0.1, 0.5)


class TestStealthProfilesStandard:
    """Tests for StealthProfiles.standard() method."""

    def test_standard_returns_stealth_config(self):
        """Test that standard() returns a StealthConfig instance."""
        config = StealthProfiles.standard()
        assert isinstance(config, StealthConfig)

    def test_standard_headless(self):
        """Test standard profile headless setting."""
        config = StealthProfiles.standard()
        assert config.headless is True

    def test_standard_solve_cloudflare(self):
        """Test standard profile solve_cloudflare setting."""
        config = StealthProfiles.standard()
        assert config.solve_cloudflare is False

    def test_standard_humanize(self):
        """Test standard profile humanize setting."""
        config = StealthProfiles.standard()
        assert config.humanize is True

    def test_standard_humanize_duration(self):
        """Test standard profile humanize_duration setting."""
        config = StealthProfiles.standard()
        assert config.humanize_duration == 1.5

    def test_standard_geoip(self):
        """Test standard profile geoip setting."""
        config = StealthProfiles.standard()
        assert config.geoip is False

    def test_standard_os_randomize(self):
        """Test standard profile os_randomize setting."""
        config = StealthProfiles.standard()
        assert config.os_randomize is True

    def test_standard_block_webrtc(self):
        """Test standard profile block_webrtc setting."""
        config = StealthProfiles.standard()
        assert config.block_webrtc is True

    def test_standard_allow_webgl(self):
        """Test standard profile allow_webgl setting."""
        config = StealthProfiles.standard()
        assert config.allow_webgl is True

    def test_standard_google_search(self):
        """Test standard profile google_search setting."""
        config = StealthProfiles.standard()
        assert config.google_search is True

    def test_standard_block_images(self):
        """Test standard profile block_images setting."""
        config = StealthProfiles.standard()
        assert config.block_images is False

    def test_standard_block_ads(self):
        """Test standard profile block_ads setting."""
        config = StealthProfiles.standard()
        assert config.block_ads is True

    def test_standard_disable_resources(self):
        """Test standard profile disable_resources setting."""
        config = StealthProfiles.standard()
        assert config.disable_resources is False

    def test_standard_network_idle(self):
        """Test standard profile network_idle setting."""
        config = StealthProfiles.standard()
        assert config.network_idle is True

    def test_standard_load_dom(self):
        """Test standard profile load_dom setting."""
        config = StealthProfiles.standard()
        assert config.load_dom is True

    def test_standard_timeout(self):
        """Test standard profile timeout setting."""
        config = StealthProfiles.standard()
        assert config.timeout == 30000

    def test_standard_random_delay(self):
        """Test standard profile random_delay setting."""
        config = StealthProfiles.standard()
        assert config.random_delay == (0.5, 2.0)

    def test_standard_viewport_size(self):
        """Test standard profile viewport_size setting."""
        config = StealthProfiles.standard()
        assert config.viewport_size == (1920, 1080)


class TestStealthProfilesMaximum:
    """Tests for StealthProfiles.maximum() method."""

    def test_maximum_returns_stealth_config(self):
        """Test that maximum() returns a StealthConfig instance."""
        config = StealthProfiles.maximum()
        assert isinstance(config, StealthConfig)

    def test_maximum_headless(self):
        """Test maximum profile headless setting."""
        config = StealthProfiles.maximum()
        assert config.headless is True

    def test_maximum_solve_cloudflare(self):
        """Test maximum profile solve_cloudflare setting."""
        config = StealthProfiles.maximum()
        assert config.solve_cloudflare is True

    def test_maximum_humanize(self):
        """Test maximum profile humanize setting."""
        config = StealthProfiles.maximum()
        assert config.humanize is True

    def test_maximum_humanize_duration(self):
        """Test maximum profile humanize_duration setting."""
        config = StealthProfiles.maximum()
        assert config.humanize_duration == 1.5

    def test_maximum_geoip(self):
        """Test maximum profile geoip setting."""
        config = StealthProfiles.maximum()
        assert config.geoip is True

    def test_maximum_os_randomize(self):
        """Test maximum profile os_randomize setting."""
        config = StealthProfiles.maximum()
        assert config.os_randomize is True

    def test_maximum_block_webrtc(self):
        """Test maximum profile block_webrtc setting."""
        config = StealthProfiles.maximum()
        assert config.block_webrtc is True

    def test_maximum_allow_webgl(self):
        """Test maximum profile allow_webgl setting."""
        config = StealthProfiles.maximum()
        assert config.allow_webgl is True

    def test_maximum_google_search(self):
        """Test maximum profile google_search setting."""
        config = StealthProfiles.maximum()
        assert config.google_search is True

    def test_maximum_block_images(self):
        """Test maximum profile block_images setting."""
        config = StealthProfiles.maximum()
        assert config.block_images is False

    def test_maximum_block_ads(self):
        """Test maximum profile block_ads setting."""
        config = StealthProfiles.maximum()
        assert config.block_ads is True

    def test_maximum_disable_resources(self):
        """Test maximum profile disable_resources setting."""
        config = StealthProfiles.maximum()
        assert config.disable_resources is False

    def test_maximum_network_idle(self):
        """Test maximum profile network_idle setting."""
        config = StealthProfiles.maximum()
        assert config.network_idle is True

    def test_maximum_load_dom(self):
        """Test maximum profile load_dom setting."""
        config = StealthProfiles.maximum()
        assert config.load_dom is True

    def test_maximum_wait_selector(self):
        """Test maximum profile wait_selector setting."""
        config = StealthProfiles.maximum()
        assert config.wait_selector == "body"

    def test_maximum_wait_selector_state(self):
        """Test maximum profile wait_selector_state setting."""
        config = StealthProfiles.maximum()
        assert config.wait_selector_state == "visible"

    def test_maximum_timeout(self):
        """Test maximum profile timeout setting."""
        config = StealthProfiles.maximum()
        assert config.timeout == 60000

    def test_maximum_random_delay(self):
        """Test maximum profile random_delay setting."""
        config = StealthProfiles.maximum()
        assert config.random_delay == (2.0, 5.0)

    def test_maximum_use_browser_pool(self):
        """Test maximum profile use_browser_pool setting."""
        config = StealthProfiles.maximum()
        assert config.use_browser_pool is True

    def test_maximum_timezone(self):
        """Test maximum profile timezone setting."""
        config = StealthProfiles.maximum()
        assert config.timezone == "America/New_York"

    def test_maximum_language(self):
        """Test maximum profile language setting."""
        config = StealthProfiles.maximum()
        assert config.language == "en-US"


class TestStealthProfilesNoJs:
    """Tests for StealthProfiles.no_js() method."""

    def test_no_js_returns_stealth_config(self):
        """Test that no_js() returns a StealthConfig instance."""
        config = StealthProfiles.no_js()
        assert isinstance(config, StealthConfig)

    def test_no_js_headless(self):
        """Test no_js profile headless setting."""
        config = StealthProfiles.no_js()
        assert config.headless is True

    def test_no_js_solve_cloudflare(self):
        """Test no_js profile solve_cloudflare setting."""
        config = StealthProfiles.no_js()
        assert config.solve_cloudflare is False

    def test_no_js_humanize(self):
        """Test no_js profile humanize setting."""
        config = StealthProfiles.no_js()
        assert config.humanize is False

    def test_no_js_geoip(self):
        """Test no_js profile geoip setting."""
        config = StealthProfiles.no_js()
        assert config.geoip is False

    def test_no_js_os_randomize(self):
        """Test no_js profile os_randomize setting."""
        config = StealthProfiles.no_js()
        assert config.os_randomize is False

    def test_no_js_block_webrtc(self):
        """Test no_js profile block_webrtc setting."""
        config = StealthProfiles.no_js()
        assert config.block_webrtc is False

    def test_no_js_allow_webgl(self):
        """Test no_js profile allow_webgl setting."""
        config = StealthProfiles.no_js()
        assert config.allow_webgl is False

    def test_no_js_google_search(self):
        """Test no_js profile google_search setting."""
        config = StealthProfiles.no_js()
        assert config.google_search is False

    def test_no_js_block_images(self):
        """Test no_js profile block_images setting."""
        config = StealthProfiles.no_js()
        assert config.block_images is True

    def test_no_js_block_ads(self):
        """Test no_js profile block_ads setting."""
        config = StealthProfiles.no_js()
        assert config.block_ads is False

    def test_no_js_disable_resources(self):
        """Test no_js profile disable_resources setting."""
        config = StealthProfiles.no_js()
        assert config.disable_resources is False

    def test_no_js_network_idle(self):
        """Test no_js profile network_idle setting."""
        config = StealthProfiles.no_js()
        assert config.network_idle is False

    def test_no_js_load_dom(self):
        """Test no_js profile load_dom setting."""
        config = StealthProfiles.no_js()
        assert config.load_dom is False

    def test_no_js_enable_js(self):
        """Test no_js profile enable_js setting."""
        config = StealthProfiles.no_js()
        assert config.enable_js is False

    def test_no_js_timeout(self):
        """Test no_js profile timeout setting."""
        config = StealthProfiles.no_js()
        assert config.timeout == 15000

    def test_no_js_random_delay(self):
        """Test no_js profile random_delay setting."""
        config = StealthProfiles.no_js()
        assert config.random_delay == (0.1, 0.3)


class TestStealthProfilesComparison:
    """Tests comparing different stealth profiles."""

    def test_minimal_vs_standard_timeout_difference(self):
        """Test that minimal has shorter timeout than standard."""
        minimal = StealthProfiles.minimal()
        standard = StealthProfiles.standard()
        assert minimal.timeout < standard.timeout

    def test_standard_vs_maximum_timeout_difference(self):
        """Test that standard has shorter timeout than maximum."""
        standard = StealthProfiles.standard()
        maximum = StealthProfiles.maximum()
        assert standard.timeout < maximum.timeout

    def test_minimal_no_humanize(self):
        """Test that minimal profile disables humanization."""
        minimal = StealthProfiles.minimal()
        assert minimal.humanize is False

    def test_standard_has_humanize(self):
        """Test that standard profile enables humanization."""
        standard = StealthProfiles.standard()
        assert standard.humanize is True

    def test_maximum_has_cloudflare(self):
        """Test that only maximum profile solves Cloudflare."""
        minimal = StealthProfiles.minimal()
        standard = StealthProfiles.standard()
        maximum = StealthProfiles.maximum()

        assert minimal.solve_cloudflare is False
        assert standard.solve_cloudflare is False
        assert maximum.solve_cloudflare is True

    def test_profiles_are_independent(self):
        """Test that modifying one profile doesn't affect others."""
        minimal = StealthProfiles.minimal()
        standard = StealthProfiles.standard()
        maximum = StealthProfiles.maximum()

        # Modify minimal
        minimal.timeout = 99999

        # Others should be unchanged
        assert standard.timeout == 30000
        assert maximum.timeout == 60000
