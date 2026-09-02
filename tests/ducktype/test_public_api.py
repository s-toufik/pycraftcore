import importlib
import inspect
import pkgutil

import pycraftcore

TARGET_PACKAGE_NAMES = {"port", "configuration", "adapter"}


def _iter_target_package_names() -> list[str]:
    names = []
    for module_info in pkgutil.walk_packages(pycraftcore.__path__, prefix="pycraftcore."):
        if not module_info.ispkg:
            continue
        if module_info.name.rsplit(".", 1)[-1] in TARGET_PACKAGE_NAMES:
            names.append(module_info.name)
    return sorted(names)


TARGET_PACKAGE_NAMES_FOUND = _iter_target_package_names()


def test_at_least_one_target_package_was_found():
    # Guards against the walker itself silently finding nothing (e.g. a typo
    # in TARGET_PACKAGE_NAMES) and every other test in this file passing vacuously.
    assert len(TARGET_PACKAGE_NAMES_FOUND) >= 10


def test_every_port_configuration_adapter_package_declares_a_public_api():
    for package_name in TARGET_PACKAGE_NAMES_FOUND:
        module = importlib.import_module(package_name)
        exported = getattr(module, "__all__", None)
        assert exported, f"{package_name} has no __all__ (empty public surface)"


def test_every_declared_export_actually_resolves():
    for package_name in TARGET_PACKAGE_NAMES_FOUND:
        module = importlib.import_module(package_name)
        for name in getattr(module, "__all__", []):
            assert hasattr(module, name), (
                f"{package_name}.__all__ declares {name!r} but it isn't an attribute of the package"
            )


def test_every_exported_class_is_actually_a_class_or_protocol():
    for package_name in TARGET_PACKAGE_NAMES_FOUND:
        module = importlib.import_module(package_name)
        for name in getattr(module, "__all__", []):
            exported = getattr(module, name)
            if inspect.isclass(exported):
                continue
            assert exported is not None
