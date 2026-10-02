import unittest, copy, json
from decimal import Decimal
from pathlib import Path
from cryptolab import analyze
from cryptolab.engine import *

EXAMPLE = json.loads(Path("examples/input.json").read_text())


class DomainTests(unittest.TestCase):
    def test_conflict_detection(self):
        r = analyze(EXAMPLE)
        self.assertTrue(r["safety_violation"])
        self.assertEqual(r["equivocating_weight"], 75)

    def test_quorum(self):
        self.assertEqual(analyze(EXAMPLE)["quorum_threshold"], 67)

    def test_duplicate_not_weighted(self):
        d = copy.deepcopy(EXAMPLE)
        d["votes"] *= 2
        r = analyze(d)
        self.assertEqual(r["duplicate_votes"], 4)
        self.assertEqual(r["certificates"][0]["weight"], 75)

    def test_no_quorum(self):
        d = copy.deepcopy(EXAMPLE)
        d["votes"] = d["votes"][:1]
        self.assertEqual(analyze(d)["certificates"], [])

    def test_ancestry(self):
        d = copy.deepcopy(EXAMPLE)
        d["blocks"][1]["height"] = 2
        with self.assertRaises(ValueError):
            analyze(d)
