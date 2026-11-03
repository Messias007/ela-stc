"""Exported browser projects must give the same results in Python (fixtures from web/test_roundtrip.js)."""
import json
import os
import shutil
import subprocess

import pytest

from ela_stc.analysis import analyze, garmin_net_change
from ela_stc.loader import load_case, load_params
from ela_stc.models import Installation

WEB = os.path.join(os.path.dirname(__file__), "..", "web")
FIX = os.path.join(WEB, "fixtures")


@pytest.fixture(scope="module", autouse=True)
def regenerate():
    if shutil.which("node"):
        subprocess.run(["node", "test_roundtrip.js"], cwd=WEB, check=True, capture_output=True)


@pytest.mark.parametrize("name", ["base", "params", "two_gtn750", "custom"])
def test_python_matches_browser(name):
    path = os.path.join(FIX, f"rt_{name}.json")
    aml, inst = load_case(path)
    p = load_params(path)
    js = json.load(open(os.path.join(FIX, f"rt_{name}_js.json")))
    for ac, j in zip(aml, js):
        a, b = analyze(ac, inst, p), analyze(ac, Installation(name="n"), p)
        py = [a["alt_frac_cont"], a["alt_frac_avg"], a["breaker_frac"], a["margin_min"], b["margin_min"],
              garmin_net_change(ac, inst)["net_a"]]
        assert py == pytest.approx([j["cont"], j["avg"], j["bk"], j["margin"], j["before"], j["net"]], rel=1e-9, abs=1e-9)
