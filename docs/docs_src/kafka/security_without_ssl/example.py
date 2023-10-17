import pytest

from faststream.broker.security import SASLPlaintext, ssl_not_set_error_msg


def test_without_ssl_warning():
    with pytest.raises(RuntimeError) as excinfo:
        security = SASLPlaintext(username="admin", password="password")
    assert str(excinfo) == ssl_not_set_error_msg

    security = SASLPlaintext(username="admin", password="password", use_ssl=False)
