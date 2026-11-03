"""Rebuild web/ela-stc.html: embeds the case (as loader JSON), web/engine.js and web/app.js into the page shell."""
import json
import os
import sys

import yaml

ROOT = os.path.join(os.path.dirname(__file__), "..")
case = yaml.safe_load(open(os.path.join(ROOT, "data", "caso_c172.yaml"), encoding="utf-8"))
page = os.path.join(ROOT, "web", "ela-stc.html")
s = open(page, encoding="utf-8").read()
i = s.index("<script>\nconst DEFAULT_CASE =")
j = s.index("</script>", i)
js = ("<script>\nconst DEFAULT_CASE = " + json.dumps(case, ensure_ascii=False) + ";\n"
      + open(os.path.join(ROOT, "web", "engine.js"), encoding="utf-8").read() + "\n"
      + open(os.path.join(ROOT, "web", "app.js"), encoding="utf-8").read() + "\n")
s = s[:i] + js + s[j:]
open(page, "w", encoding="utf-8").write(s)
json.dump(case, open(os.path.join(ROOT, "web", "fixtures", "caso_loader.json"), "w"), ensure_ascii=False)
print("built", page, len(s))
