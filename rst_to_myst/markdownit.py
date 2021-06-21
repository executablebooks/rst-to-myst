"""Convert to markdown-it tokens, which can then be rendered by mdformat."""
from io import StringIO
from textwrap import indent
from typing import IO, Any, Dict, List, NamedTuple, Optional, Union

from docutils import nodes
from markdown_it.token import Token

from .utils import yaml_dump


class RenderOutput(NamedTuple):
    tokens: List[Token]
    env: Dict[str, Any]


class MarkdownItRenderer(nodes.GenericNodeVisitor):
    """Render docutils AST to Markdown-It token stream."""

    def __init__(
        self,
        document: nodes.document,
        *,
        warning_stream: Optional[IO] = None,
        raise_on_error: bool = False,
        cite_prefix: str = "cite_",
        default_role: Optional[str] = None,
    ):
        self._document = document
        self._warning_stream = warning_stream or StringIO()
        self.raise_on_error = raise_on_error
        # prefix added to citation labels
        self.cite_prefix = cite_prefix
        # if no default role, convert to literal
        self.default_role = default_role

        self.reset_state()

    def reset_state(self):
        # record current state, that can affect children tokens
        self._tokens: List[Token] = []
        self._env = {"references": {}, "duplicate_refs": []}
        self._inline: Optional[Token] = None
        self.parent_tokens: Dict[str, int] = {}
        self._front_matter: Dict[str, Union[str, bool, int, float, dict, list]] = {}

    @property
    def document(self) -> nodes.document:
        return self._document

    def warning(self, message: str):
        self._warning_stream.write(f"RENDER WARNING: {message}\n")

    def to_tokens(self) -> RenderOutput:
        """Reset tokens and convert full document."""
        self.reset_state()
        self._document.walkabout(self)
        if self._front_matter:
            self._tokens.insert(
                0,
                Token(
                    "front_matter",
                    "",
                    0,
                    content=yaml_dump(self._front_matter),
                    markup="---",
                ),
            )
        return RenderOutput(self._tokens[:], self._env)

    def add_token(
        self, ttype: str, tag: str, nesting: int, *, content: str = "", **kwargs: Any
    ) -> Token:
        """A markdown-it token to the stream, handling inline tokens and children."""
        token = Token(ttype, tag, nesting, content=content, **kwargs)
        # record entries and exits
        if ttype.endswith("_open"):
            self.parent_tokens.setdefault(ttype[:-5], 0)
            self.parent_tokens[ttype[:-5]] += 1
        if ttype.endswith("_close"):
            self.parent_tokens.setdefault(ttype[:-6], 0)
            self.parent_tokens[ttype[:-6]] -= 1
            if self.parent_tokens[ttype[:-6]] <= 0:
                self.parent_tokens.pop(ttype[:-6])
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
        self.unknown_visit(node)

    def default_departure(self, node):
        self.unknown_departure(node)

    def unknown_visit(self, node):
        message = f"no visit method for: {node.__class__}"
        self.warning(message)
        if self.raise_on_error:
            raise NotImplementedError(message)

    def unknown_departure(self, node):
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
        if self.parent_tokens.get("th") or self.parent_tokens.get("td"):
            # table cells are treated as paragraphs already
            return
        token = self.add_token("paragraph_open", "p", 1)
        if self.parent_tokens.get("list_item"):
            # paragraphs in tight lists are hidden
            token.hidden = True

    def depart_paragraph(self, node):
        if self.parent_tokens.get("th") or self.parent_tokens.get("td"):
            # table cells are treated as paragraphs already
            return
        self.add_token("paragraph_close", "p", -1)

    def visit_Text(self, node):
        self.add_token("text", "", 0, content=node.astext())
        raise nodes.SkipNode

    def visit_emphasis(self, node):
        self.add_token("em_open", "em", 1, markup="*")

    def depart_emphasis(self, node):
        self.add_token("em_close", "em", -1, markup="*")

    def visit_strong(self, node):
        self.add_token("strong_open", "strong", 1, markup="**")

    def depart_strong(self, node):
        self.add_token("strong_close", "strong", -1, markup="**")

    def visit_transition(self, node):
        self.add_token("hr", "hr", 0, markup="---")
        raise nodes.SkipNode

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
        self.add_token("code_inline", "code", 0, markup="`", content=node.astext())
        raise nodes.SkipNode

    def visit_literal_block(self, node):
        text = node.astext()
        if not text.endswith("\n"):
            text += "\n"
        self.add_token("code_block", "code", 0, content=text)
        raise nodes.SkipNode

    def visit_block_quote(self, node):
        self.add_token("blockquote_open", "blockquote", 1, markup=">")

    def depart_block_quote(self, node):
        self.add_token("blockquote_close", "blockquote", -1, markup=">")

    def visit_attribution(self, node):
        # Markdown block quotes do not have an attribution syntax,
        # so we add a best approximation
        token = self.add_token("html_inline", "", 0)
        token.content = f'<p class="attribution">—{node.astext()}</p>'
        raise nodes.SkipNode

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
                # TODO warn about name starting ^ (clashes with footnotes)
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
            for name in node["names"]:
                self.add_token(
                    "myst_target", "", 0, attrs={"class": "myst-target"}, content=name
                )
        if "refid" in node:
            self.add_token(
                "myst_target",
                "",
                0,
                attrs={"class": "myst-target"},
                content=node["refid"],
            )

        # TODO check for content?
        raise nodes.SkipNode

    # Standard CommonMark extensions

    def parse_gfm_table(self, node) -> bool:
        """Check whether an RST table can be converted to a GFM one.

        RST tables can have e.g. cells spanning multiple columns/rows,
        which the GitHub Flavoured Markdown (GFM) table variant does not support.
        """
        # must have one child tgroup
        if len(node.children) != 1 or not isinstance(node.children[0], nodes.tgroup):
            return False
        # tgroup should contain the number of columns
        tgroup = node.children[0]
        if "cols" not in tgroup:
            return False
        ncolumns = tgroup["cols"]
        # trgoup should contain children: (colspec)*, thead, tbody
        if len(tgroup.children) < 2:
            return False
        if not isinstance(tgroup.children[-2], nodes.thead):
            return False
        if not isinstance(tgroup.children[-1], nodes.tbody):
            return False
        thead = tgroup.children[-2]
        tbody = tgroup.children[-1]
        # the header can only have one row with the full amount of columns
        if len(thead.children) != 1 or len(thead.children[0]) != ncolumns:
            return False
        # each body row should have the full amount of columns
        for row in tbody.children:
            if len(row.children) != ncolumns:
                return False
        return True

    def visit_table(self, node):

        if not self.parse_gfm_table(node):
            text = node.rawsource
            if not text.endswith("\n"):
                text += "\n"
            self.add_token(
                "fence", "code", 0, content=text, markup="```", info="{eval_rst}"
            )
            raise nodes.SkipNode

        self.add_token("table_open", "table", 1)

    def depart_table(self, node):
        self.add_token("table_close", "table", -1)

    def visit_tgroup(self, node):
        pass

    def depart_tgroup(self, node):
        pass

    def visit_colspec(self, node):
        raise nodes.SkipNode

    def visit_thead(self, node):
        self.add_token("thead_open", "thead", 1)

    def depart_thead(self, node):
        self.add_token("thead_close", "thead", -1)

    def visit_tbody(self, node):
        self.add_token("tbody_open", "tbody", 1)

    def depart_tbody(self, node):
        self.add_token("tbody_close", "tbody", -1)

    def visit_row(self, node):
        self.add_token("tr_open", "tr", 1)

    def depart_row(self, node):
        self.add_token("tr_close", "tr", -1)

    def visit_entry(self, node):
        tag = "th" if self.parent_tokens.get("thead") else "td"
        self.add_token(f"{tag}_open", tag, 1)

    def depart_entry(self, node):
        tag = "th" if self.parent_tokens.get("thead") else "td"
        self.add_token(f"{tag}_close", tag, -1)

    # TODO check if handling of is/subId required for footnotes

    def visit_footnote(self, node, refname=None):
        refname = refname or node["ids"][0]  # assume there is only one id
        self.add_token("footnote_block_open", "", 1)
        self.add_token("footnote_open", "", 1, meta={"label": refname, "id": 0})

    def depart_footnote(self, node):
        self.add_token("footnote_close", "", -1)
        self.add_token("footnote_block_close", "", -1)

    def visit_citation(self, node):
        # treated same as for visit_footnote, but with specific prefix
        # TODO fails if duplicate refname, since names is empty
        refname = node["names"][0]  # assume there is only one name
        refname = f"{self.cite_prefix}{refname}"
        return self.visit_footnote(node, refname=refname)

    def depart_citation(self, node):
        # treated same as for depart_footnote
        return self.depart_footnote(node)

    def visit_footnote_reference(self, node):
        if "refname" in node:
            refname = node["refname"]
        elif "refid" in node:
            refname = node["refid"]
        else:
            message = f"unknown footnote reference type: {node.rawsource}"
            self.warning(message)
            if self.raise_on_error:
                raise NotImplementedError(message)

        self.add_token(
            "footnote_ref", "", 0, meta={"label": refname, "id": 0, "subId": 0}
        )

        raise nodes.SkipNode

    def visit_citation_reference(self, node):
        refname = node["refname"] if "refname" in node else node["refid"]
        # for compatibility we treat citations the same as footnotes, with a prefix
        refname = f"{self.cite_prefix}{refname}"
        self.add_token(
            "footnote_ref", "", 0, meta={"label": refname, "id": 0, "subId": 0}
        )
        # the node also contains the refname as text, but we don't need that
        raise nodes.SkipNode

    def visit_FrontMatterNode(self, node):
        for field in node:
            if not len(field) == 2:
                continue
            key = field[0][0].astext()
            if not field[1].children:
                value = True
            else:
                # TODO nested render
                value = field[1].astext()
            self._front_matter[key] = value
        raise nodes.SkipNode

    # MyST Markdown specific

    def visit_RoleNode(self, node):
        # TODO nested parse of specific roles
        role = node["role"] or self.default_role
        if role:
            self.add_token(
                "myst_role", "", 0, meta={"name": role}, content=node["text"]
            )
        else:
            self.add_token("code_inline", "code", 0, markup="`", content=node["text"])
        raise nodes.SkipNode

    def visit_comment(self, node):
        # TODO alternately use <!-- -->
        self.add_token(
            "myst_line_comment",
            "hr",
            0,
            attrs={"class": "myst-line-comment"},
            content=indent(node.astext(), " "),
        )
        raise nodes.SkipNode

    def visit_substitution_reference(self, node):
        self.add_token("substitution_inline", "span", 0, content=node["refname"])
        # the node also contains the refname as text, but we don't need that
        raise nodes.SkipNode

    def visit_substitution_definition(self, node):
        if "names" not in node or not node["names"]:
            raise nodes.SkipNode
        key = node["names"][0]
        # substitution should always be a single directive
        # special cases: replace, date
        # TODO nested parse
        value = node.astext()
        self._front_matter.setdefault("substitutions", {})[key] = value
        raise nodes.SkipNode

    # TODO deflist, directive
    # TODO https://docutils.sourceforge.io/docs/user/rst/quickref.htm
    # line block, field list, option list
