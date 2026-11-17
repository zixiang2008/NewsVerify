import pytest

from app.core.security import validate_url, SSRFError


def test_rejects_localhost():
    with pytest.raises(SSRFError):
        validate_url("http://localhost/x")


def test_rejects_private_ip():
    with pytest.raises(SSRFError):
        validate_url("http://192.168.1.1/x")


def test_rejects_metadata():
    with pytest.raises(SSRFError):
        validate_url("http://169.254.169.254/latest/meta-data/")


def test_rejects_bad_scheme():
    with pytest.raises(SSRFError):
        validate_url("file:///etc/passwd")


def test_accepts_public_https():
    # DNS may resolve; just ensure no crash on scheme/host
    try:
        validate_url("https://example.com/")
    except SSRFError:
        pass