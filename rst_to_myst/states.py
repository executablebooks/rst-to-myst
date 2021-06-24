"""docutils states."""
import re
from typing import List, Optional

from docutils import nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.parsers.rst import Directive, states, tableparser
from docutils.utils import (
    BadOptionDataError,
    BadOptionError,
    escape2null,
    extract_options,
)

from .nodes import ArgumentNode, ContentNode, DirectiveNode, EvalRstNode

# Alphanumerics with isolated internal [-._+:] chars (i.e. not 2 together):
SIMPLENAME_RE = r"(?:(?!_)\w)+(?:[-._+:](?:(?!_)\w)+)*"


def get_state_classes():
    # state classes are parsed to the StateMachine class
    # and convert to a dict, with keys denoted by the class names
    # therefore sub-classes, must be named the same as their parent.
    return (
        Body,
        states.BulletList,
        states.DefinitionList,
        states.EnumeratedList,
        states.FieldList,
        states.OptionList,
        states.LineBlock,
        states.ExtensionOptions,
        Explicit,
        Text,
        states.Definition,
        Line,
        SubstitutionDef,
    )


class SectionMixin:
    def new_subsection(self, title, lineno, messages):
        """Append new subsection to document tree. On return, check level.

        Adds "level" attribute to title node
        """
        memo = self.memo
        mylevel = memo.section_level
        memo.section_level += 1
        section_node = nodes.section()
        self.parent += section_node
        textnodes, title_messages = self.inline_text(title, lineno)
        titlenode = nodes.title(title, "", *textnodes, level=memo.section_level)
        name = normalize_name(titlenode.astext())
        section_node["names"].append(name)
        section_node += titlenode
        section_node += messages
        section_node += title_messages
        self.document.note_implicit_target(section_node, section_node)
        offset = self.state_machine.line_offset + 1
        absoffset = self.state_machine.abs_line_offset() + 1
        newabsoffset = self.nested_parse(
            self.state_machine.input_lines[offset:],
            input_offset=absoffset,
            node=section_node,
            match_titles=True,
        )
        self.goto_line(newabsoffset)
        if memo.section_level <= mylevel:  # can't handle next section?
            raise EOFError  # bubble up to supersection
        # reset section_level; next pass will detect it properly
        memo.section_level = mylevel


