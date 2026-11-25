from typing import Any

import pytest
from pydantic import BaseModel, ValidationError

from pycraftcore.mcp.adapter import model_from_schema


def model(
    properties: dict[str, Any], required: tuple[str, ...] = (), **extra: Any
) -> type[BaseModel]:
    schema: dict[str, Any] = {
        "type": "object",
        "properties": properties,
        "required": list(required),
    }
    return model_from_schema("probe", schema | extra)


def accepts(probe: type[BaseModel], value: Any) -> bool:
    try:
        probe.model_validate({"value": value})
    except ValidationError:
        return False
    return True


@pytest.mark.parametrize(
    ("spec", "good", "bad"),
    [
        ({"enum": ["asc", "desc"]}, "asc", "sideways"),
        ({"type": "string", "enum": ["asc", "desc"]}, "desc", "ASC"),
        ({"const": "read"}, "read", "write"),
        ({"enum": [1, 2, None]}, None, 3),
        ({"type": "integer", "minimum": 1, "maximum": 50}, 50, 51),
        ({"type": "integer", "minimum": 1}, 1, 0),
        ({"type": "number", "exclusiveMinimum": 0}, 0.1, 0),
        ({"type": "number", "exclusiveMaximum": 1}, 0.9, 1),
        ({"type": "number", "minimum": 0, "exclusiveMinimum": True}, 0.1, 0),
        ({"type": "integer", "multipleOf": 5}, 15, 12),
        ({"type": "string", "minLength": 2, "maxLength": 3}, "abc", "abcd"),
        ({"type": "string", "minLength": 2}, "ab", "a"),
        ({"type": "string", "pattern": "^[a-z_]+$"}, "kitchen", "Kitchen"),
        ({"type": "string", "pattern": "^(?!system\\.)"}, "recipes", "system.users"),
        (
            {"type": "array", "items": {"type": "string"}, "maxItems": 2},
            ["a", "b"],
            ["a", "b", "c"],
        ),
        ({"type": "array", "minItems": 1}, [1], []),
        ({"type": "array", "items": {"type": "integer", "maximum": 9}}, [1, 9], [1, 10]),
        ({"anyOf": [{"type": "integer"}, {"type": "string", "maxLength": 2}]}, "ab", "abc"),
        ({"oneOf": [{"type": "boolean"}, {"enum": ["auto"]}]}, "auto", "manual"),
        ({"type": ["string", "null"], "maxLength": 2}, None, "abc"),
    ],
)
def test_a_constraint_of_the_schema_is_kept(spec: dict[str, Any], good: Any, bad: Any) -> None:
    probe = model({"value": spec}, required=("value",))

    assert accepts(probe, good)
    assert not accepts(probe, bad)


def test_a_reference_into_the_definitions_keeps_its_constraints() -> None:
    page = {"type": "object", "properties": {"size": {"type": "integer", "maximum": 100}}}
    for key in ("$defs", "definitions"):
        probe = model(
            {"value": {"$ref": f"#/{key}/Page"}}, required=("value",), **{key: {"Page": page}}
        )

        assert accepts(probe, {"size": 100})
        assert not accepts(probe, {"size": 101})


def test_a_single_all_of_is_read_as_the_schema_it_holds() -> None:
    probe = model(
        {"value": {"allOf": [{"$ref": "#/$defs/Order"}], "description": "Sort order."}},
        required=("value",),
        **{"$defs": {"Order": {"enum": ["asc", "desc"]}}},
    )

    assert accepts(probe, "asc")
    assert not accepts(probe, "up")


def test_a_nested_object_keeps_its_required_keys_and_value_constraints() -> None:
    where = {
        "type": "object",
        "properties": {
            "field": {"type": "string", "description": "Field to compare."},
            "op": {"enum": ["=", "<"]},
        },
        "required": ["field"],
    }
    probe = model({"value": where}, required=("value",))

    assert accepts(probe, {"field": "name", "op": "<"})
    assert not accepts(probe, {"op": "="})
    assert not accepts(probe, {"field": "name", "op": "!"})
    nested = probe.model_json_schema()["$defs"]["probe_value"]["properties"]["field"]
    assert nested["description"] == "Field to compare."


def test_a_nested_object_is_sent_back_exactly_as_given() -> None:
    filter_ = {
        "type": "object",
        "properties": {"deletedAt": {"type": ["string", "null"]}, "_id": {"type": "string"}},
    }
    probe = model({"value": filter_}, required=("value",))

    given = {"deletedAt": None, "_id": "42", "$set": {"x": 1}}
    dumped = probe.model_validate({"value": given}).model_dump(exclude_unset=True)

    assert dumped == {"value": given}
    assert probe.model_validate({"value": {}}).model_dump(exclude_unset=True) == {"value": {}}


def test_a_nested_object_closed_by_its_schema_refuses_other_keys() -> None:
    closed = {
        "type": "object",
        "properties": {"field": {"type": "string"}},
        "additionalProperties": False,
    }
    probe = model({"value": closed}, required=("value",))

    assert accepts(probe, {"field": "name"})
    assert not accepts(probe, {"field": "name", "other": 1})


def test_an_object_without_properties_keeps_the_type_of_its_values() -> None:
    counts = {"type": "object", "additionalProperties": {"type": "integer", "minimum": 0}}
    probe = model({"value": counts}, required=("value",))

    assert accepts(probe, {"recipes": 3})
    assert not accepts(probe, {"recipes": -1})
    assert accepts(model({"value": {"type": "object"}}, required=("value",)), {"any": [1]})


@pytest.mark.parametrize(
    ("spec", "value"),
    [
        ({"type": "string", "format": "date-time"}, "not a date"),
        ({"type": "string", "pattern": "\\p{L}+"}, "123"),
        ({"type": "integer", "minimum": "5"}, 1),
        ({"type": "string", "maxLength": -1}, "abc"),
        ({"type": "integer", "multipleOf": 0}, 7),
        ({"enum": [{"a": 1}, [1]]}, "anything"),
        ({"type": "array", "items": True}, [1, "a"]),
        ({"$ref": "https://example.com/schema.json"}, {"any": 1}),
        ({"$ref": "#/$defs/Missing"}, 1),
        ({"allOf": [{"type": "string"}, {"maxLength": 2}]}, 3),
        ({"type": "whatever"}, 1),
    ],
)
def test_a_keyword_that_cannot_be_kept_faithfully_is_not_made_stricter(
    spec: dict[str, Any], value: Any
) -> None:
    assert accepts(model({"value": spec}, required=("value",)), value)


def test_a_recursive_reference_stops_at_the_recursion() -> None:
    node = {
        "type": "object",
        "properties": {
            "name": {"type": "string", "maxLength": 3},
            "children": {"type": "array", "items": {"$ref": "#/$defs/Node"}},
        },
    }
    probe = model(
        {"value": {"$ref": "#/$defs/Node"}}, required=("value",), **{"$defs": {"Node": node}}
    )

    assert accepts(probe, {"name": "a", "children": [{"name": "toolong", "children": []}]})
    assert not accepts(probe, {"name": "toolong"})


def test_an_optional_argument_keeps_its_default_and_accepts_none() -> None:
    probe = model({"limit": {"type": "integer", "maximum": 50, "default": 10}})

    assert probe().model_dump() == {"limit": 10}
    assert probe(limit=None).model_dump() == {"limit": None}
    with pytest.raises(ValidationError):
        probe(limit=51)


def test_a_schema_without_properties_still_takes_any_argument() -> None:
    probe = model_from_schema("probe", {"type": "object", "properties": {}})

    assert probe.model_validate({"anything": 1}).model_dump() == {"anything": 1}
