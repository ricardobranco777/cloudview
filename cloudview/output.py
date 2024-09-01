"""
Handle tabular output in these formats: text, json
"""

import json

from cloudview.singleton import Singleton


# pylint: disable=redefined-builtin
class Output(metaclass=Singleton):
    """
    Helper class to handle tabular output in text, json
    """

    def __init__(
        self,
        type: str | None = None,
        keys: dict[str, str] | list[str] | None = None,
        **kwargs,
    ) -> None:
        """
        type must be either text, json
        fmt is the format string used for text
        keys are the items in the dictionary
        """
        if type not in ("text", "json"):
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

    def header(self) -> None:
        """
        Print the header for output
        """
        if self._type == "text":
            print(
                self._output_format.format_map({key: key.upper() for key in self._keys})
            )

    def info(self, item) -> None:
        """
        Dump item information
        """
        if self._type == "text":
            if isinstance(item, dict):
                print(self._output_format.format_map(item))
            else:
                print(self._output_format.format_map(item.__dict__))
        elif self._type == "json":
            self._items.append(item if isinstance(item, dict) else item.__dict__)

    def footer(self) -> None:
        """
        Print the footer for output
        """
        if self._type == "json":
            print(json.dumps(self._items, indent=2, default=str))
