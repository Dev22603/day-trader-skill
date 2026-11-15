"""trader-learn: the course file, the glossary and the course keeper (learn.py)."""

import io
import json
import os
import re
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from _load import load, ROOT

learn = load("trader-learn", "learn")
ticket = load("trader-broker", "ticket")

with open(learn.COURSE, encoding="utf-8") as _fh:
    COURSE_TEXT = _fh.read()
with open(learn.GLOSSARY, encoding="utf-8") as _fh:
    GLOSSARY_TEXT = _fh.read()
LESSONS = learn.parse_course(COURSE_TEXT)
WORDS = learn.parse_glossary(GLOSSARY_TEXT)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = learn.main(argv)
    return code, out.getvalue(), err.getvalue()


class Course(unittest.TestCase):
    def test_every_lesson_is_complete(self):
        self.assertEqual(len(LESSONS), 43)
        ids = [l["id"] for l in LESSONS]
        self.assertEqual(len(set(ids)), len(ids))
        self.assertEqual(ids[0], "A1")                                     # it starts with revenue
        for l in LESSONS:
            self.assertTrue(l["title"] and l["goal"] and l["example"] and l["pack"] and l["module"], l["id"])
            self.assertGreaterEqual(len(l["points"]), 3, l["id"])
            self.assertGreaterEqual(len(l["checks"]), 2, l["id"])
            for q, a in l["checks"]:
                self.assertTrue(q.endswith("?") and a, (l["id"], q))

    def test_eleven_modules_in_order(self):
        mods = []
        for l in LESSONS:
            if l["module"] not in mods:
                mods.append(l["module"])
        self.assertEqual([m.split()[0] for m in mods], list("ABCDEFGHIJK"))
        for l in LESSONS:
            self.assertEqual(l["id"][0], l["module"][0], l["id"])          # lesson H3 sits in module H

    def test_gross_and_net_are_the_stall_example(self):
        a = {l["id"]: l for l in LESSONS}
        self.assertIn("2,000 - 800 = Rs 1,200", a["A2"]["example"])        # gross profit
        self.assertIn("net profit of Rs 300", a["A3"]["example"])          # after expenses, interest and tax
        self.assertIn("1,200 / 2,000 = 60%", a["A4"]["example"])
        self.assertIn("300 / 2,000 = 15%", a["A4"]["example"])

    def test_the_cost_lesson_quotes_what_the_tools_compute(self):
        # one TCS share, bought at 2,442.00: the same trade the tools' own tests use
        win, lose = ticket.nse_charges(2442.0, 2461.3), ticket.nse_charges(2442.0, 2422.7)
        i1 = [l for l in LESSONS if l["id"] == "I1"][0]["example"]
        for part in ("brokerage", "stt", "exchange", "stamp", "gst", "total"):
            self.assertIn("%.2f" % win[part], i1, part)
        i2 = [l for l in LESSONS if l["id"] == "I2"][0]["example"]
        net_win, net_loss = round(19.30 - win["total"], 2), round(19.30 + lose["total"], 2)
        self.assertIn("+%.2f net" % net_win, i2)
        self.assertIn("-%.2f net" % net_loss, i2)
        self.assertIn("%.2f" % round(net_win / net_loss, 2), i2)           # reward to risk after costs
        self.assertIn("about %d%%" % round(100 * net_loss / (net_win + net_loss)), i2)   # break-even win rate
        rates = ticket.NSE_CHARGES
        points = " ".join([l for l in LESSONS if l["id"] == "I1"][0]["points"])
        for fact in ("%g%%" % rates["brokerage_pct"], "Rs %g" % rates["brokerage_max"], "%g%%" % rates["stt_sell_pct"],
                     "%g%%" % rates["exchange_pct"], "%g%%" % rates["stamp_buy_pct"], "%g%%" % rates["gst_pct"]):
            self.assertIn(fact, points, fact)

    def test_the_risk_lessons_add_up(self):
        h = {l["id"]: l for l in LESSONS}
        self.assertIn("2,442.00 - 2,422.70 = Rs 19.30", h["H1"]["example"])
        self.assertIn("15 x 19.30 = Rs 289.50", h["H3"]["example"])
        self.assertEqual(int(500 / 19.30), 25)                              # "25 shares at most"
        self.assertIn("0.4 x 2 - 0.6 x 1 = +0.2R", h["H4"]["example"])
        self.assertAlmostEqual(0.5 * 0.76 - 0.5 * 1.13, -0.185, places=3)   # "a loss of about 0.19R"
        self.assertIn("lose Rs 1,000, which is 10% of your money", h["H5"]["example"])

    def test_plain_ascii_and_the_shape_learn_py_reads(self):
        for name, text in (("course.md", COURSE_TEXT), ("glossary.md", GLOSSARY_TEXT)):
            self.assertEqual(sorted({c for c in text if ord(c) > 127}), [], name)   # prints on any console
        self.assertEqual(len(re.findall(r"(?m)^### ", COURSE_TEXT)), len(LESSONS))   # no lesson was skipped


