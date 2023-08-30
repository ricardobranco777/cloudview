"""
Handle tabular output in these formats: text, json & html
"""

import json
import os
from typing import Optional, Union

from jinja2 import Template

from cloudview.cachedfile import CachedFile
from cloudview.singleton import Singleton


# pylint: disable=redefined-builtin
class Output(metaclass=Singleton):
    """
    Helper class to handle tabular output in text, json or html
    """

    def __init__(
        self,
        type: Optional[str] = None,
        keys: Optional[Union[dict[str, str], list[str]]] = None,
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
        self._items: list[dict] = []
        self._kwargs = kwargs

    def __repr__(self):
        return f'{type(self).__name__}(type="{self._type}", keys={self._keys})'

    def header(self):
        """
        Print the header for output
        """
        if self._type == "text":
            print(
                "  ".join(
                    [f"{key.upper():{align}}" for key, align in self._keys.items()]
                )
            )
        elif self._type == "html":
            header = CachedFile(
                os.path.join(os.path.dirname(__file__), "header.html")
            ).get_data()
            table_header = "".join([f"<th>{key.upper()}</th>" for key in self._keys])
            print(Template(header).render(**self._kwargs), table_header)

    def info(self, item):
        """
        Dump item information
        """
        if self._type == "text":
            print(
                "  ".join([f"{item[key]:{align}}" for key, align in self._keys.items()])
            )
        elif self._type == "json":
            if isinstance(item, dict):
                self._items.append(item)
            else:
                self._items.append(item.__dict__)
        elif self._type == "html":
            item["name"] = f"<a href=\"{item['href']}\">{item['name']}</a>"
            lines = "".join([f" <td>{item[key]}</td>" for key in self._keys])
            print(f"<tr>\n{lines}\n</tr>")

    def footer(self):
        """
        Print the footer for output
        """
        if self._type == "json":
            print(json.dumps(self._items, indent=2, default=str))
        elif self._type == "html":
            footer = CachedFile(
                os.path.join(os.path.dirname(__file__), "footer.html")
            ).get_data()
            print(Template(footer).render(**self._kwargs))
