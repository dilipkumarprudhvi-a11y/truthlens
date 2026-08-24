"""
Security tests for SSRF protection, URL validation, and input boundary constraints.
"""

import pytest
from backend.services.url_extractor import is_safe_url


def test_ssrf_blocks_localhost():
    assert is_safe_url("http://localhost:8000/admin") is False
    assert is_safe_url("http://127.0.0.1:5000") is False
    assert is_safe_url("http://127.0.0.2") is False


def test_ssrf_blocks_private_subnets():
    assert is_safe_url("http://192.168.1.1/router") is False
    assert is_safe_url("http://10.0.0.1/internal") is False
    assert is_safe_url("http://172.16.0.5/api") is False


def test_ssrf_blocks_cloud_metadata():
    assert is_safe_url("http://169.254.169.254/latest/meta-data") is False


def test_ssrf_blocks_non_http_schemes():
    assert is_safe_url("file:///etc/passwd") is False
    assert is_safe_url("ftp://server/data") is False
    assert is_safe_url("javascript:alert(1)") is False


def test_ssrf_allows_public_web_urls():
    assert is_safe_url("https://www.reuters.com/world") is True
    assert is_safe_url("https://en.wikipedia.org/wiki/Main_Page") is True
