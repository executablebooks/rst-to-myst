from typing import Any, List, Tuple

from docutils import nodes


class UnprocessedText(nodes.Text):
    """Text that should not be processed in any way (e.g. escaping characters)."""


class EvalRstNode(nodes.Element):
    """Should contain a single ``Text`` node with the contents to wrap."""


class RoleNode(nodes.Element):
    pass


class DirectiveNode(nodes.Element):
    """This node will have an optional ``ArgumentNode`` and/or ``ContentNode`` child."""

    def __init__(
        self,
        rawsource,
        *,
        name: str,
        module: str,
        conversion: str,
        options_list: List[Tuple[str, Any]],
        **kwargs
    ) -> None:
        super().__init__(
            rawsource,
            name=name,
            module=module,
            conversion=conversion,
            options_list=options_list,
            **kwargs
        )


class ArgumentNode(nodes.Element):
    """The parsed argument of a directive."""


class ContentNode(nodes.Element):
    """The parsed content of a directive."""


class FrontMatterNode(nodes.Element):
    """Contains the first field list in the document."""
