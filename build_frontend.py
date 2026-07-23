#!/usr/bin/env python3
"""Combines frontend parts into index.html"""
import os
BASE = os.path.dirname(os.path.abspath(__file__))
PARTS = os.path.join(BASE, "frontend", "parts")
OUT   = os.path.join(BASE, "frontend", "index.html")

def read(name):
    with open(os.path.join(PARTS, name), encoding="utf-8") as f:
        return f.read()

head   = read("head.html")
utils  = read("utils.js")
page1  = read("page1.jsx")
page2  = read("page2.jsx")
page3  = read("page3.jsx")
app    = read("app.jsx")

html = f"""{head}
</head>
<body>
<div id="root"></div>
<script type="text/babel">
{utils}
{page1}
{page2}
{page3}
{app}
</script>
</body>
</html>
"""

with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)

print(f"Built -> {OUT}  ({len(html):,} chars)")
