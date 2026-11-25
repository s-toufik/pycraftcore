import operator
import re
from collections.abc import Iterable
from functools import reduce
from typing import Annotated, Any, Literal, NotRequired, Required, TypedDict

from pydantic import BaseModel, ConfigDict, Field, create_model

_PYTHON_TYPES: dict[str, Any] = {
    "string": str,
    "integer": int,
    "number": float,
    "boolean": bool,
    "null": type(None),
}
_REGEX_ENGINE: ConfigDict = ConfigDict(regex_engine="python-re")
_NUMBER_BOUNDS: dict[str, str] = {
    "minimum": "ge",
    "maximum": "le",
    "exclusiveMinimum": "gt",
    "exclusiveMaximum": "lt",
    "multipleOf": "multiple_of",
}
_LENGTH_BOUNDS: dict[str, dict[str, str]] = {
    "string": {"minLength": "min_length", "maxLength": "max_length"},
    "array": {"minItems": "min_length", "maxItems": "max_length"},
}
_DEFINITIONS: tuple[str, ...] = ("#/$defs/", "#/definitions/")


def model_from_schema(model_name: str, schema: dict[str, Any] | None) -> type[BaseModel]:
    if not schema or schema.get("type") != "object" or not schema.get("properties"):
        return create_model(model_name, __config__=ConfigDict(extra="allow"))

    reader = _SchemaReader(schema)
    required: set[str] = set(schema.get("required", ()))
    fields: dict[str, Any] = {}
    for name, spec in schema["properties"].items():
        annotation: Any = reader.annotation(spec, f"{model_name}_{name}")
        description: str | None = spec.get("description") if isinstance(spec, dict) else None
        if name in required:
            fields[name] = (annotation, Field(description=description))
        else:
            default: Any = spec.get("default") if isinstance(spec, dict) else None
            fields[name] = (annotation | None, Field(default=default, description=description))
    return create_model(model_name, __config__=_REGEX_ENGINE, **fields)


class _SchemaReader:
    def __init__(self, schema: dict[str, Any]) -> None:
        self._definitions: dict[str, Any] = {
            **schema.get("definitions", {}),
            **schema.get("$defs", {}),
        }

    def annotation(self, spec: Any, name: str, resolving: frozenset[str] = frozenset()) -> Any:
        if not isinstance(spec, dict):
            return Any
        if "$ref" in spec:
            return self._reference(spec["$ref"], name, resolving)
        if "const" in spec:
            return _literal([spec["const"]])
        if "enum" in spec:
            return _literal(spec["enum"])
        for key in ("anyOf", "oneOf"):
            if isinstance(spec.get(key), list):
                return _union(self.annotation(option, name, resolving) for option in spec[key])
        if isinstance(spec.get("allOf"), list):
            parts: list[Any] = spec["allOf"]
            return self.annotation(parts[0], name, resolving) if len(parts) == 1 else Any

        kind: Any = spec.get("type", "object" if "properties" in spec else None)
        if isinstance(kind, list):
            return _union(
                self.annotation(spec | {"type": entry}, name, resolving) for entry in kind
            )
        if kind == "array":
            return _constrained(self._array(spec, name, resolving), kind, spec)
        if kind == "object":
            return self._object(spec, name, resolving)
        return _constrained(_PYTHON_TYPES.get(kind, Any), kind, spec)

    def _reference(self, reference: Any, name: str, resolving: frozenset[str]) -> Any:
        key: str | None = next(
            (
                reference.removeprefix(prefix)
                for prefix in _DEFINITIONS
                if isinstance(reference, str) and reference.startswith(prefix)
            ),
            None,
        )
        if key is None or key in resolving or key not in self._definitions:
            return Any
        return self.annotation(self._definitions[key], name, resolving | {key})

    def _array(self, spec: dict[str, Any], name: str, resolving: frozenset[str]) -> Any:
        items: Any = spec.get("items")
        element: Any = self.annotation(items, f"{name}_item", resolving) if items else Any
        return list[element]

    def _object(self, spec: dict[str, Any], name: str, resolving: frozenset[str]) -> Any:
        properties: Any = spec.get("properties")
        extra: Any = spec.get("additionalProperties", True)
        if not isinstance(properties, dict) or not properties:
            values: Any = self.annotation(extra, f"{name}_value", resolving)
            return dict[str, values]

        required: set[str] = set(spec.get("required", ()))
        keys: dict[str, Any] = {}
        for key, sub in properties.items():
            annotation: Any = self.annotation(sub, f"{name}_{key}", resolving)
            if isinstance(sub, dict) and isinstance(sub.get("description"), str):
                annotation = Annotated[annotation, Field(description=sub["description"])]
            keys[key] = Required[annotation] if key in required else NotRequired[annotation]
        typed: Any = TypedDict(name, keys)  # ty: ignore[invalid-argument-type]
        typed.__pydantic_config__ = _REGEX_ENGINE | ConfigDict(
            extra="forbid" if extra is False else "allow"
        )
        return typed


def _literal(values: list[Any]) -> Any:
    if not values or not all(
        isinstance(value, str | int | float | bool | None) for value in values
    ):
        return Any
    return Literal.__getitem__(tuple(values))


def _union(annotations: Iterable[Any]) -> Any:
    options: list[Any] = list(annotations)
    if not options or any(option is Any for option in options):
        return Any
    return reduce(operator.or_, options)


def _constrained(base: Any, kind: Any, spec: dict[str, Any]) -> Any:
    constraints: dict[str, Any] = {}
    if kind in ("integer", "number"):
        constraints = _number_constraints(spec)
    if kind in _LENGTH_BOUNDS:
        constraints = {
            argument: spec[key]
            for key, argument in _LENGTH_BOUNDS[kind].items()
            if _is_count(spec.get(key))
        }
    if kind == "string" and _is_pattern(spec.get("pattern")):
        constraints["pattern"] = spec["pattern"]
    return Annotated[base, Field(**constraints)] if constraints else base


def _number_constraints(spec: dict[str, Any]) -> dict[str, Any]:
    constraints: dict[str, Any] = {
        argument: spec[key] for key, argument in _NUMBER_BOUNDS.items() if _is_number(spec.get(key))
    }
    for flag, bound, strict, loose in (
        ("exclusiveMinimum", "minimum", "gt", "ge"),
        ("exclusiveMaximum", "maximum", "lt", "le"),
    ):
        if spec.get(flag) is True and loose in constraints:
            constraints[strict] = constraints.pop(loose)
    if constraints.get("multiple_of") == 0:
        del constraints["multiple_of"]
    return constraints


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_pattern(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        re.compile(value)
    except re.error:
        return False
    return True
