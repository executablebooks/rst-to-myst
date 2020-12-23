import re

from docutils import nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.parsers.rst import states
from docutils.utils import escape2null

from .nodes import DirectiveNode

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

        # lineno = self.state_machine.abs_line_number()
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

        return [
            DirectiveNode(
                block_text,
                name=type_name,
                indent=indent,
                indented=indented,
            )
        ], blank_finish

    def run_directive(self, *arg, **kwargs):
        raise NotImplementedError

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


class Body(SectionMixin, ExplicitMixin, states.Body):
    def __init__(self, state_machine, debug=False):
        super().__init__(state_machine, debug=debug)
        self.nested_sm_kwargs = {
            "state_classes": get_state_classes(),
            "initial_state": "Body",
        }


class Explicit(ExplicitMixin, states.Explicit):
    pass


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