class ExplicitMixin:
    def explicit_construct(self, match):
        """Determine which explicit construct this is, parse & return it.

        Overrides "directive" and "substitution_def" methods
        """
        errors = []
        for method, pattern in self.explicit.constructs:
            expmatch = pattern.match(match.string)
            if expmatch:
                try:
                    if method.__name__ == "directive":
                        return self.directive(expmatch)
                    elif method.__name__ == "substitution_def":
                        return self.substitution_def(expmatch)
                    else:
                        return method(self, expmatch)
                except states.MarkupError as error:
                    lineno = self.state_machine.abs_line_number()
                    message = " ".join(error.args)
                    errors.append(self.reporter.warning(message, line=lineno))
                    break
        nodelist, blank_finish = self.comment(match)
        return nodelist + errors, blank_finish

    def directive(self, match, **option_presets):
        """Returns a 2-tuple: list of nodes, and a "blank finish" boolean."""
        type_name = match.group(1)

        (
            block_text,
            indented,
            indent,
            lineno,
            line_offset,
            blank_finish,
        ) = self.parse_directive_match(match)

        # try to get directive class
        # directive_class, messages = directives.directive(
        #     type_name, self.memo.language, self.document
        # )
        directive_class: Optional[
            Directive
        ] = self.document.settings.namespace.get_directive(type_name)

        # default to eval rst
        if directive_class is None:
            # TODO warning message?
            return self.eval_rst(type_name, block_text, indent, indented, blank_finish)

        # get directive path for lookup
        directive_path = f"{directive_class.__module__}.{directive_class.__name__}"

        # lookup directive path
        conversion = self.document.settings.directive_data.get(directive_path, None)

        if conversion not in [
            "direct",
            "parse_argument",
            "parse_content",
            "parse_content_titles",
            "parse_all",
        ]:
            if conversion and conversion != "eval_rst":
                self.reporter.warning(
                    f'Unknown conversion type "{conversion}"',
                    nodes.literal_block(block_text, block_text),
                    line=lineno,
                )
            return self.eval_rst(type_name, block_text, indent, indented, blank_finish)

        try:
            (
                arg_block,
                options_list,
                content,
                content_offset,
            ) = self.parse_directive_block(indented, line_offset, directive_class)
        except states.MarkupError as error:
            self.reporter.warning(
                f'Error in "{type_name}" directive parse:\n{" ".join(error.args)}',
                nodes.literal_block(block_text, block_text),
                line=lineno,
            )
            return self.eval_rst(type_name, block_text, indent, indented, blank_finish)

        directive_node = DirectiveNode(
            block_text,
            name=type_name,
            module=directive_path,
            conversion=conversion,
            options_list=options_list,
        )

        if directive_class.required_arguments or directive_class.optional_arguments:
            argument_node = ArgumentNode()
            directive_node += argument_node
            if conversion in ("parse_argument", "parse_all"):
                textnodes, messages = self.inline_text(" ".join(arg_block), lineno)
                # TODO report messages?
                argument_node.extend(textnodes)
            else:
                argument_node += nodes.Text(" ".join(arg_block))

        if directive_class.has_content:
            content_node = ContentNode()
            directive_node += content_node
            if conversion in ("parse_content", "parse_content_titles", "parse_all"):
                self.nested_parse(
                    content,
                    content_offset,
                    content_node,
                    match_titles="titles" in conversion,
                )
            else:
                content_node += nodes.Text("\n".join(content or []))

        return [directive_node], blank_finish

    @staticmethod
    def eval_rst(
        name: str, block_text: str, indent: int, indented: List[str], blank_finish: bool
    ):
        """Return an EvalRstNode."""
        node = EvalRstNode(block_text, name=name, indent=indent)
        if not block_text.startswith(".. "):
            # substitution definition directives
            block_text = ".. " + block_text
        node += nodes.Text(block_text)
        return [node], blank_finish

    def parse_directive_match(self, match):
        lineno = self.state_machine.abs_line_number()
        initial_line_offset = self.state_machine.line_offset
        (
            indented,
            indent,
            line_offset,
            blank_finish,
        ) = self.state_machine.get_first_known_indented(match.end(), strip_top=0)
        block_text = "\n".join(
            self.state_machine.input_lines[
                initial_line_offset : self.state_machine.line_offset + 1
            ]
        )

        blank_finish = blank_finish or self.state_machine.is_next_line_blank()

        return block_text, indented, indent, lineno, line_offset, blank_finish

    def parse_directive_block(self, indented, line_offset, directive):

        if indented and not indented[0].strip():
            indented.trim_start()
            line_offset += 1

        while indented and not indented[-1].strip():
            indented.trim_end()

        if indented and (
            directive.required_arguments
            or directive.optional_arguments
            or directive.option_spec
        ):
            for i, line in enumerate(indented):  # noqa: B007
                if not line.strip():
                    break
            else:
                i += 1

            arg_block = indented[:i]
            content = indented[i + 1 :]
            content_offset = line_offset + i + 1
        else:
            content = indented
            content_offset = line_offset
            arg_block = []

        if directive.option_spec:
            option_list, arg_block = self.parse_directive_arg_block(arg_block)
        else:
            option_list = []

        if arg_block and not (
            directive.required_arguments or directive.optional_arguments
        ):
            content = arg_block + indented[i:]
            content_offset = line_offset
            arg_block = []

        while content and not content[0].strip():
            content.trim_start()
            content_offset += 1

        # TODO warning?
        # if content and not directive.has_content:
        #     raise MarkupError("no content permitted")

        return (arg_block, option_list, content, content_offset)

    def parse_directive_arg_block(self, arg_block):
        """Split arg block into arg and options list."""

        for i, line in enumerate(arg_block):
            if re.match(Body.patterns["field_marker"], line):
                opt_block = arg_block[i:]
                arg_block = arg_block[:i]
                break
        else:
            opt_block = []

        if not opt_block:
            return [], arg_block

        field_list = nodes.field_list()
        newline_offset, blank_finish = self.nested_list_parse(
            opt_block,
            0,
            field_list,
            initial_state="ExtensionOptions",
            blank_finish=True,
        )
        if newline_offset != len(opt_block):  # incomplete parse of block
            raise states.MarkupError("invalid option block")

        try:
            option_list = extract_options(field_list)
        except (BadOptionError, BadOptionDataError) as error:
            raise states.MarkupError(str(error))

        return option_list, arg_block

    def substitution_def(self, match):
        pattern = self.explicit.patterns.substitution
        src, srcline = self.state_machine.get_source_and_line()
        (
            block,
            indent,
            offset,
            blank_finish,
        ) = self.state_machine.get_first_known_indented(match.end(), strip_indent=False)
        blocktext = match.string[: match.end()] + "\n".join(block)
        block.disconnect()
        escaped = escape2null(block[0].rstrip())
        blockindex = 0
        while True:
            subdefmatch = pattern.match(escaped)
            if subdefmatch:
                break
            blockindex += 1
            try:
                escaped = escaped + " " + escape2null(block[blockindex].strip())
            except IndexError:
                raise states.MarkupError("malformed substitution definition.")
        del block[:blockindex]  # strip out the substitution marker
        block[0] = (block[0].strip() + " ")[subdefmatch.end() - len(escaped) - 1 : -1]
        if not block[0]:
            del block[0]
            offset += 1
        while block and not block[-1].strip():
            block.pop()
        subname = subdefmatch.group("name")
        substitution_node = nodes.substitution_definition(blocktext)
        substitution_node.source = src
        substitution_node.line = srcline
        if not block:
            raise states.MarkupError(
                f'Substitution definition "{subname}" missing contents: {src}:{srcline}'
            )
        block[0] = block[0].strip()
        substitution_node["names"].append(nodes.whitespace_normalize_name(subname))
        new_abs_offset, blank_finish = self.nested_list_parse(
            block,
            input_offset=offset,
            node=substitution_node,
            initial_state="SubstitutionDef",
            blank_finish=blank_finish,
            state_machine_kwargs={"state_classes": get_state_classes()},
        )

        return [substitution_node], blank_finish

    def table(self, isolate_function, parser_class):
        """Parse a table, and record the raw text."""
        block, messages, blank_finish = isolate_function()
        if block:
            try:
                parser = parser_class()
                tabledata = parser.parse(block)
                tableline = self.state_machine.abs_line_number() - len(block) + 1
                table = self.build_table(tabledata, tableline)  # type: nodes.table
                table.rawsource = "\n".join(block)  # added for MyST
                nodelist = [table] + messages
            except tableparser.TableMarkupError as err:
                nodelist = (
                    self.malformed_table(block, " ".join(err.args), offset=err.offset)
                    + messages
                )
        else:
            nodelist = messages
        return nodelist, blank_finish


