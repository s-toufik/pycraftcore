import pytest

from pycraftcore.web.schema.web_application import WebApplication
from tests.web.support import nothing


@pytest.mark.parametrize("base_path", ["", "/shop", "/shop/v1"])
def test_a_base_path_is_empty_or_a_slash_separated_prefix(base_path) -> None:
    application = WebApplication(
        title="orders-api", lifespan=nothing, routes=list, base_path=base_path
    )

    assert application.base_path == base_path


@pytest.mark.parametrize("base_path", ["shop", "/shop/", "/"])
def test_a_base_path_starts_with_a_slash_and_does_not_end_with_one(base_path) -> None:
    with pytest.raises(ValueError, match="base_path"):
        WebApplication(title="orders-api", lifespan=nothing, routes=list, base_path=base_path)
