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
        seconds: int = 600,
    ):
        """
        type must be either text, json or html
        fmt is the format string used for text
        keys are the items in the dictionary
        seconds is the refresh time for HTML output
        """
        if type not in ("text", "json", "html"):
            raise ValueError(f"Invalid type: {type}")
        self.type = type
        if keys is None:
            keys = []
        self.keys = keys
        self.format = format
        self.seconds = seconds
        self.data: list[dict] = []

    def header(self):
        """
        Print the header for output
        """
        if self.type == "text":
            print(self.format.format(item={key: key.upper() for key in self.keys}))
        elif self.type == "html":
            table_header = "\n".join([f"<th>{key.upper()}</th>" for key in self.keys])
            print(f"{HEADER}{table_header}")

    def info(self, item):
        """
        Dump item information
        """
        if self.type == "text":
            print(self.format.format(item=item))
        elif self.type == "json":
            self.data.append(item.__dict__)
        elif self.type == "html":
            item.name = f'<a href="{item.href}">{item.name}</a>'
            lines = "\n".join([f" <td>{item[key]}</td>" for key in self.keys])
            print(f"<tr>\n{lines}\n</tr>")

    def footer(self):
        """
        Print the footer for output
        """
        if self.type == "json":
            print(json.dumps(self.data, indent=2, default=str))
        elif self.type == "html":
            print(FOOTER)
