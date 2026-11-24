import pytest

from pycraftcore.application_configuration.enum.operation_type import OperationType
from pycraftcore.application_configuration.model import McpOperation, McpTool
from tests.application_configuration.model.connectors import mcp_connector


def make_mcp_operation(**overrides) -> McpOperation:
    values = dict(name="kitchen", type=OperationType.mcp, connector=mcp_connector())
    values.update(overrides)
    return McpOperation(**values)


def test_a_wrapped_tool_has_no_description_or_fixed_arguments_by_default():
    tool = McpTool(name="recipes_find", tool="mongodb_find")

    assert (tool.description, tool.arguments) == (None, {})


def test_a_wrapped_tool_name_may_use_dots_dashes_and_128_characters():
    tool = McpTool(name="kitchen.recipes-find", tool="x" * 128)

    assert (tool.name, len(tool.tool)) == ("kitchen.recipes-find", 128)


@pytest.mark.parametrize(
    ("values", "message"),
    [
        ({"name": "recipes find"}, "name 'recipes find' must be 1 to 128"),
        ({"name": ""}, "name '' must be 1 to 128"),
        ({"name": "x" * 129}, "must be 1 to 128"),
        ({"name": "recipes_find\n"}, "must be 1 to 128"),
        ({"tool": "mongodb/find"}, "tool 'mongodb/find' must be 1 to 128"),
        ({"tool": "mongodb_find\n"}, "must be 1 to 128"),
        ({"description": "  "}, "description must not be blank"),
        ({"arguments": {" ": "kitchen"}}, "argument names must not be blank"),
    ],
)
def test_a_wrapped_tool_that_cannot_be_published_is_refused(values, message):
    with pytest.raises(ValueError, match=message):
        McpTool(**{"name": "recipes_find", "tool": "mongodb_find"} | values)


def test_an_mcp_operation_has_no_prefix_tools_or_parameters_by_default():
    operation = make_mcp_operation()

    assert (operation.prefix, operation.tools, operation.parameters) == (None, [], {})


def test_an_mcp_operation_splits_named_tools_from_wrapped_ones_in_order():
    find = McpTool(name="recipes_find", tool="mongodb_find", arguments={"collection": "recipes"})
    schema = McpTool(name="recipes_schema", tool="mongodb_collection_schema")
    operation = make_mcp_operation(tools=["python_executor", find, "file_*", schema])

    assert operation.listed_tools == ("python_executor", "file_*")
    assert operation.wrapped_tools == (find, schema)


@pytest.mark.parametrize("prefix", ["", "mongo db", "mongo/db", "kitchen\n", "x" * 129])
def test_a_prefix_that_cannot_start_a_tool_name_is_refused(prefix):
    with pytest.raises(ValueError, match=r"prefix .* must be 1 to 128"):
        make_mcp_operation(prefix=prefix)


@pytest.mark.parametrize(
    ("parameters", "keys"),
    [
        ({"tools": ["jira_search"]}, r"parameters\.tools"),
        ({"prefix": "jira", "tools": []}, r"parameters\.prefix, parameters\.tools"),
    ],
)
def test_a_6x_prefix_or_tools_left_in_parameters_is_refused(parameters, keys):
    with pytest.raises(ValueError, match=rf"'kitchen': move {keys} to the operation itself"):
        make_mcp_operation(parameters=parameters)


def test_other_parameters_are_passed_through():
    operation = make_mcp_operation(parameters={"header": {"x-team": "kitchen"}})

    assert operation.parameters == {"header": {"x-team": "kitchen"}}


@pytest.mark.parametrize("entry", ["", "  ", " python_executor", "python_executor\n"])
def test_a_listed_tool_that_can_match_nothing_is_refused(entry):
    with pytest.raises(ValueError, match="listed tools must not be blank or start or end"):
        make_mcp_operation(tools=["file_reader", entry])


@pytest.mark.parametrize(
    "tools",
    [
        ["python_executor", "python_executor"],
        [
            McpTool(name="recipes_find", tool="mongodb_find"),
            McpTool(name="recipes_find", tool="mongodb_aggregate"),
        ],
        [
            "mongodb_find",
            McpTool(name="mongodb_find", tool="mongodb_find", arguments={"database": "kitchen"}),
        ],
    ],
)
def test_a_tool_name_used_twice_in_one_operation_is_refused(tools):
    with pytest.raises(ValueError, match="'kitchen': tools named more than once"):
        make_mcp_operation(tools=tools)


def test_every_name_used_twice_is_named_in_one_message():
    tools = [
        "b_tool",
        "a_tool",
        McpTool(name="a_tool", tool="x"),
        McpTool(name="b_tool", tool="y"),
    ]

    with pytest.raises(ValueError, match="more than once: a_tool, b_tool$"):
        make_mcp_operation(tools=tools)


def test_a_wrapped_tool_may_keep_the_name_of_the_tool_it_is_built_on():
    locked = McpTool(name="mongodb_find", tool="mongodb_find", arguments={"database": "kitchen"})

    assert make_mcp_operation(tools=[locked]).wrapped_tools == (locked,)


def test_a_pattern_is_not_compared_with_the_names_it_could_match():
    operation = make_mcp_operation(tools=["mongodb_*", McpTool(name="mongodb_find", tool="x")])

    assert operation.listed_tools == ("mongodb_*",)
