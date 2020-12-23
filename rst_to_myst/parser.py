from io import StringIO
from typing import Tuple

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

from .inliner import InlinerMyst
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


def to_ast(
    text: str, uri: str = "source", report_level=2, halt_level=4, warning_stream=None
) -> Tuple[nodes.document, StringIO]:
    settings = OptionParser(components=(RSTParser,)).get_default_values()
    warning_stream = StringIO() if warning_stream is None else warning_stream
    settings.warning_stream = warning_stream
    settings.report_level = report_level  # 2=warning
    settings.halt_level = halt_level  # 4=severe
    # The level at or above which `SystemMessage` exceptions
    # will be raised, halting execution.

    document = new_document(uri, settings=settings)

    parser = RSTParser()
    parser.parse(text, document)

    # these three transforms are required for converting targets correctly
    for transform_cls in [
        PropagateTargets,  # Propagate empty internal targets to the next element. (260)
        AnonymousHyperlinks,  # Link anonymous references to targets. (440)
        IndirectHyperlinks,  # "refuri" migrated back to all indirect targets (460)
        Footnotes,  # Assign numbers to autonumbered footnotes (620)
        StripFootnoteLabel,
        ResolveListItems,
    ]:
        transform = transform_cls(document)
        transform.apply()

    return document, warning_stream
