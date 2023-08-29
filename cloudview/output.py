"""
Handle tabular output in these formats: text, json & html
"""

import json
from typing import Optional

from cloudview.singleton import Singleton
from cloudview.templates import HEADER, FOOTER


# pylint: disable=redefined-builtin
class Output(metaclass=Singleton):
    """
    Helper class to handle tabular output in text, json or html
    """

    def __init__(
        self,
        type: Optional[str] = None,
        format: Optional[str] = None,
        keys: Optional[list[str]] = None,
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
        self._format = format
        if keys is None:
            keys = []
        self._keys = keys
        self._items: list[dict] = []

    def __repr__(self):
        return f'{type(self).__name__}(type="{self._type}", format="{self._format}", keys={self._keys})'

    def header(self):
        """
        Print the header for output
        """
        if self._type == "text":
            print(self._format.format(item={key: key.upper() for key in self._keys}))
        elif self._type == "html":
            table_header = "".join([f"<th>{key.upper()}</th>" for key in self._keys])
            print(f"{HEADER}{table_header}")

    def info(self, item):
        """
        Dump item information
        """
        if self._type == "text":
            print(self._format.format(item=item))
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
            print(FOOTER)