class Body(SectionMixin, ExplicitMixin, states.Body):
    def __init__(self, state_machine, debug=False):
        super().__init__(state_machine, debug=debug)
        self.nested_sm_kwargs = {
            "state_classes": get_state_classes(),
            "initial_state": "Body",
        }

    def field_marker(self, match, context, next_state):
        """Field list item.

        Modified to store full text of field_list in ``rawsource``
        """
        field_list = nodes.field_list()
        self.parent += field_list
        field, blank_finish = self.field(match)
        field_list += field
        offset = self.state_machine.line_offset + 1  # next line
        newline_offset, blank_finish = self.nested_list_parse(
            self.state_machine.input_lines[offset:],
            input_offset=self.state_machine.abs_line_offset() + 1,
            node=field_list,
            initial_state="FieldList",
            blank_finish=blank_finish,
        )
        self.goto_line(newline_offset)
        # TODO this slicing of input_lines seems to work, but I'm not exactly sure why
        field_list.rawsource += "\n".join(
            self.state_machine.input_lines[
                offset - 1 : offset + (newline_offset - field.line)
            ]
        )
        if not blank_finish:
            self.parent += self.unindent_warning("Field list")
        return [], next_state, []


class Explicit(ExplicitMixin, states.Explicit):
    def __init__(self, state_machine, debug=False):
        super().__init__(state_machine, debug=debug)
        self.nested_sm_kwargs = {
            "state_classes": get_state_classes(),
            "initial_state": "Body",
        }


class Line(SectionMixin, states.Line):
    def __init__(self, state_machine, debug=False):
        super().__init__(state_machine, debug=debug)
        self.nested_sm_kwargs = {
            "state_classes": get_state_classes(),
            "initial_state": "Body",
        }


class Text(SectionMixin, states.Text):
    def __init__(self, state_machine, debug=False):
        super().__init__(state_machine, debug=debug)
        self.nested_sm_kwargs = {
            "state_classes": get_state_classes(),
            "initial_state": "Body",
        }


class SubstitutionDef(Body):
    """
    Parser for the contents of a substitution_definition element.
    """

    patterns = {
        "embedded_directive": re.compile(r"(%s)::( +|$)" % SIMPLENAME_RE, re.UNICODE),
        "text": r"",
    }
    initial_transitions = ["embedded_directive", "text"]

    def embedded_directive(self, match, context, next_state):
        nodelist, blank_finish = self.directive(match, alt=self.parent["names"][0])
        self.parent += nodelist
        if not self.state_machine.at_eof():
            self.blank_finish = blank_finish
        raise EOFError

    def text(self, match, context, next_state):
        if not self.state_machine.at_eof():
            self.blank_finish = self.state_machine.is_next_line_blank()
        raise EOFError
