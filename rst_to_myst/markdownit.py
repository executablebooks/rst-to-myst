"""Convert to markdown-it tokens, which can then be rendered by mdformat."""
from io import StringIO
from typing import IO, Any, Dict, List, NamedTuple, Optional

from docutils import nodes
from markdown_it.token import Token


class RenderOutput(NamedTuple):
    tokens: List[Token]
    env: Dict[str, Any]


class MarkdownItRenderer(nodes.GenericNodeVisitor):
    def __init__(
        self,
        document: nodes.document,
        *,
        warning_stream: Optional[IO] = None,
        raise_on_error=False,
    ):
        self._document = document
        self._tokens: List[Token] = []
        self._env = {"references": {}, "duplicate_refs": []}
        self._inline: Optional[Token] = None
        self._warning_stream = warning_stream or StringIO()
        self.raise_on_error = raise_on_error

    @property
    def document(self) -> nodes.document:
        return self._document

    def warning(self, message: str):
        self._warning_stream.write(f"RENDER WARNING: {message}\n")

    def to_tokens(self) -> RenderOutput:
        """Reset tokens and convert full document."""
        self._tokens = []
        self._env = {"references": {}, "duplicate_refs": []}
        self._document.walkabout(self)
        return RenderOutput(self._tokens[:], self._env)

    def add_token(self, ttype: str, tag: str, nesting: int, **kwargs: Any) -> Token:
        """A markdown-it token to the stream, handling inline tokens and children."""
        token = Token(ttype, tag, nesting, **kwargs)
        # decide whether we should be adding as an inline child
        if ttype in {"paragraph_open", "heading_open", "th_open", "td_open"}:
            self._tokens.append(token)
            self._inline = Token("inline", "", 0, children=[])
            self._tokens.append(self._inline)
        elif ttype in {"paragraph_close", "heading_close", "th_close", "td_close"}:
            self._tokens.append(token)
            self._inline = None
        elif self._inline:
            self._inline.children.append(token)
        else:
            self._tokens.append(token)
        return token

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

    # Skipped components

    def visit_document(self, node):
        pass

    def depart_document(self, node):
        pass

    def visit_Element(self, node):
        pass

    def depart_Element(self, node):
        pass

    def visit_system_message(self, node):
        # ignore
        raise nodes.SkipNode

    def visit_problematic(self, node):
        # ignore
        raise nodes.SkipNode

    # CommonMark components

    def visit_section(self, node):
        pass  # handled by title

    def depart_section(self, node):
        pass

    def visit_title(self, node):
        token = self.add_token("heading_open", f"h{node['level']}", 1)
        token.markup = "#" * node["level"]

    def depart_title(self, node):
        token = self.add_token("heading_close", f"h{node['level']}", -1)
        token.markup = "#" * node["level"]

    def visit_paragraph(self, node):
        self.add_token("paragraph_open", "p", 1)

    def depart_paragraph(self, node):
        self.add_token("paragraph_close", "p", -1)

    def visit_Text(self, node):
        token = self.add_token("text", "", 0)
        token.content = node.astext()

    def depart_Text(self, node):
        pass

    def visit_emphasis(self, node):
        self.add_token("em_open", "em", 1, markup="*")

    def depart_emphasis(self, node):
        self.add_token("em_close", "em", -1, markup="*")

    def visit_strong(self, node):
        self.add_token("strong_open", "strong", 1, markup="**")

    def depart_strong(self, node):
        self.add_token("strong_close", "strong", -1, markup="**")

    def visit_bullet_list(self, node):
        self.add_token("bullet_list_open", "ul", 1, markup=node["bullet"])

    def depart_bullet_list(self, node):
        self.add_token("bullet_list_close", "ul", -1, markup=node["bullet"])

    def visit_enumerated_list(self, node):
        token = self.add_token("ordered_list_open", "ol", 1, markup=".")
        if "start" in node:
            token.attrs["start"] = node["start"]

    def depart_enumerated_list(self, node):
        self.add_token("ordered_list_close", "ol", -1, markup=".")

    def visit_list_item(self, node):
        token = self.add_token("list_item_open", "li", 1)
        if "style" in node:
            if node["style"] == "bullet":
                token.markup = node["prefix"].strip()
            elif node["style"] == "enumerated":
                token.markup = "."

    def depart_list_item(self, node):
        self.add_token("list_item_close", "li", -1)

    def visit_literal(self, node):
        token = self.add_token("code_inline", "code", 0, markup="`")
        token.content = node.astext()
        raise nodes.SkipNode

    def visit_literal_block(self, node):
        token = self.add_token("code_block", "code", 0)
        token.content = node.astext()
        raise nodes.SkipNode

    def visit_block_quote(self, node):
        self.add_token("blockquote_open", "blockquote", 1, markup=">")

    def depart_block_quote(self, node):
        self.add_token("blockquote_close", "blockquote", -1, markup=">")

    def visit_reference(self, node):
        # we assume all reference names are plain text
        # TODO check this is always the case
        text = node.astext()

        if "standalone_uri" in node:
            # autolink
            token = self.add_token("link_open", "a", 1, markup="autolink", info="auto")
            token.attrs["href"] = node["refuri"]
            self.add_token("text", "", 0, content=node["refuri"])
            self.add_token("link_close", "a", -1, markup="autolink", info="auto")
        elif "refname" in node:
            # reference a link definition `[refname]: url`, or a target `(refname)=`
            # TODO ensure mdformat does not wrap in <>
            token = self.add_token(
                "link_open",
                "a",
                1,
                attrs={"href": node["refname"]},
                # TODO should only add label if target found
                meta={"label": node["refname"]},
            )
            self.add_token("text", "", 0, content=text)
            self.add_token("link_close", "a", -1)
        elif "refuri" in node:
            # external link
            token = self.add_token("link_open", "a", 1, attrs={"href": node["refuri"]})
            self.add_token("text", "", 0, content=text)
            self.add_token("link_close", "a", -1)
        elif "refid" in node:
            # anonymous links, pointing to internal targets
            # TODO ensure mdformat does not wrap in <>
            token = self.add_token("link_open", "a", 1, attrs={"href": node["refid"]})
            self.add_token("text", "", 0, content=text)
            self.add_token("link_close", "a", -1)
        else:
            message = f"unknown reference type: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)

        raise nodes.SkipNode

    def visit_target(self, node):
        if "inline" in node and node["inline"]:
            # TODO inline targets
            message = f"inline targets not implemented: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)
            self.add_token("text", "", 0, content=str(node.rawsource))
            raise nodes.SkipNode

        if "refuri" in node:
            for name in node["names"]:
                # [{name}]: {node['refuri']}
                # TODO warn about name starting ^
                if name not in self._env["references"]:
                    self._env["references"][name] = {
                        "title": "",
                        "href": node["refuri"],
                        "map": [node.line, node.line],
                    }
                else:
                    self._env["duplicate_refs"].append(
                        {
                            "label": name,
                            "title": "",
                            "href": node["refuri"],
                            "map": [node.line, node.line],
                        }
                    )
        elif "names" in node:
            for _name in node["names"]:
                # TODO
                pass  # self.add_lines([f"({name})="])
        if "refid" in node:
            # should only be for anonymous
            # TODO
            pass  # self.add_lines([f"({node['refid']})="])

        # TODO check for content?
        raise nodes.SkipNode
