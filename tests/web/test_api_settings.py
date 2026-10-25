import pytest

from pycraftcore.web.schema import ApiSettings


@pytest.mark.parametrize("base_path", ["", "/shop", "/shop/v1"])
def test_a_base_path_is_empty_or_a_slash_separated_prefix(base_path) -> None:
    assert ApiSettings(title="orders-api", base_path=base_path).base_path == base_path


@pytest.mark.parametrize("base_path", ["shop", "/shop/", "/"])
def test_a_base_path_starts_with_a_slash_and_does_not_end_with_one(base_path) -> None:
    with pytest.raises(ValueError, match="base_path"):
        ApiSettings(title="orders-api", base_path=base_path)


@pytest.mark.parametrize(
    ("base_path", "docs", "openapi"),
    [("", "/docs", "/docs/openapi.json"), ("/shop", "/shop/docs", "/shop/docs/openapi.json")],
)
def test_the_documentation_lives_under_the_base_path(base_path, docs, openapi) -> None:
    api = ApiSettings(title="orders-api", base_path=base_path)

    assert (api.docs_path, api.openapi_path) == (docs, openapi)
