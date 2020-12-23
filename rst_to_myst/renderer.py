from io import StringIO
from textwrap import indent
from typing import IO, Optional, Tuple

from docutils import nodes

from .parser import to_ast


class MystRenderer(nodes.GenericNodeVisitor):
    def __init__(
        self, document, warning_stream=None, raise_on_error=False, cite_prefix="cite_"
    ):
        self.document = document
        self._rendered: str = ""
        self._indent: int = 0
        self._warning_stream: IO = warning_stream or StringIO()
        self.raise_on_error = raise_on_error
        self._uri_refnames = None
        self.cite_prefix = cite_prefix
        self.extensions_required = set()

    @property
    def rendered(self) -> str:
        return self._rendered

    def warning(self, message: str):
        self._warning_stream.write(f"RENDER WARNING: {message}\n")

    def incr_indent(self, i: int):
        self._indent += i

    def decr_indent(self, i: int):
        self._indent -= i
        assert self._indent >= 0, "indent decreased to <0"

    def add_indent(self):
        if self._indent:
            self._rendered += " " * self._indent

    def add_inline(self, text: str):
        if self._indent:
            text = indent(text, " " * self._indent)[self._indent :]
        self._rendered += text

    def add_newline(self, i=1):
        self._rendered += "\n" * i

    def add_lines(self, lines, newline_before=False, newline_after=False):
        if newline_before:
            self._rendered += "\n"
        text = "\n".join(lines)
        if self._indent:
            text = indent(text, " " * self._indent)
        self._rendered += text
        if newline_after:
            self._rendered += "\n"

    def default_visit(self, node):
        message = f"no visit method for: {node.__class__}"
        self.warning(message)
        if self.raise_on_error:
            raise NotImplementedError(message)

    def default_departure(self, node):
        message = f"no depart method for: {node.__class__}"
        self.warning(message)
        if self.raise_on_error:
            raise NotImplementedError(message)

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        pass

    def visit_system_message(self, node):
        # ignore
        raise nodes.SkipNode

    def visit_problematic(self, node):
        # ignore
        raise nodes.SkipNode

    def visit_section(self, node):
        pass  # handled by title

    def depart_section(self, node):
        pass

    def visit_title(self, node):
        self.add_lines([("#" * node["level"]) + " "])

    def depart_title(self, node):
        self.add_newline(2)

    def visit_paragraph(self, node):
        # don't indent if the first element in another block
        if node.parent.children[0] != node:
            self.add_indent()
        elif not isinstance(
            node.parent, (nodes.footnote, nodes.citation, nodes.list_item)
        ):
            self.add_indent()

    def depart_paragraph(self, node):
        self.add_newline(2)

    def visit_Text(self, node):
        self.add_inline(node.astext())

    def depart_Text(self, node):
        pass

    # note: for emphasis and strong, nested inline is not allowed,
    # so we do not need to worry about that

    def visit_emphasis(self, node):
        self.add_inline("*")

    def depart_emphasis(self, node):
        self.add_inline("*")

    def visit_strong(self, node):
        self.add_inline("**")

    def depart_strong(self, node):
        self.add_inline("**")

    def visit_RoleNode(self, node):
        # TODO nested parse of specific roles
        self.add_inline(f"{{{node['role']}}}`{node['text']}`")

    def depart_RoleNode(self, node):
        pass

    def visit_literal(self, node):
        self.add_inline("`")

    def depart_literal(self, node):
        self.add_inline("`")

    def visit_transition(self, node):
        self.add_lines(["---"])

    def depart_transition(self, node):
        self.add_newline(2)

    def visit_comment(self, node):
        self.add_lines(["<!---"], False, True)

    def depart_comment(self, node):
        self.add_lines(["-->"], True)
        self.add_newline(2)

    def visit_target(self, node):
        if "inline" in node and node["inline"]:
            # TODO inline targets
            message = f"inline targets not implemented: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)
            self.add_inline(str(node.rawsource))
            raise nodes.SkipNode

        if "refuri" in node:
            for name in node["names"]:
                # TODO warn about name starting ^
                self.add_lines([f"[{name}]: {node['refuri']}"])
                self.add_newline(2)
        elif "names" in node:
            for name in node["names"]:
                self.add_lines([f"({name})="])
                self.add_newline(2)
        if "refid" in node:
            # should only be for anonymous
            self.add_lines([f"({node['refid']})="])
            self.add_newline(2)

        # TODO check for content?
        raise nodes.SkipNode

    def depart_target(self, node):
        pass

    def is_target_uri(self, refname):
        """Return True, if a refname points towards a target which is an external URI

        This is used to decide if a reference should be [][refname] or [](refname)
        """
        if self._uri_refnames is None:
            self._uri_refnames = set()
            for target in self.document.traverse(nodes.target):
                if "refuri" in target:
                    for name in target["names"]:
                        self._uri_refnames.add(name)
        return refname in self._uri_refnames

    def visit_reference(self, node):

        if "standalone_uri" in node:
            # auto-link
            self.add_inline(f"<{node['refuri']}>")
            raise nodes.SkipNode

        self.add_inline("[")

    def depart_reference(self, node):
        # TODO embedded targets
        self.add_inline("]")
        if "refname" in node:
            if self.is_target_uri(node["refname"]):
                # will reference a link definition `[refname]: url`
                self.add_inline(f"[{node['refname']}]")
            else:
                # will reference a target `(refname)=`
                self.add_inline(f"({node['refname']})")
        elif "refuri" in node:
            self.add_inline(f"(<{node['refuri']}>)")
        elif "refid" in node:
            # this should only be the case for anonymous links,
            # pointing to internal targets
            self.add_inline(f"({node['refid']})")
        else:
            message = f"unknown reference type: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)

    def visit_substitution_reference(self, node):
        self.extensions_required.add("substitution")
        self.add_inline(f"{{{{ {node['refname']} }}}}")
        # the node also contains the refname as text, but we don't need that
        raise nodes.SkipNode

    def depart_substitution_reference(self, node):
        pass

    def visit_footnote_reference(self, node):
        if "refname" in node:
            # normal reference
            self.add_inline(f"[^{node['refname']}]")
        elif "refid" in node:
            # auto number/symbol reference
            self.add_inline(f"[^{node['refid']}]")
        else:
            message = f"unknown footnote reference type: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)
        # the node also contains the refname as text, but we don't need that
        raise nodes.SkipNode

    def visit_citation_reference(self, node):
        refname = node["refname"] if "refname" in node else node["refid"]
        # for compatibility we treat citations the same as footnotes, with a prefix
        self.add_inline(f"[^{self.cite_prefix}{refname}]")
        # the node also contains the refname as text, but we don't need that
        raise nodes.SkipNode

    def visit_footnote(self, node):
        refname = node["ids"][0]  # TODO assuming there is only one id
        self.add_lines([f"[^{refname}]: "])
        self.incr_indent(2)

    def depart_footnote(self, node):
        self.decr_indent(2)
        # self.add_newline(1)

    def visit_citation(self, node):
        # same as for visit_footnote
        refname = node["names"][0]  # TODO assuming there is only one name
        self.add_lines([f"[^{self.cite_prefix}{refname}]: "])
        self.incr_indent(2)

    def depart_citation(self, node):
        self.decr_indent(2)
        # self.add_newline(1)

    def visit_DirectiveNode(self, node):
        # The default is simply to wrap in eval-rst
        # TODO decide which/how directives can be converted/expanded
        name = node["name"]
        content = node["indented"]
        indent_len = node["indent"]
        self.add_lines(
            ["```{eval-rst}", f".. {name}:: " + (content[0] if content else "")]
            + indent("\n".join(content[1:]), " " * indent_len).splitlines()
            + ["```"],
        )
        self.add_newline(2)

    def depart_DirectiveNode(self, node):
        pass

    # we handle setting list item attributes in a transform

    def visit_bullet_list(self, node):
        pass

    def depart_bullet_list(self, node):
        self.add_newline()

    def visit_enumerated_list(self, node):
        pass

    def depart_enumerated_list(self, node):
        self.add_newline()

    def visit_list_item(self, node):
        self.add_lines([node["prefix"]])
        self.incr_indent(len(node["prefix"]))

    def depart_list_item(self, node):
        # remove new line between items
        self._rendered = self._rendered.rstrip()
        self.add_newline()
        self.decr_indent(len(node["prefix"]))

    # TODO https://docutils.sourceforge.io/docs/user/rst/quickref.htm
    # quote_block, substitution definitions,
    # tables, deflist, line block, literal block, field list,


def render(
    document: nodes.document, warning_stream: Optional[IO] = None, **kwargs
) -> Tuple[str, IO]:
    renderer = MystRenderer(document, warning_stream, **kwargs)
    document.walkabout(renderer)
    # TODO also return or print renderer.extensions_required
    # TODO remove double black lines
    # TODO remove spaces in blank lines
    return renderer.rendered, renderer._warning_stream


def convert(
    text: str,
    warning_stream: Optional[IO] = None,
    raise_on_error: bool = False,
    cite_prefix: str = "cite_",
) -> Tuple[str, IO]:
    document, warning_stream = to_ast(text, warning_stream=warning_stream)
    text, warning_stream = render(
        document, warning_stream, cite_prefix=cite_prefix, raise_on_error=raise_on_error
    )
    return text, warning_stream
