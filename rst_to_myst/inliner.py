"""This is a copy of the Inliner class found in docutils/docutils/parsers/rst/states.py
It has been 'updated', to make it (a) more readable, (b) easier to subclass, and
(c) more inline with python 3 syntax. Changes include:

- Removing class properties and calls to local()
- Replacing % string formatting with f-strings
- Extract a separate Regexes class to initialise and store compiled regexes
- Adding method documentation
- Adding type hinting

For inline syntax reference see:
See http://docutils.sourceforge.net/docs/user/rst/quickref.html

The key elements are:

--------------- --------------- --------------------------------------------------------
Type            Example
--------------- --------------- --------------------------------------------------------
emphasis        *emphasis* 	    Normally rendered as italics.
strong          **strong**      Normally rendered as bold.
interpreted     `interpreted`   Domain- or application-dependent. Can be
                                prefixed/suffixed by a role, e.g. :a:`b` or `b`:a:
                                Whitespace or punctuation is required around interpreted
inline literal  ``literal`` 	Normally rendered as monospaced text.
                                Spaces should be preserved, but line breaks will not be.
simple ref      reference_ 	    A simple, one-word hyperlink reference.
                                e.g. target: .. _reference: http://www.python.org/
phrase ref      `phrase`_ 	    A hyperlink reference, with spaces or punctuation,
                                needs to be quoted with backquotes.
embedded ref    `text <ref_>`_
anonymous ref   anonymous__ 	Both simple and phrase references may be anonymous
                                (the reference text is not repeated at the target).
                                e.g. target: .. __: anonymous
inline target   _`target` 	 	A cross-reference target within text.
sub ref         |sub| 	        e.g. target: .. |sub| image:: myimage.png
                                Substitution can be text, an image, a hyperlink,
                                or a combination of these and others.
footnote ref    [1]_,[#]_,[*]_  e.g. target: .. [5] A numerical footnote
citation ref    [CIT2002]_      e.g. target: .. [CIT2002] A citation
hyperlink uri   http://a.net/
embedded uri    `uri <a.org>`_
--------------- --------------- --------------------------------------------------------
"""
import re
from typing import Any, Callable, List, Match, Pattern, Tuple

from docutils import ApplicationError, nodes
from docutils.nodes import fully_normalize_name as normalize_name
from docutils.nodes import whitespace_normalize_name
from docutils.parsers.rst import roles
from docutils.utils import (
    Reporter,
    escape2null,
    get_trim_footnote_ref_space,
    punctuation_chars,
    split_escaped_whitespace,
    unescape,
    urischemes,
)

from .nodes import RoleNode


class MarkupMismatch(Exception):
    """A mismatch occurred in the Markup."""


def build_regexp(definition: Tuple[str, str, str, List], compile_regexp: bool = True):
    """Build, compile and return a regular expression based on `definition`.

    :param definition: a 4-tuple (group name, prefix, suffix, parts),
        where "parts" is a list of regular expressions and/or regular
        expression definitions to be joined into an or-group.
    """
    name, prefix, suffix, parts = definition
    part_strings = []
    for part in parts:
        if isinstance(part, (list, tuple)):
            part_strings.append(build_regexp(part, compile_regexp=False))
        else:
            part_strings.append(part)
    or_group = "|".join(part_strings)
    regexp = f"{prefix}(?P<{name}>{or_group}){suffix}"
    if compile_regexp:
        return re.compile(regexp, re.UNICODE)
    else:
        return regexp


