import pytest

from faststream.broker.security import SASLPlaintext, ssl_not_set_error_msg


def test_without_ssl_warning():
    with pytest.raises(RuntimeError) as excinfo:
        security = SASLPlaintext(username="admin", password="password")
    assert str(excinfo.value) == ssl_not_set_error_msg, excinfo.value

    security = SASLPlaintext(username="admin", password="password", use_ssl=False)
