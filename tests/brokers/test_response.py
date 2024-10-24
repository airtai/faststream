from faststream.response import Response, ensure_response


def test_raw_data() -> None:
    resp = ensure_response(1)
    assert resp.body == 1
    assert resp.headers == {}


def test_response_with_response_instance() -> None:
    resp = ensure_response(Response(1, headers={"some": 1}))
    assert resp.body == 1
    assert resp.headers == {"some": 1}
