import pytest

from faststream.security import SASLPlaintext, ssl_not_set_error_msg
from faststream.kafka.security import parse_security


def test_without_ssl_warning():
    security = SASLPlaintext(username="admin", password="password")
    with pytest.warns(RuntimeWarning, match=ssl_not_set_error_msg):
        parse_security(security)

    SASLPlaintext(username="admin", password="password", use_ssl=False)