class Regexes:
    """Initialise and store compiled regexes."""

    def __init__(self, start_string_prefix: str, end_string_suffix: str):

        # Define inline object recognitions
        # ---------------------------------
        non_whitespace_before = r"(?<!\s)"
        non_whitespace_escape_before = r"(?<![\s\x00])"
        non_unescaped_whitespace_escape_before = r"(?<!(?<!\x00)[\s\x00])"
        non_whitespace_after = r"(?!\s)"
        # Alphanumerics with isolated internal [-._+:] chars (i.e. not 2 together):
        simplename = r"(?:(?!_)\w)+(?:[-._+:](?:(?!_)\w)+)*"
        # Valid URI characters (see RFC 2396 & RFC 2732);
        # final \x00 allows backslash escapes in URIs:
        uric = r"""[-_.!~*'()[\];/:@&=+$,%a-zA-Z0-9\x00]"""
        # Delimiter indicating the end of a URI (not part of the URI):
        uri_end_delim = r"""[>]"""
        # Last URI character; same as uric but no punctuation:
        urilast = r"""[_~*/=+a-zA-Z0-9]"""
        # End of a URI (either 'urilast' or 'uric followed by a uri_end_delim'):
        uri_end = fr"""(?:{urilast}|{uric}(?={uri_end_delim}))"""
        emailc = r"""[-_!~*'{|}/#?^`&=+$%a-zA-Z0-9\x00]"""
        email_pattern = fr"""
                {emailc}+(?:\.{emailc}+)*       # name
                (?<!\x00)@                      # at
                {emailc}+(?:\.{emailc}*)*       # host
                {uri_end}                       # final URI char
                """

        # Create initial pattern, which matches start-strings
        # (emphasis, strong, interpreted, phrase reference, literal,
        # substitution reference, and inline target),
        # and complete constructs (simple reference, footnote reference)
        parts = (
            "initial_inline",
            start_string_prefix,
            "",
            [
                (
                    # simple start-strings
                    "start",
                    "",
                    non_whitespace_after,
                    [
                        r"\*\*",  # strong
                        r"\*(?!\*)",  # emphasis but not strong
                        r"``",  # literal
                        r"_`",  # inline internal target
                        r"\|(?!\|)",  # substitution reference
                    ],
                ),
                (
                    # whole constructs
                    "whole",
                    "",
                    end_string_suffix,
                    [
                        # reference name & end-string
                        fr"(?P<refname>{simplename})(?P<refend>__?)",
                        (
                            "footnotelabel",
                            r"\[",
                            r"(?P<fnend>\]_)",
                            [
                                r"[0-9]+",  # manually numbered
                                fr"\#({simplename})?",  # auto-numbered (w/ label?)
                                r"\*",  # auto-symbol
                                fr"(?P<citationlabel>{simplename})",
                            ],  # citation reference
                        ),
                    ],
                ),
                (
                    # interpreted text or phrase reference
                    "backquote",
                    f"(?P<role>(:{simplename}:)?)",  # optional role
                    non_whitespace_after,
                    ["`(?!`)"],  # but not literal
                ),
            ],
        )
        self.initial = build_regexp(parts)

        self.emphasis = re.compile(
            non_whitespace_escape_before + r"(\*)" + end_string_suffix, re.UNICODE
        )

        self.strong = re.compile(
            non_whitespace_escape_before + r"(\*\*)" + end_string_suffix, re.UNICODE
        )

        self.interpreted_or_phrase_ref = re.compile(
            fr"""
            {non_unescaped_whitespace_escape_before}
            (
            `
            (?P<suffix>
                (?P<role>:{simplename}:)?
                (?P<refend>__?)?
            )
            )
            {end_string_suffix}
            """,
            re.VERBOSE | re.UNICODE,
        )

        self.embedded_link = re.compile(
            fr"""
            (
            (?:[ \n]+|^)            # spaces or beginning of line/string
            <                       # open bracket
            {non_whitespace_after}
            (([^<>]|\x00[<>])+)     # anything but unescaped angle brackets
            {non_whitespace_escape_before}
            >                       # close bracket
            )
            $                         # end of string
            """,
            re.VERBOSE | re.UNICODE,
        )

        self.literal = re.compile(
            non_whitespace_before + "(``)" + end_string_suffix, re.UNICODE
        )

        self.target = re.compile(
            non_whitespace_escape_before + r"(`)" + end_string_suffix, re.UNICODE
        )

        self.substitution_ref = re.compile(
            non_whitespace_escape_before + r"(\|_{0,2})" + end_string_suffix, re.UNICODE
        )
        self.email = re.compile(email_pattern + "$", re.VERBOSE | re.UNICODE)

        self.uri = re.compile(
            (
                fr"""
            {start_string_prefix}
            (?P<whole>
                (?P<absolute>           # absolute URI
                (?P<scheme>             # scheme (http, ftp, mailto)
                    [a-zA-Z][a-zA-Z0-9.+-]*
                )
                :
                (
                    (                     # either:
                    (//?)?                # hierarchical URI
                    {uric}*               # URI characters
                    {uri_end}             # final URI char
                    )
                    (                     # optional query
                    \?{uric}*
                    {uri_end}
                    )?
                    (                    # optional fragment
                    \#{uric}*
                    {uri_end}
                    )?
                )
                )
            |                           # *OR*
                (?P<email>              # email address
                """
                + email_pattern
                + fr"""
                )
            )
            {end_string_suffix}
            """
            ),
            re.VERBOSE | re.UNICODE,
        )

        self.pep = re.compile(
            fr"""
            {start_string_prefix}
            (
                (pep-(?P<pepnum1>\d+)(.txt)?) # reference to source file
            |
                (PEP\s+(?P<pepnum2>\d+))      # reference by name
            )
            {end_string_suffix}""",
            re.VERBOSE | re.UNICODE,
        )

        self.rfc = re.compile(
            fr"""
            {start_string_prefix}
            (RFC(-|\s+)?(?P<rfcnum>\d+))
            {end_string_suffix}""",
            re.VERBOSE | re.UNICODE,
        )


