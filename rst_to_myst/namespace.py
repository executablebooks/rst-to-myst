import copy
import threading
from importlib import import_module
from inspect import getdoc
from itertools import chain
from types import ModuleType
from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Optional, Type
from unittest.mock import Mock

from docutils.parsers.rst import Directive, directives, languages, roles

if TYPE_CHECKING:
    from sphinx.domains import Domain
    from sphinx.extension import Extension

LOCK = threading.Lock()


class DomainMock:
    def __init__(self, name, directives=None, roles=None):
        self.name = name
        self.directives = copy.copy(directives or {})
        self.roles = copy.copy(roles or {})

    def __repr__(self) -> str:
        return f"DomainMock(name={self.name})"


class ApplicationNamespace:
    """A mock ``sphinx.application.Sphinx``, to collect roles and directives."""

    def __init__(
        self,
        language_code: str = "en",
        default_domain: Optional[str] = "py",
    ):
        self.extensions: Dict[str, "Extension"] = {}
        self.directives: Dict[str, Directive] = {}
        self.roles: Dict[str, Any] = {}
        self.domains: Dict[str, DomainMock] = {}
        # the default domain will be tried even without the domain prefix
        self.default_domain = default_domain

        self.language_module: Optional[ModuleType] = languages.get_language(
            language_code
        )

    def __getattr__(self, name: str):
        """Mock unneeded methods of ``sphinx.application.Sphinx``."""
        return Mock()

    # sphinx application methods

    def add_directive(
        self, name: str, cls: Type[Directive], override: bool = False
    ) -> None:
        self.directives[name] = cls

    def add_role(self, name: str, role: Any, override: bool = False) -> None:
        self.roles[name] = role

    def add_domain(self, domain: Type["Domain"], override: bool = False) -> None:
        self.domains[domain.name] = DomainMock(
            domain.name, domain.directives, domain.roles
        )

    def add_directive_to_domain(
        self, domain: str, name: str, cls: Type[Directive], override: bool = False
    ) -> None:
        if domain not in self.domains:
            raise KeyError(f"domain {domain} not yet registered")
        self.domains[domain].directives[name] = cls

    def add_role_to_domain(
        self, domain: str, name: str, role: Any, override: bool = False
    ) -> None:
        if domain not in self.domains:
            raise KeyError(f"domain {domain} not yet registered")
        self.domains[domain].roles[name] = role

    # additional methods

    def get_element(self, attr: str, name: str):

        # convert to standardised name
        canonicalname = name.lower()
        # try translation
        if self.language_module is not None:
            try:
                canonicalname = getattr(self.language_module, attr)[canonicalname]
            except (AttributeError, KeyError):
                pass

        if ":" in canonicalname:
            # look in domains
            domain_name, domain_element = canonicalname.split(":", 1)
            if domain_name in self.domains:
                domain = self.domains[domain_name]
                element = getattr(domain, attr).get(domain_element, None)
                if element is not None:
                    return element

        elif self.default_domain is not None and self.default_domain in self.domains:
            # look in default domain
            domain = self.domains[self.default_domain]
            element = getattr(domain, attr).get(canonicalname, None)
            if element is not None:
                return element

        # always look in std domain
        if "std" in self.domains:
            domain = self.domains["std"]
            element = getattr(domain, attr).get(canonicalname, None)
            if element is not None:
                return element

        # now look in standard location
        return getattr(self, attr).get(canonicalname, None)

    def get_directive(self, name: str):
        return self.get_element("directives", name)

    def get_role(self, name: str):
        return self.get_element("roles", name)

    def list_directives(self) -> List[str]:
        """List all directive names"""
        return sorted(self.directives) + sorted(
            f"{prefix}:{name}"
            for prefix, domain in self.domains.items()
            for name in domain.directives
        )

    def list_roles(self) -> List[str]:
        """List all role names"""
        return sorted(self.roles) + sorted(
            f"{prefix}:{name}"
            for prefix, domain in self.domains.items()
            for name in domain.roles
        )

    def get_directive_data(self, name: str) -> dict:
        """Return data about a particular directive."""
        direct = self.get_directive(name)
        if direct is None:
            raise KeyError(f"Directive not found: {name}")

        options = (
            {k: str(v.__name__) for k, v in direct.option_spec.items()}
            if direct.option_spec
            else {}
        )
        data = {
            "name": name,
            "description": getdoc(direct) or "",
            "class": f"{direct.__module__}.{direct.__name__}",
            "required_arguments": direct.required_arguments,
            "optional_arguments": direct.optional_arguments,
            "has_content": direct.has_content,
            "options": options,
        }
        if "Base class for " in data["description"]:
            # base class for docutils is too verbose
            data["description"] = ""
        return data

    def get_role_data(self, name: str) -> dict:
        """Return data about a particular role."""
        role = self.get_role(name)
        if role is None:
            raise KeyError(f"Role not found: {name}")
        return {
            "name": name,
            "description": getdoc(role) or "",
            "module": f"{role.__module__}",
        }


def compile_namespace(
    extensions: Iterable[str] = (),
    use_sphinx: bool = True,
    default_domain="py",
    language_code="en",
) -> ApplicationNamespace:
    """Gather all available directives and roles."""
    app = ApplicationNamespace(
        default_domain=default_domain, language_code=language_code
    )

    for key, (modulename, classname) in directives._directive_registry.items():
        if key not in app.directives:
            try:
                module = import_module(f"docutils.parsers.rst.directives.{modulename}")
                app.directives[key] = getattr(module, classname)
            except (AttributeError, ModuleNotFoundError):
                pass

    old_directives = directives._directives

    app.roles.update(roles._role_registry)
    app.roles.update(roles._roles)

    old_roles = roles._roles

    if not use_sphinx:
        return app

    from sphinx.application import builtin_extensions
    from sphinx.errors import ExtensionError
    from sphinx.extension import Extension
    from sphinx.registry import EXTENSION_BLACKLIST

    LOCK.acquire()
    try:

        directives._directives = app.directives
        roles._roles = app.roles

        for extname in chain(builtin_extensions, extensions):

            if extname in app.extensions or extname in EXTENSION_BLACKLIST:
                continue

            try:
                mod = import_module(extname)
            except ImportError as err:
                raise ImportError(f"Could not import extension {extname}", err) from err

            setup = getattr(mod, "setup", None)
            if setup is None:
                raise ExtensionError(
                    "extension %r has no setup() function; is it really "
                    "a Sphinx extension module?",
                    extname,
                )

            metadata = setup(app) or {}

            if not isinstance(metadata, dict):
                metadata = {}

            app.extensions[extname] = Extension(extname, mod, **metadata)

    finally:
        directives._directives = old_directives
        roles._roles = old_roles
        LOCK.release()

    return app


if __name__ == "__main__":
    _app = compile_namespace(("sphinx.ext.autosummary",))
    for _name, _cls in _app.directives.items():
        if "patch" in _cls.__module__:
            print(f"# {_name}")
            print(f"{_cls.__module__}.{_cls.__name__}: eval_rst")
    # for _dname, _domain in _app.domains.items():
    #     for _name, _cls in _domain.directives.items():
    #         print(f"# {_dname}:{_name}")
    #         print(f"{_cls.__module__}.{_cls.__name__}: eval_rst")
