#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Handle tabular output in these formats: text, json & html
"""

from json import JSONEncoder


# TODO: Parameterize refresh time
HTML_HEADER = '''<!DOCTYPE html>
<html><head><meta charset="utf-8" http-equiv="refresh" content="600"/>
<title>Instances</title></head>
<style>
body {
  background-color: white;
  color: black;
}
table, th, td {
  border: 1px solid black;
  border-collapse: collapse;
}
th, td {
  padding: 10px;
}
th {
  text-align: left;
}
table#instances tr:nth-child(even) {
  background-color: #eee;
}
table#instances tr:nth-child(odd) {
  background-color: #fff;
}
</style>
<body><table style="width:77%" id="instances">
'''

# TODO: Parameterize date format
HTML_FOOTER = '''</table><br>
Last updated:
<p id="date" style="background-color:white;color:black;"></p>
<script>
    var date = new Date();
    document.getElementById("date").innerHTML = date;
</script>
</body></html>'''


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
                "<th>%s</th>" % _.upper() for _ in self.keys])
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
