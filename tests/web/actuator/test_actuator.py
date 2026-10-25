from pycraftcore.web.actuator import Actuator, HealthSchema, HealthStatus, InfoSchema


def actuator(ready: bool) -> Actuator:
    return Actuator("orders-api", "1.2.3", "staging", "team@example.com", lambda: ready)


def test_health_is_always_up() -> None:
    assert actuator(ready=False).health() == HealthSchema(status=HealthStatus.UP)


def test_readiness_is_down_with_503_until_the_service_is_ready() -> None:
    assert actuator(ready=False).readiness().status_code == 503
    assert actuator(ready=True).readiness() == HealthSchema(status=HealthStatus.UP)
    assert actuator(ready=True).readiness().status_code == 200


def test_info_describes_the_service() -> None:
    assert actuator(ready=True).info() == InfoSchema(
        name="orders-api", version="1.2.3", environment="staging", authors="team@example.com"
    )
