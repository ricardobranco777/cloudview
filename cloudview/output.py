#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Handle tabular output in these formats: text, json & html
"""

from os.path import dirname
from json import JSONEncoder

from cloudview.singleton import Singleton


with open(dirname(__file__) + "/html/header.html") as file:
    HTML_HEADER = file.read()

with open(dirname(__file__) + "/html/footer.html") as file:
    HTML_FOOTER = file.read()


@Singleton
class Output:
    """
    Helper class to handle tabular output in text, json or html
    """
    def __init__(self, type=None, fmt=None, keys=None):
        """
        type must be either text, json or html
        fmt is the format string used for text
        keys are the items in the dictionary
        """
        if type not in ('text', 'json', 'html'):
            raise ValueError("Invalid type: %s" % type)
        self.type = type
        self.keys = keys.split()
        self.fmt = fmt
        self.last_item = None

    def header(self):
        """
        Print the header for output
        """
        if self.type == "text":
            print(self.fmt.format(d={
                _: _.upper()
                for _ in self.keys
            }))
        elif self.type == "json":
            print("[")
        elif self.type == "html":
            table_header = "\n".join([
                "<th>{}</th>".format(_.upper().replace('_', ' '))
                for _ in self.keys])
            print(HTML_HEADER + table_header)

    def info(self, item=None, **kwargs):
        """
        Dump item information
        """
        if item is None:
            item = dict(kwargs)
        if self.type == "text":
            print(self.fmt.format(d=item))
        elif self.type == "json":
            if self.last_item is not None:
                print("%s," % self.last_item)
            self.last_item = JSONEncoder(
                default=str, indent=2, sort_keys=True
            ).encode(item)
        elif self.type == "html":
            kwargs['name'] = '<a href="instance/%s/%s">%s</a>' % (
                kwargs['provider'].lower(),
                kwargs['instance_id'],
                kwargs['name'])
            print(
                "<tr>\n" +
                "\n".join([
                    "<td>%s</td>" % kwargs[_] for _ in self.keys]) +
                "</tr>")

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
        if self.type == "json":
            if self.last_item is None:
                self.last_item = ""
            print("%s\n]" % self.last_item)
        elif self.type == "html":
            print(HTML_FOOTER)
