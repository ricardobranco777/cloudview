"""
Handle tabular output in these formats: text, json & html
"""

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
        template: str | None = None,
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
        self.type = type
        self.template = template
        if isinstance(keys, (list, tuple)):
            self.keys = dict.fromkeys(keys, "")
        else:
            self.keys = keys or {}
        self.items: list[dict] = []
        self.kwargs = kwargs

    def __repr__(self):
        return (
            f"{type(self).__name__}("
            + ", ".join(
                [
                    f"{k}='{repr(getattr(self, k))}'"
                    if getattr(self, k) is not None
                    else f"{k}=None"
                    for k in ("type", "template", "keys")
                ]
            )
            + ")"
        )

    def header(self):
        """
        Print the header for output
        """
        if self.type == "text":
            if self.template is None:
                print(
                    "  ".join(
                        [f"{key.upper():{align}}" for key, align in self.keys.items()]
                    )
                )
        elif self.type == "html":
            table_header = "".join([f"<th>{key.upper()}</th>" for key in self.keys])
            with open(
                os.path.join(os.path.dirname(__file__), "header.html"), encoding="utf-8"
            ) as file:
                header = file.read()
            print(Template(header).render(**self.kwargs), table_header)

    def info(self, item):
        """
        Dump item information
        """
        if self.type == "text":
            if self.template is None:
                print(
                    "  ".join(
                        [f"{item[key]:{align}}" for key, align in self.keys.items()]
                    )
                )
            else:
                print(Template(self.template).render(item.__dict__))
        elif self.type == "json":
            if isinstance(item, dict):
                self.items.append(item)
            else:
                self.items.append(item.__dict__)
        elif self.type == "html":
            item["name"] = f"<a href=\"{item['href']}\">{item['name']}</a>"
            lines = "".join([f" <td>{item[key]}</td>" for key in self.keys])
            print(f"<tr>\n{lines}\n</tr>")

    def footer(self):
        """
        Print the footer for output
        """
        if self.type == "json":
            print(json.dumps(self.items, indent=2, default=str))
        elif self.type == "html":
            with open(
                os.path.join(os.path.dirname(__file__), "footer.html"), encoding="utf-8"
            ) as file:
                footer = file.read()
            print(Template(footer).render(**self.kwargs))
