import pytest

from faststream.security import SASLPlaintext, ssl_not_set_error_msg


def test_without_ssl_warning():
    with pytest.raises(RuntimeError) as excinfo:
        SASLPlaintext(username="admin", password="password")
    assert str(excinfo.value) == ssl_not_set_error_msg, excinfo.value

    SASLPlaintext(username="admin", password="password", use_ssl=False)
