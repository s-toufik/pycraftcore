import pytest

from tests.web.apps import blacksheep_orders, fastapi_orders, litestar_orders

EVERY_TOOLKIT = pytest.mark.parametrize(
    "orders_app",
    [fastapi_orders.orders_app, litestar_orders.orders_app, blacksheep_orders.orders_app],
    ids=["fastapi", "litestar", "blacksheep"],
)
