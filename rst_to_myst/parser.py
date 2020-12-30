from io import StringIO
from typing import Tuple

import yaml
from docutils import nodes
from docutils.frontend import OptionParser
from docutils.parsers.rst import Parser
from docutils.transforms import Transform
from docutils.transforms.references import (
    AnonymousHyperlinks,
    Footnotes,
    PropagateTargets,
)
from docutils.utils import new_document, roman
from importlib_resources import files

from . import data as package_data
from .inliner import InlinerMyst
from .namespace import compile_namespace
from .nodes import DirectiveNode, FrontMatterNode
from .states import get_state_classes


class RSTParser(Parser):
    def __init__(self):
        self.initial_state = "Body"
        self.state_classes = get_state_classes()
        for state_class in self.state_classes:
            # flush any cached states from the last parse
            state_class.nested_sm_cache = []
        self.inliner = InlinerMyst()


class IndirectHyperlinks(Transform):
    def apply(self):
        for target in self.document.indirect_targets:
            if not target.resolved:
                self.resolve_indirect_target(target)
            # Do not resolve the actual references, since this replaces the "refname"
            # self.resolve_indirect_references(target)


class StripFootnoteLabel(Transform):
    # footnotes and citations can start with a label note, which we do not need
    def apply(self):
        for node in self.document.traverse(
            lambda n: isinstance(n, (nodes.footnote, nodes.citation))
        ):
            if node.children and isinstance(node.children[0], nodes.label):
                node.pop(0)


ENUM_CONVERTERS = {
    "arabic": (lambda i: i),
    "lowerroman": (lambda i: roman.toRoman(i).lower()),
    "upperroman": (lambda i: roman.toRoman(i).upper()),
    "loweralpha": (lambda i: chr(ord("a") + i - 1)),
    "upperalpha": (lambda i: chr(ord("a") + i - 1).upper()),
}


class ResolveListItems(Transform):
    def apply(self):
        for node in self.document.traverse(nodes.bullet_list):
            prefix = node["bullet"] + " "
            for child in node.children:
                if isinstance(child, nodes.list_item):
                    child["style"] = "bullet"
                    child["prefix"] = prefix
        for node in self.document.traverse(nodes.enumerated_list):
            number = 1
            if "start" in node:
                number = node["start"]
            # TODO markdown-it only supports numbers
            # prefix = node["prefix"]
            # suffix = node["suffix"]
            # convert = ENUM_CONVERTERS[node["enumtype"]]
            for child in node.children:
                if isinstance(child, nodes.list_item):
                    child["style"] = "enumerated"
                    child["prefix"] = f"{number}. "
                    number += 1


class DirectiveNesting(Transform):
    def apply(self):
        for node in self.document.traverse(DirectiveNode):  # type: DirectiveNode
            # TODO this will overcount if multiple directives at same nesting depth
            node["delimiter"] *= (
                3
                + sum(1 for _ in node.traverse(DirectiveNode, include_self=False))
                # add an extra delimiter if the directive contains a table,
                # because we wrap some in eval_rst directive
                + (1 if sum(1 for _ in node.traverse(nodes.table)) else 0)
            )


class FrontMatter(Transform):
    def apply(self):
        if not self.document.settings.front_matter:
            return
        index = self.document.first_child_not_matching_class(nodes.PreBibliographic)
        if index is None:
            return
        candidate = self.document[index]
        if isinstance(candidate, nodes.field_list):
            front_matter = FrontMatterNode("", *candidate.children)
            self.document[index] = front_matter


def to_ast(
    text: str,
    uri: str = "source",
    report_level=2,
    halt_level=4,
    warning_stream=None,
    language_code="en",
    use_sphinx=True,
    extensions=(),
    default_domain="py",
    conversions=None,
    front_matter=True,
) -> Tuple[nodes.document, StringIO]:
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    warning_stream = StringIO() if warning_stream is None else warning_stream
    settings.warning_stream = warning_stream
    settings.report_level = report_level  # 2=warning
    settings.halt_level = halt_level  # 4=severe
    # The level at or above which `SystemMessage` exceptions
    # will be raised, halting execution.
    settings.language_code = language_code

    document = new_document(uri, settings=settings)

    # compile lookup for directives/roles
    namespace = compile_namespace(
        language_code=language_code,
        use_sphinx=use_sphinx,
        extensions=extensions,
        default_domain=default_domain,
    )
    document.settings.namespace = namespace

    # get conversion lookup for directives
    directive_data = yaml.safe_load(
        files(package_data).joinpath("directives.yml").read_text("utf8")
    )
    if conversions:
        directive_data.update(conversions)
    document.settings.directive_data = directive_data

    # whether to treat initial field list as front matter
    document.settings.front_matter = front_matter

    parser = RSTParser()
    parser.parse(text, document)

    # these three transforms are required for converting targets correctly
    for transform_cls in [
        PropagateTargets,  # Propagate empty internal targets to the next element. (260)
        FrontMatter,  # convert initial field list (DocInfo=340)
        AnonymousHyperlinks,  # Link anonymous references to targets. (440)
        IndirectHyperlinks,  # "refuri" migrated back to all indirect targets (460)
        Footnotes,  # Assign numbers to autonumbered footnotes (620)
        # bespoke transforms
        StripFootnoteLabel,
        ResolveListItems,
        DirectiveNesting,
    ]:
        transform = transform_cls(document)
        transform.apply()

    return document, warning_stream
