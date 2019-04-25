#
# Copyright 2019 Ricardo Branco <rbranco@suse.de>
# MIT License
#
"""
Handle tabular output in these formats: text, json & html
"""

from json import JSONEncoder
from cloudview.singleton import Singleton


# TODO: Parameterize refresh time
HTML_HEADER = '''<!DOCTYPE html>
<html><head><meta charset="utf-8" http-equiv="refresh" content="600"/>
<title>Instances</title></head>
<style>
body, p {
  background-color: white;
  color: black;
}
a {
  text-decoration:none;
}
a:link, a:visited {
  color: blue;
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
  background-color: white;
}
</style>
<body><table style="width:77%" id="instances">
'''

# TODO: Parameterize date format
HTML_FOOTER = '''</table><br>
<p>Last updated: <span id="date"></span></p>
<script type="text/javascript">
var date = new Date();
document.getElementById("date").innerHTML = date;
</script>

<p id="refresh"></p>
<script type="text/javascript">
var seconds = 600;
var timer = setInterval(function(){
seconds--;
document.getElementById("refresh").textContent = "Next refresh in " + seconds + " seconds";
  if (seconds <= 0) {
    clearInterval(timer);
    document.getElementById("refresh").textContent = "Refreshing...";
  }
}, 1000);
</script>
</body></html>'''


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
                "<th>%s</th>" % _.upper().replace('_', ' ') for _ in self.keys])
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
                kwargs['provider'].lower(), kwargs['instance_id'], kwargs['name'])
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