class Glossary(unittest.TestCase):
    def test_every_word_points_at_a_lesson(self):
        self.assertGreaterEqual(len(WORDS), 80)
        self.assertEqual(len(re.findall(r"(?m)^- \*\*", GLOSSARY_TEXT)), len(WORDS))   # every line parsed
        ids = {l["id"] for l in LESSONS}
        for w in WORDS:
            self.assertIn(w["lesson"], ids, w["term"])
        owner = {}                                   # no name may lead to two different words
        for w in WORDS:
            for name in [w["term"]] + w["aliases"]:
                self.assertEqual(owner.setdefault(learn.squeeze(name), w["term"]), w["term"], name)

    def test_the_words_a_beginner_asks_first(self):
        for asked, term in (("gross profit", "gross profit"), ("net profit", "net profit"),
                            ("net vs gross", "gross and net"), ("turnover", "revenue"), ("stoploss", "stop-loss"),
                            ("Stop Loss", "stop-loss"), ("SL-M", "stop-loss"), ("PE ratio", "P/E"), ("F&O", "futures and options"),
                            ("pledge", "pledging"), ("MIS", "intraday"), ("CNC", "delivery"), ("STT", "STT"),
                            ("R:R", "reward to risk"), ("nifty", "index"), ("demat", "demat account")):
            hit, how = learn.find_term(WORDS, asked)
            self.assertEqual((hit and hit["term"], how), (term, "exact"), asked)
        hit, how = learn.find_term(WORDS, "brokrage")                       # a typo finds the closest word
        self.assertEqual((hit["term"], how), ("brokerage", "close"))
        self.assertIsNone(learn.find_term(WORDS, "zzzzqx")[0])


class Keeper(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.state = os.path.join(self.tmp.name, "state", "learn.json")

    def go(self, *argv):
        return run(["--state", self.state] + list(argv))

    def test_next_moves_on_when_a_lesson_is_done(self):
        code, out, _ = self.go("next")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("A1  Revenue: the money that comes in"), out[:60])
        self.assertIn("Check (ask one at a time, wait for the answer, never show the answer first):", out)
        self.assertIn("answer: Rs 3,000 (150 x 20).", out)
        self.assertIn("learn.py done A1 --score RIGHT/2", out)
        code, out, _ = self.go("done", "a1", "--score", "2/2")
        self.assertEqual(code, 0)
        self.assertIn("Done: A1 Revenue: the money that comes in (2/2).", out)
        self.assertIn("Next: A2 Gross profit", out)
        self.assertTrue(self.go("next")[1].startswith("A2  "))
        with open(self.state) as fh:
            self.assertEqual(json.load(fh)["done"]["A1"]["score"], "2/2")
        code, out, _ = self.go("list")
        self.assertIn("  [x] A1  Revenue: the money that comes in  (2/2)", out)
        self.assertIn("  [ ] A2  Gross profit", out)
        self.assertIn("1 of 43 lessons done.", out)

    def test_show_term_and_the_end_of_the_course(self):
        code, out, _ = self.go("show", "h3")
        self.assertIn("H3  Position size: how many shares", out)
        self.assertIn("Module: H Risk", out)
        code, out, _ = self.go("term", "gross profit")
        self.assertEqual(code, 0)
        self.assertTrue(out.startswith("gross profit: Revenue minus the cost of goods sold"), out)
        self.assertIn("Lesson A2.", out)
        code, out, _ = self.go("term", "brokrage")
        self.assertIn("Closest word in the glossary to \"brokrage\":", out)
        code, out, _ = self.go("term", "zzzzqx")
        self.assertEqual(code, 1)
        self.assertIn("is not in the glossary", out)
        for l in LESSONS:
            self.go("done", l["id"])
        code, out, _ = self.go("next")
        self.assertEqual(code, 1)
        self.assertIn("The course is finished: all 43 lessons are done.", out)

    def test_plain_errors(self):
        code, _, err = self.go("show", "Z9")
        self.assertEqual(code, 1)
        self.assertIn("there is no lesson Z9", err)
        code, _, err = self.go("done", "A1", "--score", "two")
        self.assertIn("--score wants right/asked, like 2/3", err)
        os.makedirs(os.path.dirname(self.state))
        with open(self.state, "w") as fh:
            fh.write("{not json")
        self.assertIn("is not valid JSON", self.go("list")[2])


class Skill(unittest.TestCase):
    def test_the_skill_file_matches_the_course(self):
        with open(os.path.join(ROOT, "trader-learn", "SKILL.md"), encoding="utf-8") as fh:
            text = fh.read()
        self.assertIn("43 short lessons", text)
        for mod in "ABCDEFGHIJK":
            last = max(int(l["id"][1:]) for l in LESSONS if l["id"][0] == mod)
            self.assertIn("| %s1 to %s%d |" % (mod, mod, last), text, mod)   # the course table is right
        self.assertIn("not financial advice", text.lower())


if __name__ == "__main__":
    unittest.main()
