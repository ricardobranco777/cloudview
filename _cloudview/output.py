#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Handle tabular output in these formats: text, json & html
"""

from functools import lru_cache
from os.path import dirname
from json import JSONEncoder

from jinja2 import Template

from _cloudview.singleton import Singleton


@lru_cache(maxsize=1)
def get_html_header(**kwargs):
    """
    Return the HTML header rendered from a Jinja2 template
    """
    with open(dirname(__file__) + "/html/header.html", encoding="utf-8") as file:
        template = Template(file.read())
    return template.render(**kwargs)


@lru_cache(maxsize=1)
def get_html_footer(**kwargs):
    """
    Return the HTML footer rendered from a Jinja2 template
    """
    with open(dirname(__file__) + "/html/footer.html", encoding="utf-8") as file:
        template = Template(file.read())
    return template.render(**kwargs)


@Singleton
class Output:
    """
    Helper class to handle tabular output in text, json or html
    """
    def __init__(self, output_format=None, fmt=None, keys=None, seconds=600):
        """
        type must be either text, json or html
        fmt is the format string used for text
        keys are the items in the dictionary
        seconds is the refresh time for HTML output
        """
        if output_format not in ('text', 'json', 'html'):
            raise ValueError(f"Invalid type: {output_format}")
        self.output_format = output_format
        self.keys = keys.split()
        self.fmt = fmt
        self.last_item = None
        self.seconds = seconds

    def header(self):
        """
        Print the header for output
        """
        if self.output_format == "text":
            print(self.fmt.format(d={
                _: _.upper()
                for _ in self.keys
            }))
        elif self.output_format == "json":
            print("[")
        elif self.output_format == "html":
            table_header = "\n".join([f"<th>{_.upper().replace('_', ' ')}</th>" for _ in self.keys])
            print(get_html_header(seconds=self.seconds) + table_header)

    def info(self, item=None, **kwargs):
        """
        Dump item information
        """
        if item is None:
            item = dict(kwargs)
        if self.output_format == "text":
            print(self.fmt.format(d=item))
        elif self.output_format == "json":
            if self.last_item is not None:
                print(f"{self.last_item}")
            self.last_item = JSONEncoder(
                default=str, indent=2, sort_keys=True
            ).encode(item)
        elif self.output_format == "html":
            kwargs['name'] = f"<a href=\"instance/{kwargs['provider'].lower()}/{kwargs['instance_id']}\">{kwargs['name']}</a>"
            lines = "\n".join([f" <td>{kwargs[_]}</td>" for _ in self.keys])
            print(f"<tr>\n{lines}\n</tr>")

    def all(self, iterable):
        """
        Dump all items in iterable
        """
        for item in iterable:
            self.info(item=item)

    def footer(self):
        """
        Print the footer for output
        """
        if self.output_format == "json":
            if self.last_item is None:
                self.last_item = ""
            print(f"{self.last_item}\n]")
        elif self.output_format == "html":
            print(get_html_footer(seconds=self.seconds))