DispatchResult = Tuple[str, List[nodes.Node], str, List[nodes.system_message]]
ImplicitResult = List[nodes.Node]


class Inliner:
    """Class for parsing inline markup.

    To use::

        inliner = Inliner()
        inliner.init_customizations(document.settings)
        inliner.parse(text, lineno, memo, parent)

    """

    def __init__(self, regex_class=None):
        """Initialise inliner."""
        # list of (pattern, bound method) tuples, used by `self.implicit_inline`.
        self.implicit_dispatch = []  # type: List[Tuple[Pattern, Callable]]
        self.regex_class = regex_class or Regexes
        # this is required by ``rfc_reference_role()``
        self.rfc_url = "rfc%d.html"

    def init_customizations(self, settings):
        """Initialise lookahead and look-behind expressions for inline markup rules.

        ``settings`` is document settings, whereby the following attributes are used:

        - settings.character_level_inline_markup (boolean);
          Inline markup recognized anywhere, regardless of surrounding characters.
          (Useful for East Asian languages, experimental)
        - settings.pep_references (boolean); handle PEP references
        - settings.rfc_references (boolean); handle RFC references

        """
        if getattr(settings, "character_level_inline_markup", False):
            start_string_prefix = "(^|(?<!\x00))"
            end_string_suffix = ""
        else:
            start_string_prefix = "(^|(?<=\\s|[%s%s]))" % (
                punctuation_chars.openers,
                punctuation_chars.delimiters,
            )
            end_string_suffix = "($|(?=\\s|[\x00%s%s%s]))" % (
                punctuation_chars.closing_delimiters,
                punctuation_chars.delimiters,
                punctuation_chars.closers,
            )

        self.patterns = self.regex_class(
            start_string_prefix=start_string_prefix, end_string_suffix=end_string_suffix
        )

        self.implicit_dispatch.append((self.patterns.uri, self.standalone_uri))
        if settings.pep_references:
            self.implicit_dispatch.append((self.patterns.pep, self.pep_reference))
        if settings.rfc_references:
            self.implicit_dispatch.append((self.patterns.rfc, self.rfc_reference))

    @property
    def dispatch_methods(self):
        """Maps start/end characters of inline syntax to their method handles."""
        return {
            "*": self.emphasis,
            "**": self.strong,
            "`": self.interpreted_or_phrase_ref,
            "``": self.literal,
            "_`": self.inline_internal_target,
            "]_": self.footnote_reference,
            "|": self.substitution_reference,
            "_": self.reference,
            "__": self.anonymous_reference,
        }

    def parse(
        self, text: str, lineno: int, memo: Any, parent: Any
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """
        Return 2 lists: nodes (text and inline elements), and system_messages.

        1. Using `self.patterns.initial`, a pattern which matches start-strings
           (emphasis, strong, interpreted, phrase reference, literal,
           substitution reference, and inline target) and complete constructs
           (simple reference, footnote reference), search for a candidate.
        2. When one is found, check for validity (e.g., not a quoted '*' character).
        3. If valid, search for the corresponding end string if applicable, and
           check it for validity.
        4. If not found or invalid, generate a warning and ignore the start-string.
        5. Implicit inline markup (e.g. standalone URIs) is found last.
        """
        self.reporter = memo.reporter  # type: Reporter
        self.document = memo.document  # type: nodes.document
        self.language = memo.language
        self.parent = parent
        remaining = escape2null(text)
        processed = []
        unprocessed = []
        messages = []
        while remaining:
            match = self.patterns.initial.search(remaining)
            if match:
                groups = match.groupdict()
                method = self.dispatch_methods[
                    groups["start"]
                    or groups["backquote"]
                    or groups["refend"]
                    or groups["fnend"]
                ]
                before, inlines, remaining, sysmessages = method(match, lineno)
                unprocessed.append(before)
                messages += sysmessages
                if inlines:
                    processed += self.implicit_inline("".join(unprocessed), lineno)
                    processed += inlines
                    unprocessed = []
            else:
                break
        remaining = "".join(unprocessed) + remaining
        if remaining:
            processed += self.implicit_inline(remaining, lineno)
        return processed, messages

    def quoted_start(self, match: Match) -> bool:
        """Test if inline markup start-string is 'quoted'.

        'Quoted' in this context means the start-string is enclosed in a pair
        of matching opening/closing delimiters (not necessarily quotes)
        or at the end of the match.
        """
        string = match.string
        start = match.start()
        if start == 0:  # start-string at beginning of text
            return False
        prestart = string[start - 1]
        try:
            poststart = string[match.end()]
        except IndexError:  # start-string at end of text
            return True  # not "quoted" but no markup start-string either
        return punctuation_chars.match_chars(prestart, poststart)

    def emphasis(self, match: Match, lineno: int) -> DispatchResult:
        """Handle *emphasis*"""
        before, inlines, remaining, sysmessages, endstring = self.inline_obj(
            match, lineno, self.patterns.emphasis, nodes.emphasis
        )
        return before, inlines, remaining, sysmessages

    def strong(self, match: Match, lineno: int) -> DispatchResult:
        """Handle **strong**"""
        before, inlines, remaining, sysmessages, endstring = self.inline_obj(
            match, lineno, self.patterns.strong, nodes.strong
        )
        return before, inlines, remaining, sysmessages

    def interpreted_or_phrase_ref(self, match: Match, lineno: int) -> DispatchResult:
        """Handle :role:`interpreted`, `interpreted`:role: or `phrase ref`_

        If interpreted, evoke ``self.interpreted``, or
        if phrase ref, evoke ``self.self.phrase_ref``
        """
        end_pattern = self.patterns.interpreted_or_phrase_ref
        string = match.string
        matchstart = match.start("backquote")
        matchend = match.end("backquote")
        rolestart = match.start("role")
        role = match.group("role")
        position = ""
        if role:
            role = role[1:-1]
            position = "prefix"
        elif self.quoted_start(match):
            return (string[:matchend], [], string[matchend:], [])
        endmatch = end_pattern.search(string[matchend:])
        if endmatch and endmatch.start(1):  # 1 or more chars
            textend = matchend + endmatch.end()
            if endmatch.group("role"):
                if role:
                    msg = self.reporter.warning(
                        "Multiple roles in interpreted text (both "
                        "prefix and suffix present; only one allowed).",
                        line=lineno,
                    )
                    text = unescape(string[rolestart:textend], True)
                    prb = self.problematic(text, text, msg)
                    return string[:rolestart], [prb], string[textend:], [msg]
                role = endmatch.group("suffix")[1:-1]
                position = "suffix"
            escaped = endmatch.string[: endmatch.start(1)]
            rawsource = unescape(string[matchstart:textend], True)
            if rawsource[-1:] == "_":
                if role:
                    msg = self.reporter.warning(
                        "Mismatch: both interpreted text role %s and "
                        "reference suffix." % position,
                        line=lineno,
                    )
                    text = unescape(string[rolestart:textend], True)
                    prb = self.problematic(text, text, msg)
                    return string[:rolestart], [prb], string[textend:], [msg]
                return self.phrase_ref(
                    string[:matchstart],
                    string[textend:],
                    rawsource,
                    escaped,
                    unescape(escaped),
                )
            else:
                rawsource = unescape(string[rolestart:textend], True)
                nodelist, messages = self.interpreted(rawsource, escaped, role, lineno)
                return (string[:rolestart], nodelist, string[textend:], messages)
        msg = self.reporter.warning(
            "Inline interpreted text or phrase reference start-string "
            "without end-string.",
            line=lineno,
        )
        text = unescape(string[matchstart:matchend], True)
        prb = self.problematic(text, text, msg)
        return string[:matchstart], [prb], string[matchend:], [msg]

    def phrase_ref(
        self, before: str, after: str, rawsource: str, escaped: str, text: str
    ) -> DispatchResult:
        """Handle phrase references e.g. `phrase ref`_, `embedded <ref_>`_"""
        match = self.patterns.embedded_link.search(escaped)
        if match:  # embedded <URI> or <alias_>
            text = unescape(escaped[: match.start(0)])
            rawtext = unescape(escaped[: match.start(0)], True)
            aliastext = unescape(match.group(2))
            rawaliastext = unescape(match.group(2), True)
            underscore_escaped = rawaliastext.endswith(r"\_")
            if aliastext.endswith("_") and not (
                underscore_escaped or self.patterns.uri.match(aliastext)
            ):
                aliastype = "name"
                alias = normalize_name(aliastext[:-1])
                target = nodes.target(match.group(1), refname=alias)
                target.indirect_reference_name = aliastext[:-1]
            else:
                aliastype = "uri"
                alias_parts = split_escaped_whitespace(match.group(2))
                alias = " ".join(
                    "".join(unescape(part).split()) for part in alias_parts
                )
                alias = self.adjust_uri(alias)
                if alias.endswith(r"\_"):
                    alias = alias[:-2] + "_"
                target = nodes.target(match.group(1), refuri=alias)
                target.referenced = 1
            if not aliastext:
                raise ApplicationError("problem with embedded link: %r" % aliastext)
            if not text:
                text = alias
                rawtext = rawaliastext
        else:
            target = None
            rawtext = unescape(escaped, True)

        refname = normalize_name(text)
        reference = nodes.reference(
            rawsource, text, name=whitespace_normalize_name(text)
        )
        reference[0].rawsource = rawtext

        node_list = [reference]

        if rawsource[-2:] == "__":
            if target and (aliastype == "name"):
                reference["refname"] = alias
                self.document.note_refname(reference)
                # self.document.note_indirect_target(target) # required?
            elif target and (aliastype == "uri"):
                reference["refuri"] = alias
            else:
                reference["anonymous"] = 1
        else:
            if target:
                target["names"].append(refname)
                if aliastype == "name":
                    reference["refname"] = alias
                    self.document.note_indirect_target(target)
                    self.document.note_refname(reference)
                else:
                    reference["refuri"] = alias
                    self.document.note_explicit_target(target, self.parent)
                # target.note_referenced_by(name=refname)
                node_list.append(target)
            else:
                reference["refname"] = refname
                self.document.note_refname(reference)
        return before, node_list, after, []

    def adjust_uri(self, uri: str) -> str:
        """Append `mailto:` to email address uri's"""
        match = self.patterns.email.match(uri)
        if match:
            return "mailto:" + uri
        else:
            return uri

    def interpreted(
        self, rawsource: str, text: str, role: str, lineno: int
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Handle an interpreted text role, e.g. :role:interpreted` or `interpreted`:role:

        The role function is located and returned, then used to create the requisite
        nodes and messages.

        """
        role_fn, messages = roles.role(role, self.language, lineno, self.reporter)
        if role_fn:
            nodes, messages2 = role_fn(role, rawsource, text, lineno, self)
            try:
                nodes[0][0].rawsource = unescape(text, True)
            except IndexError:
                pass
            return nodes, messages + messages2
        else:
            msg = self.reporter.error(
                'Unknown interpreted text role "%s".' % role, line=lineno
            )
            return ([self.problematic(rawsource, rawsource, msg)], messages + [msg])

    def literal(self, match: Match, lineno: int) -> DispatchResult:
        """Handle a string literal, e.g. ``literals``"""
        before, inlines, remaining, sysmessages, endstring = self.inline_obj(
            match,
            lineno,
            self.patterns.literal,
            nodes.literal,
            restore_backslashes=True,
        )
        return before, inlines, remaining, sysmessages

    def inline_internal_target(self, match: Match, lineno: int) -> DispatchResult:
        """Handle an inline internal target, e.g. _`target`"""
        before, inlines, remaining, sysmessages, endstring = self.inline_obj(
            match, lineno, self.patterns.target, nodes.target
        )
        if inlines and isinstance(inlines[0], nodes.target):
            assert len(inlines) == 1
            target = inlines[0]
            name = normalize_name(target.astext())
            target["names"].append(name)
            target["inline"] = True  # myst addition
            self.document.note_explicit_target(target, self.parent)
        return before, inlines, remaining, sysmessages

    def substitution_reference(self, match: Match, lineno: int) -> DispatchResult:
        """Handle a substitution reference, e.g. |sub|"""
        before, inlines, remaining, sysmessages, endstring = self.inline_obj(
            match, lineno, self.patterns.substitution_ref, nodes.substitution_reference
        )
        if len(inlines) == 1:
            subref_node = inlines[0]
            if isinstance(subref_node, nodes.substitution_reference):
                subref_text = subref_node.astext()
                self.document.note_substitution_ref(subref_node, subref_text)
                if endstring[-1:] == "_":
                    reference_node = nodes.reference(
                        "|%s%s" % (subref_text, endstring), ""
                    )
                    if endstring[-2:] == "__":
                        reference_node["anonymous"] = 1
                    else:
                        reference_node["refname"] = normalize_name(subref_text)
                        self.document.note_refname(reference_node)
                    reference_node += subref_node
                    inlines = [reference_node]
        return before, inlines, remaining, sysmessages

    def footnote_reference(self, match: Match, lineno: int) -> DispatchResult:
        """Handles footnote/citation references, e.g. [1]_"""
        label = match.group("footnotelabel")
        refname = normalize_name(label)
        string = match.string
        before = string[: match.start("whole")]
        remaining = string[match.end("whole") :]
        if match.group("citationlabel"):
            refnode = nodes.citation_reference(f"[{label}]_", refname=refname)
            refnode += nodes.Text(label)
            self.document.note_citation_ref(refnode)
        else:
            refnode = nodes.footnote_reference(f"[{label}]_")
            if refname[0] == "#":
                refname = refname[1:]
                refnode["auto"] = 1
                self.document.note_autofootnote_ref(refnode)
            elif refname == "*":
                refname = ""
                refnode["auto"] = "*"
                self.document.note_symbol_footnote_ref(refnode)
            else:
                refnode += nodes.Text(label)
            if refname:
                refnode["refname"] = refname
                self.document.note_footnote_ref(refnode)
            if get_trim_footnote_ref_space(self.document.settings):
                before = before.rstrip()
        return (before, [refnode], remaining, [])

    def reference(
        self, match: Match, lineno: int, anonymous: bool = False
    ) -> DispatchResult:
        """Handle simple references,  e.g. reference_ and anonymous__"""
        referencename = match.group("refname")
        refname = normalize_name(referencename)
        referencenode = nodes.reference(
            referencename + match.group("refend"),
            referencename,
            name=whitespace_normalize_name(referencename),
        )
        referencenode[0].rawsource = referencename
        if anonymous:
            referencenode["anonymous"] = 1
        else:
            referencenode["refname"] = refname
            self.document.note_refname(referencenode)
        string = match.string
        matchstart = match.start("whole")
        matchend = match.end("whole")
        return (string[:matchstart], [referencenode], string[matchend:], [])

    def anonymous_reference(self, match: Match, lineno: int) -> DispatchResult:
        """Handle anonymous references, e.g. anonymous__"""
        return self.reference(match, lineno, anonymous=True)

    def inline_obj(
        self,
        match: Match,
        lineno: int,
        end_pattern: Pattern,
        nodeclass: nodes.TextElement,
        restore_backslashes: bool = False,
    ):
        """Create the node for an inline class, if the end string match can be found."""
        string = match.string
        matchstart = match.start("start")
        matchend = match.end("start")
        if self.quoted_start(match):
            return (string[:matchend], [], string[matchend:], [], "")
        endmatch = end_pattern.search(string[matchend:])
        if endmatch and endmatch.start(1):  # 1 or more chars
            _text = endmatch.string[: endmatch.start(1)]
            text = unescape(_text, restore_backslashes)
            textend = matchend + endmatch.end(1)
            rawsource = unescape(string[matchstart:textend], True)
            node = nodeclass(rawsource, text)
            node[0].rawsource = unescape(_text, True)
            return (
                string[:matchstart],
                [node],
                string[textend:],
                [],
                endmatch.group(1),
            )
        msg = self.reporter.warning(
            "Inline %s start-string without end-string." % nodeclass.__name__,
            line=lineno,
        )
        text = unescape(string[matchstart:matchend], True)
        rawsource = unescape(string[matchstart:matchend], True)
        prb = self.problematic(text, rawsource, msg)
        return string[:matchstart], [prb], string[matchend:], [msg], ""

    def problematic(
        self, text: str, rawsource: str, message: nodes.system_message
    ) -> nodes.problematic:
        """Create a 'problematic' node, if a syntax issue has been encountered."""
        msgid = self.document.set_id(message, self.parent)
        problematic = nodes.problematic(rawsource, text, refid=msgid)
        prbid = self.document.set_id(problematic)
        message.add_backref(prbid)
        return problematic

    def implicit_inline(self, text, lineno: int) -> ImplicitResult:
        """Check each of the patterns in `self.implicit_dispatch` for a match,
        and dispatch to the stored method for the pattern.

        Recursively check the text before and after the match.
        Return a list of `nodes.Text` and inline element nodes.
        """
        if not text:
            return []
        for pattern, method in self.implicit_dispatch:
            match = pattern.search(text)
            if match:
                try:
                    # Must recurse on strings before *and* after the match;
                    # there may be multiple patterns.
                    return (
                        self.implicit_inline(text[: match.start()], lineno)
                        + method(match, lineno)
                        + self.implicit_inline(text[match.end() :], lineno)
                    )
                except MarkupMismatch:
                    pass
        return [nodes.Text(unescape(text), rawsource=unescape(text, True))]

    def standalone_uri(self, match: Match, lineno: int) -> ImplicitResult:
        """Handle standalone URIs, e.g. http://www.python.org"""
        if (
            not match.group("scheme")
            or match.group("scheme").lower() in urischemes.schemes
        ):
            if match.group("email"):
                addscheme = "mailto:"
            else:
                addscheme = ""
            text = match.group("whole")
            unescaped = unescape(text)
            rawsource = unescape(text, True)
            reference = nodes.reference(
                rawsource, unescaped, refuri=addscheme + unescaped
            )
            reference["standalone_uri"] = True  # myst addition
            reference[0].rawsource = rawsource
            return [reference]
        else:
            raise MarkupMismatch("not a valid scheme")

    def pep_reference(self, match: Match, lineno: int) -> ImplicitResult:
        """Handle reference to a PEP (Python Enhancement Proposal), e.g. `PEP 287`__"""
        text = match.group(0)
        if text.startswith("pep-"):
            pepnum = int(match.group("pepnum1"))
        elif text.startswith("PEP"):
            pepnum = int(match.group("pepnum2"))
        else:
            raise MarkupMismatch
        ref = (
            self.document.settings.pep_base_url
            + self.document.settings.pep_file_url_template % pepnum
        )
        unescaped = unescape(text)
        return [nodes.reference(unescape(text, True), unescaped, refuri=ref)]

    def rfc_reference(self, match: Match, lineno: int) -> ImplicitResult:
        """Handle reference to a RFC (Request For Comments), e.g. `RFC 2822`__"""
        text = match.group(0)
        if text.startswith("RFC"):
            rfcnum = int(match.group("rfcnum"))
            ref = self.document.settings.rfc_base_url + self.rfc_url % rfcnum
        else:
            raise MarkupMismatch
        unescaped = unescape(text)
        return [nodes.reference(unescape(text, True), unescaped, refuri=ref)]


class InlinerMyst(Inliner):
    """Inliner that does not run roles."""

    def interpreted(
        self, rawsource: str, text: str, role: str, lineno: int
    ) -> Tuple[List[nodes.Node], List[nodes.system_message]]:
        """Handle an interpreted text role, e.g. :role:interpreted` or `interpreted`:role:

        MyST Adaption: The role function is located and returned,
        then used to create the requisite nodes and messages.

        """
        return [
            RoleNode(
                rawsource, role=role, text=unescape(text, restore_backslashes=True)
            )
        ], []

    def phrase_ref(
        self, before: str, after: str, rawsource: str, escaped: str, text: str
    ) -> DispatchResult:
        """Handle phrase references e.g. `phrase ref`_, `embedded <ref_>`_

        MyST Adaption: For embedded targets we do not create a separate target node,
        just add ``reference["embedded"] = True``

        """
        match = self.patterns.embedded_link.search(escaped)

        if match:  # embedded <URI> or <alias_>
            text = unescape(escaped[: match.start(0)])
            rawtext = unescape(escaped[: match.start(0)], True)
            aliastext = unescape(match.group(2))
            rawaliastext = unescape(match.group(2), True)
            underscore_escaped = rawaliastext.endswith(r"\_")
            if aliastext.endswith("_") and not (
                underscore_escaped or self.patterns.uri.match(aliastext)
            ):
                aliastype = "name"
                alias = normalize_name(aliastext[:-1])
                target = nodes.target(match.group(1), refname=alias)
                target.indirect_reference_name = aliastext[:-1]
            else:
                aliastype = "uri"
                alias_parts = split_escaped_whitespace(match.group(2))
                alias = " ".join(
                    "".join(unescape(part).split()) for part in alias_parts
                )
                alias = self.adjust_uri(alias)
                if alias.endswith(r"\_"):
                    alias = alias[:-2] + "_"
                target = nodes.target(match.group(1), refuri=alias)
                target.referenced = 1
            if not aliastext:
                raise ApplicationError("problem with embedded link: %r" % aliastext)
            if not text:
                text = alias
                rawtext = rawaliastext
        else:
            target = None
            rawtext = unescape(escaped, True)

        refname = normalize_name(text)
        reference = nodes.reference(
            rawsource, text, name=whitespace_normalize_name(text)
        )
        reference[0].rawsource = rawtext

        # node_list = [reference]
        if target:
            reference["embedded"] = True

        if rawsource[-2:] == "__":
            if target and (aliastype == "name"):
                reference["refname"] = alias
                self.document.note_refname(reference)
            elif target and (aliastype == "uri"):
                reference["refuri"] = alias
            else:
                reference["anonymous"] = 1
        else:
            if target:
                if aliastype == "name":
                    reference["refname"] = alias
                    self.document.note_refname(reference)
                else:
                    reference["refuri"] = alias
            else:
                reference["refname"] = refname
                self.document.note_refname(reference)

        return before, [reference], after, []
