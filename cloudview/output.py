"""
Handle tabular output in these formats: text, json & html
"""

import html
import json
import os

from jinja2 import Template

from cloudview.singleton import Singleton


# pylint: disable=redefined-builtin
class Output(metaclass=Singleton):
    """
    Helper class to handle tabular output in text, json or html
    """

    def __init__(
        self,
        type: str | None = None,
        keys: dict[str, str] | list[str] | None = None,
        **kwargs,
    ):
        """
        type must be either text, json or html
        fmt is the format string used for text
        keys are the items in the dictionary
        seconds is the refresh time for HTML output
        """
        if type not in ("text", "json", "html"):
            raise ValueError(f"Invalid type: {type}")
        self._type = type
        if isinstance(keys, (list, tuple)):
            self._keys = dict.fromkeys(keys, "")
        else:
            self._keys = keys or {}
        if self._type == "text":
            self._output_format = "  ".join(
                f"{{{key}:{align}}}" for key, align in self._keys.items()
            )
        self._kwargs = kwargs
        self._items: list[dict] = []

    def header(self):
        """
        Print the header for output
        """
        if self._type == "text":
            print(
                self._output_format.format(**{key: key.upper() for key in self._keys})
            )
        elif self._type == "html":
            table_header = "".join(f"<th>{key.upper()}</th>" for key in self._keys)
            table_header = f'<table style="width:100%"><thead><tr>{table_header}</tr></thead><tbody>'
            with open(
                os.path.join(os.path.dirname(__file__), "header.html"), encoding="utf-8"
            ) as file:
                header = file.read()
            print(Template(header).render(**self._kwargs), table_header)

    def info(self, item):
        """
        Dump item information
        """
        if self._type == "text":
            if isinstance(item, dict):
                print(self._output_format.format(**item))
            else:
                print(self._output_format.format(**item.__dict__))
        elif self._type == "json":
            if isinstance(item, dict):
                self._items.append(item)
            else:
                self._items.append(item.__dict__)
        elif self._type == "html":
            info = {
                k: html.escape(item[k]) if isinstance(item[k], str) else item[k]
                for k in self._keys
            }
            info["name"] = f"<a href=\"{item['href']}\">{item['name']}</a>"
            cells = "".join(f"<td>{info[key]}</td>" for key in self._keys)
            print(f"<tr>{cells}</tr>")

    def footer(self):
        """
        Print the footer for output
        """
        if self._type == "json":
            print(json.dumps(self._items, indent=2, default=str))
        elif self._type == "html":
            with open(
                os.path.join(os.path.dirname(__file__), "footer.html"), encoding="utf-8"
            ) as file:
                footer = file.read()
            table_footer = "</tbody></table>"
            print(table_footer, Template(footer).render(**self._kwargs))
