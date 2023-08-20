"""
Jinja templates
"""

from jinja2 import Template


_HEADER = """<!DOCTYPE html>
<html><head><meta charset="utf-8" http-equiv="refresh" content="{{ seconds }}"/>
<link rel="shortcut icon" href="/favicon.ico">
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
<body>
<center><h2><a href="https://github.com/ricardobranco777/cloudview">CloudView</a></h2></center>
<table style="width:100%" id="instances">
"""

_FOOTER = """
</table><br>
<p>Last updated: <span id="date"></span></p>
<script type="text/javascript">
var date = new Date();
document.getElementById("date").innerHTML = date;
</script>

<p id="refresh"></p>
<script type="text/javascript">
 var seconds = {{ seconds }};
 var timer = setInterval(function() {
  seconds--;
  document.getElementById("refresh").textContent = "Next refresh in " + seconds + " seconds";
  if (seconds <= 0) {
   clearInterval(timer);
   document.getElementById("refresh").textContent = "Refreshing...";
  }
 }, 1000);
</script>
</body></html>"""


HEADER = Template(_HEADER)
FOOTER = Template(_FOOTER)
