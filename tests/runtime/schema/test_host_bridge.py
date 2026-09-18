from pycraftcore.runtime.schema.host_bridge import HostBridgeConfig


def test_host_bridge_config_defaults_to_no_functions():
    config = HostBridgeConfig(host="127.0.0.1", port=5000, token="secret")

    assert config.host == "127.0.0.1"
    assert config.port == 5000
    assert config.token == "secret"
    assert config.function_names == ()


def test_host_bridge_config_accepts_function_names():
    config = HostBridgeConfig(
        host="127.0.0.1", port=5000, token="secret", function_names=("file_reader", "sql_query")
    )

    assert config.function_names == ("file_reader", "sql_query")
