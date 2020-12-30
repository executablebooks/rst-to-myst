from docutils import nodes


class RoleNode(nodes.Element):
    pass


class DirectiveNode(nodes.Element):
    pass


class ArgumentNode(nodes.Element):
    """The parsed argument of a directive."""


class ContentNode(nodes.Element):
    """The parsed content of a directive."""


class FrontMatterNode(nodes.Element):
    """Contains the first field list in the document."""
