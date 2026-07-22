"""Tests for configuration loading and validation."""

import os

import pytest

from redmine_mcp_server.config import ConfigurationError, load_config, validate_url


class TestValidateUrl:
    """Tests for URL validation logic."""

    def test_accepts_http_url(self):
        assert validate_url("http://redmine.example.com") == "http://redmine.example.com"

    def test_accepts_https_url(self):
        assert validate_url("https://redmine.example.com") == "https://redmine.example.com"

    def test_strips_trailing_slash(self):
        assert validate_url("https://redmine.example.com/") == "https://redmine.example.com"

    def test_rejects_ftp_url(self):
        with pytest.raises(ConfigurationError, match="must start with"):
            validate_url("ftp://redmine.example.com")

    def test_rejects_no_scheme(self):
        with pytest.raises(ConfigurationError, match="must start with"):
            validate_url("redmine.example.com")

    def test_rejects_empty_string(self):
        with pytest.raises(ConfigurationError, match="must start with"):
            validate_url("")

    def test_rejects_random_string(self):
        with pytest.raises(ConfigurationError, match="must start with"):
            validate_url("not-a-url")


class TestLoadConfig:
    """Tests for environment variable loading and validation."""

    def test_loads_valid_config(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        config = load_config()
        assert config["redmine_url"] == "https://redmine.example.com"
        assert config["redmine_api_key"] == "abc123"

    def test_missing_redmine_url(self, monkeypatch):
        monkeypatch.delenv("REDMINE_URL", raising=False)
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        with pytest.raises(ConfigurationError, match="REDMINE_URL"):
            load_config()

    def test_empty_redmine_url(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        with pytest.raises(ConfigurationError, match="REDMINE_URL"):
            load_config()

    def test_whitespace_only_redmine_url(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "   ")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        with pytest.raises(ConfigurationError, match="REDMINE_URL"):
            load_config()

    def test_missing_redmine_api_key(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
        monkeypatch.delenv("REDMINE_API_KEY", raising=False)
        with pytest.raises(ConfigurationError, match="REDMINE_API_KEY"):
            load_config()

    def test_empty_redmine_api_key(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
        monkeypatch.setenv("REDMINE_API_KEY", "")
        with pytest.raises(ConfigurationError, match="REDMINE_API_KEY"):
            load_config()

    def test_whitespace_only_redmine_api_key(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com")
        monkeypatch.setenv("REDMINE_API_KEY", "   ")
        with pytest.raises(ConfigurationError, match="REDMINE_API_KEY"):
            load_config()

    def test_invalid_url_scheme(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "ftp://redmine.example.com")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        with pytest.raises(ConfigurationError, match="must start with"):
            load_config()

    def test_url_trailing_slash_stripped(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://redmine.example.com/")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        config = load_config()
        assert config["redmine_url"] == "https://redmine.example.com"

    def test_url_with_path(self, monkeypatch):
        monkeypatch.setenv("REDMINE_URL", "https://example.com/redmine")
        monkeypatch.setenv("REDMINE_API_KEY", "abc123")
        config = load_config()
        assert config["redmine_url"] == "https://example.com/redmine"
