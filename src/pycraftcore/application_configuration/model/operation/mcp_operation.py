import re
from dataclasses import dataclass, field
from typing import Annotated, Any, ClassVar

from pydantic import ConfigDict, Discriminator, Tag

from pycraftcore.application_configuration.model.connector.mcp_connector import McpConnector
from pycraftcore.application_configuration.model.operation.base_operation import BaseOperation

_MCP_TOOL_NAME = re.compile(r"[A-Za-z0-9_.-]{1,128}")
_MCP_TOOL_NAME_RULE: str = "1 to 128 letters, digits, '_', '-' or '.'"
_MOVED_OUT_OF_PARAMETERS: tuple[str, ...] = ("prefix", "tools", "headers", "header")


def _is_mcp_tool_name(value: str) -> bool:
    return _MCP_TOOL_NAME.fullmatch(value) is not None


@dataclass(frozen=True, slots=True)
class McpTool:
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    name: str
    tool: str
    description: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        for label, value in (("name", self.name), ("tool", self.tool)):
            if not _is_mcp_tool_name(value):
                raise ValueError(f"mcp tool {label} {value!r} must be {_MCP_TOOL_NAME_RULE}")
        if self.description is not None and not self.description.strip():
            raise ValueError(f"mcp tool {self.name!r}: description must not be blank")
        if any(not key.strip() for key in self.arguments):
            raise ValueError(f"mcp tool {self.name!r}: argument names must not be blank")


def _tool_entry_kind(value: Any) -> str:
    return "name" if isinstance(value, str) else "wrapper"


McpToolEntry = Annotated[
    Annotated[str, Tag("name")] | Annotated[McpTool, Tag("wrapper")],
    Discriminator(_tool_entry_kind),
]


@dataclass(slots=True)
class McpOperation(BaseOperation):
    __pydantic_config__: ClassVar[ConfigDict] = ConfigDict(extra="forbid")

    connector: McpConnector
    prefix: str | None = None
    tools: list[McpToolEntry] = field(default_factory=list)
    headers: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self._check_prefix()
        self._check_nothing_left_in_parameters()
        self._check_listed_tools()
        self._check_names_are_unique()

    @property
    def listed_tools(self) -> tuple[str, ...]:
        return tuple(entry for entry in self.tools if isinstance(entry, str))

    @property
    def wrapped_tools(self) -> tuple[McpTool, ...]:
        return tuple(entry for entry in self.tools if isinstance(entry, McpTool))

    def _check_prefix(self) -> None:
        if self.prefix is not None and not _is_mcp_tool_name(self.prefix):
            raise ValueError(
                f"mcp operation {self.name!r}: prefix {self.prefix!r} must be {_MCP_TOOL_NAME_RULE}"
            )

    def _check_nothing_left_in_parameters(self) -> None:
        moved: list[str] = [key for key in _MOVED_OUT_OF_PARAMETERS if key in self.parameters]
        if moved:
            keys: str = ", ".join(f"parameters.{key}" for key in moved)
            raise ValueError(
                f"mcp operation {self.name!r}: move {keys} to the operation itself (pycraftcore 7)"
            )

    def _check_listed_tools(self) -> None:
        unreadable: list[str] = [
            repr(entry)
            for entry in self.listed_tools
            if not entry.strip() or entry != entry.strip()
        ]
        if unreadable:
            raise ValueError(
                f"mcp operation {self.name!r}: listed tools must not be blank or start or end "
                f"with spaces: {', '.join(unreadable)}"
            )

    def _check_names_are_unique(self) -> None:
        names: list[str] = [*self.listed_tools, *(tool.name for tool in self.wrapped_tools)]
        duplicated: list[str] = sorted({name for name in names if names.count(name) > 1})
        if duplicated:
            raise ValueError(
                f"mcp operation {self.name!r}: tools named more than once: {', '.join(duplicated)}"
            )
