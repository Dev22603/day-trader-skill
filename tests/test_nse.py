"""The Indian market: a symbol ending in .NS runs on the NSE clock (India time,
9:15 to 15:30, the NSE holiday list, flat by 15:15) and goes to Yahoo unchanged.

Synthetic bars, built here: no network and no fixture files. Every tool is
loaded as its own copy, so the market switch never reaches the US tests."""

import datetime
import io
import json
import os
import random
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from _load import load, ROOT

entry = load("trader-entry", "entry")
exitp = load("trader-exit", "exit")
alerts = load("trader-alerts", "alerts")
check = load("trader-risk", "check")
scan = load("trader-scanner", "scan")
tm = load("trader-timemachine", "timemachine")
size = load("trader-budget", "size")
ticket = load("trader-broker", "ticket")
news = load("trader-news", "news")

DT = datetime.datetime
SYM = "RELIANCE.NS"
DAY = datetime.date(2026, 11, 16)          # a Monday, a normal NSE session
CFG_PATH = os.path.join(ROOT, "trader-budget", "config.example.json")
# NSE capital-market trading holidays 2026 (circulars NSE/CMTR/71775 and NSE/CMTR/72260)
NSE_2026 = ["2026-01-15", "2026-01-26", "2026-03-03", "2026-03-26", "2026-03-31", "2026-04-03", "2026-04-14",
            "2026-05-01", "2026-05-28", "2026-06-26", "2026-09-14", "2026-10-02", "2026-10-20", "2026-11-10",
            "2026-11-24", "2026-12-25"]
PLAN = {"created_by": "trader-exit", "symbol": SYM, "side": "buy", "date": DAY.isoformat(), "setup": "orb",
        "entry": 1500.0, "entry_time": "9:40 AM", "entry_bar": 4, "interval": "5m",
        "opening_range": {"high": 1498.0, "low": 1490.0, "minutes": 15},
        "stop": 1495.0, "target": 1506.0, "risk_per_share": 5.0, "reward_risk": 1.2}


def ts(day, hhmm):
    """India wall-clock time -> Unix seconds (India is UTC+5:30 all year)."""
    h, m = [int(x) for x in hhmm.split(":")]
    local = DT.combine(day, datetime.time(h, m))
    return int((local - datetime.timedelta(hours=5, minutes=30) - DT(1970, 1, 1)).total_seconds())


def chart_doc(bars, sym=SYM):
    """[(unix seconds, open, high, low, close, volume)] -> Yahoo's v8 chart JSON."""
    cols = list(zip(*bars))
    return {"chart": {"error": None, "result": [{
        "meta": {"symbol": sym, "dataGranularity": "5m", "previousClose": 1480.0},
        "timestamp": list(cols[0]),
        "indicators": {"quote": [{"open": list(cols[1]), "high": list(cols[2]), "low": list(cols[3]),
                                  "close": list(cols[4]), "volume": list(cols[5])}]}}]}}


# 09:15, 09:20, 09:25 set the range (high 1498, low 1490); the 09:35 bar closes above it at 1500
MORNING = [("09:15", 1492, 1496, 1490, 1495), ("09:20", 1495, 1498, 1493, 1494), ("09:25", 1494, 1497, 1492, 1496),
           ("09:30", 1496, 1498, 1494, 1497), ("09:35", 1497, 1501, 1496, 1500), ("09:40", 1500, 1503, 1499, 1502),
           ("09:45", 1502, 1504, 1500, 1501), ("09:50", 1501, 1503, 1499, 1500), ("09:55", 1500, 1502, 1498, 1501)]


def morning(day=DAY):
    return [(ts(day, t), o, h, l, c, 10000) for t, o, h, l, c in MORNING]


def run(mod, argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = mod.main(argv)
    return code, out.getvalue(), err.getvalue()


class Files(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)

    def path(self, name):
        return os.path.join(self.tmp.name, name)

    def write(self, name, doc):
        with open(self.path(name), "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return self.path(name)


class Calendar(unittest.TestCase):
    def test_the_holiday_list_is_the_published_one(self):
        for mod in (entry, exitp, alerts, check, scan):
            self.assertEqual(sorted(mod.NSE_HOLIDAYS), NSE_2026, mod.__name__)
        for d in NSE_2026:
            self.assertLess(datetime.date.fromisoformat(d).weekday(), 5, d)

    def test_india_time_is_utc_plus_530_all_year(self):
        for mod in (entry, exitp, alerts, check, scan, tm, size, ticket):
            mod.use_market([SYM])
            for day in ("2026-07-01", "2026-12-01"):            # no daylight time: the same in July and December
                utc = mod.parse_now(day + " 09:15")
                self.assertEqual((utc.hour, utc.minute), (3, 45), mod.__name__)
                self.assertEqual(mod.to_eastern(utc), DT.fromisoformat(day + " 09:15"), mod.__name__)

    def test_the_session_is_915_to_1530(self):
        alerts.use_market([SYM])
        at = lambda t: alerts.market_status(alerts.parse_now("2026-11-16 " + t))
        early = at("09:14")
        self.assertEqual((early["open"], early["reason"], early["next_open"]),
                         (False, "before the open", "2026-11-16 09:15"))
        opened = at("09:15")
        self.assertEqual((opened["open"], opened["opens"], opened["closes"], opened["early_close"]),
                         (True, "09:15", "15:30", None))
        self.assertTrue(at("15:29")["open"])
        closed = at("15:30")
        self.assertEqual((closed["open"], closed["reason"], closed["next_open"]),
                         (False, "after the close", "2026-11-17 09:15"))

    def test_holidays_weekends_and_an_unknown_year(self):
        alerts.use_market([SYM])
        hol = alerts.market_status(alerts.parse_now("2026-11-24 10:00"))
        self.assertEqual((hol["open"], hol["reason"]), (False, "NSE holiday: Prakash Gurpurb Sri Guru Nanak Dev"))
        self.assertEqual(hol["next_open"], "2026-11-25 09:15")
        self.assertEqual(alerts.market_status(alerts.parse_now("2026-11-14 10:00"))["reason"], "weekend")
        self.assertTrue(alerts.market_status(alerts.parse_now("2026-11-26 10:00"))["open"])    # Thanksgiving: NYSE only
        self.assertFalse(alerts.market_status(alerts.parse_now("2027-01-04 10:00"))["calendar_known"])

    def test_us_symbols_keep_the_nyse_clock(self):
        alerts.use_market([SYM])
        self.assertFalse(alerts.use_market(["TSLA"]))
        st = alerts.market_status(alerts.parse_now("2026-10-19 10:15"))
        self.assertEqual((st["open"], st["opens"], st["closes"]), (True, "09:30", "16:00"))
        self.assertEqual(alerts.parse_now("2026-10-19 10:15"), DT(2026, 10, 19, 14, 15))
        self.assertFalse(alerts.market_status(alerts.parse_now("2026-11-26 10:00"))["open"])   # Thanksgiving

    def test_one_run_one_market(self):
        for mod, err in ((entry, entry.EntryError), (exitp, exitp.PlanError), (alerts, alerts.AlertError),
                         (check, check.RiskError), (scan, scan.ScanError), (tm, tm.TMError),
                         (size, size.SizeError), (ticket, ticket.TicketError)):
            with self.assertRaises(err):
                mod.use_market(["TSLA", SYM])

    def test_the_clock_command(self):
        code, out, _ = run(alerts, ["clock", SYM, "--now", "2026-11-16 10:00"])
        self.assertEqual(code, 0)
        self.assertIn("India 2026-11-16 10:00 (Monday): NSE OPEN, regular session.", out)
        self.assertIn("Today's session: 09:15 to 15:30.", out)
        code, out, _ = run(alerts, ["clock", "--now", "2026-10-19 10:15"])
        self.assertIn("New York 2026-10-19 10:15 (Monday): NYSE OPEN", out)


class Symbols(unittest.TestCase):
    def test_ns_symbols_go_to_yahoo_as_they_are(self):
        self.assertEqual(entry.yahoo_symbol("reliance.ns"), SYM)
        self.assertIn("/chart/RELIANCE.NS?", entry.chart_path(SYM, "1d", "5m"))
        self.assertEqual(scan.to_yahoo(SYM), SYM)
        self.assertEqual(scan.from_yahoo("BAJAJ-AUTO.NS"), "BAJAJ-AUTO.NS")
        self.assertIn("symbols=RELIANCE.NS,TCS.NS&", scan.spark_path([SYM, "tcs.ns"], "1d", "5m"))
        self.assertIn("/chart/RELIANCE.NS?", alerts.yahoo_url(SYM))
        self.assertIn("/chart/RELIANCE.NS?", tm.chart_url(SYM))
        self.assertEqual(news.yahoo_symbol(SYM), SYM)

    def test_an_ampersand_is_escaped_in_the_url_only(self):
        self.assertEqual(entry.yahoo_symbol("M&M.NS"), "M&M.NS")
        self.assertIn("/chart/M%26M.NS?", entry.chart_path("M&M.NS", "1d", "5m"))
        self.assertIn("symbols=M%26M.NS,TCS.NS&", scan.spark_path(["M&M.NS", "TCS.NS"], "1d", "5m"))
        self.assertIn("/chart/M%26M.NS?", alerts.yahoo_url("M&M.NS"))

    def test_us_symbols_are_rewritten_as_before(self):
        self.assertEqual(entry.yahoo_symbol("brk.b"), "BRK-B")
        self.assertEqual(scan.to_yahoo("BRK.B"), "BRK-B")
        self.assertEqual(scan.from_yahoo("BRK-B"), "BRK.B")
        self.assertEqual(news.yahoo_symbol("BRK.B"), "BRK-B")
        self.assertIn("/chart/BRK-B?", tm.chart_url("brk.b"))


class Entry(Files):
    def check(self, now, *more):
        f = self.write("RELIANCE.NS.json", chart_doc(morning()))
        return run(entry, ["check", SYM, "--offline", f, "--now", now, "--config", self.path("none.json")] + list(more))

    def test_the_range_is_915_to_930_and_the_breakout_triggers(self):
        code, out, _ = self.check("2026-11-16 09:45")
        self.assertEqual(code, 0, out)
        self.assertIn("RELIANCE.NS  Mon 2026-11-16 09:45 IST  opening-range breakout", out)
        self.assertIn("Opening range 9:15-9:30: high Rs 1498.00, low Rs 1490.00 (3 of 3 bars).", out)
        self.assertIn("TRIGGERED 9:40 AM at Rs 1500.00: the 9:35 bar (bar 4) closed above the range high", out)
        self.assertNotIn("$", out)                                    # rupees on an NSE run

    def test_the_entry_window_is_0930_to_1500(self):
        code, out, _ = self.check("2026-11-16 09:45", "--json")
        res = json.loads(out)
        self.assertEqual((res["opens"], res["closes"]), ("09:15", "15:30"))
        self.assertEqual((res["no_entries_before"], res["no_entries_after"]), ("09:30", "15:00"))
        # the top-level times are New York times: an NSE run reads the "nse" block instead
        cfg = self.write("config.json", {"no_entries_before": "09:45", "no_entries_after": "15:30",
                                         "nse": {"no_entries_after": "14:30"}})
        f = self.write("RELIANCE.NS.json", chart_doc(morning()))
        code, out, _ = run(entry, ["check", SYM, "--offline", f, "--now", "2026-11-16 09:45", "--config", cfg, "--json"])
        res = json.loads(out)
        self.assertEqual((res["no_entries_before"], res["no_entries_after"]), ("09:30", "14:30"))

    def test_before_the_open_and_on_a_holiday(self):
        code, out, _ = self.check("2026-11-16 09:10")
        self.assertEqual(code, 1)
        self.assertIn("NOT OPEN YET  the NSE opens at 9:15 and the 15-minute range is set at 9:30.", out)
        code, out, _ = self.check("2026-11-24 10:00")
        self.assertIn("the NSE is closed today (NSE holiday: Prakash Gurpurb Sri Guru Nanak Dev)", out)
        self.assertIn("Next open: 2026-11-25 09:15 India.", out)


class Exit(Files):
    def plan(self, *more):
        return run(exitp, ["plan", "--symbol", SYM, "--entry", "1500", "--or-high", "1498", "--or-low", "1490",
                           "--date", "2026-11-16", "--time", "9:40 AM", "--now", "2026-11-16 09:41"] + list(more))

    def test_flat_by_is_1515(self):
        code, out, err = self.plan("--config", self.path("none.json"))
        self.assertEqual(code, 0, err)
        self.assertIn("Flat by       15:15 IST, win or lose: no overnight hold", out)
        code, out, _ = self.plan("--config", CFG_PATH, "--json")      # the shipped example config
        self.assertEqual(json.loads(out)["flat_by"], "15:15")

    def test_the_new_york_flat_by_is_not_used_and_the_nse_block_is(self):
        cfg = self.write("config.json", {"flat_by": "15:55"})
        self.assertEqual(json.loads(self.plan("--config", cfg, "--json")[1])["flat_by"], "15:15")
        cfg = self.write("config.json", {"flat_by": "15:55", "nse": {"flat_by": "15:10"}})
        self.assertEqual(json.loads(self.plan("--config", cfg, "--json")[1])["flat_by"], "15:10")

    def test_a_flat_by_at_or_after_the_close_is_refused(self):
        code, _, err = self.plan("--config", self.path("none.json"), "--flat-by", "15:30")
        self.assertEqual(code, 1)
        self.assertIn("--flat-by 15:30 is at or after the 3:30 PM close", err)
        cfg = self.write("config.json", {"nse": {"flat_by": "15:45"}})
        code, _, err = self.plan("--config", cfg)
        self.assertEqual(code, 1)
        self.assertIn("flat_by 15:45 is at or after the NSE's 3:30 PM close", err)

    def test_a_us_plan_still_gets_1555(self):
        code, out, err = run(exitp, ["plan", "--symbol", "TSLA", "--entry", "364.18", "--or-high", "362.18",
                                     "--or-low", "354.47", "--date", "2026-10-19", "--time", "10:15 AM",
                                     "--now", "2026-10-19 10:16", "--config", CFG_PATH, "--json"])
        plan = json.loads(out)
        self.assertEqual(plan["flat_by"], "15:55", err)
        self.assertEqual((plan["stop"], plan["target"]), (358.32, 375.9))     # to the cent, as before
        self.assertNotIn("tick", plan)

    def tick_plan(self, entry_px, high, low, *more):
        code, out, err = run(exitp, ["plan", "--symbol", SYM, "--entry", str(entry_px), "--or-high", str(high),
                                     "--or-low", str(low), "--date", "2026-11-16", "--time", "9:40 AM",
                                     "--now", "2026-11-16 09:41", "--config", self.path("none.json"), "--json"]
                             + list(more))
        self.assertEqual(code, 0, err)
        return json.loads(out)

    def test_the_stop_and_target_sit_on_the_nse_tick(self):
        self.assertEqual([float(exitp.nse_tick(p)) for p in (187.44, 250, 1000, 1000.05, 5000, 7500, 10919, 25000)],
                         [0.01, 0.05, 0.05, 0.10, 0.10, 0.50, 1.00, 5.00])
        p = self.tick_plan(2442, 2434.90, 2410.50, "--target", "1R")           # the midpoint is on the tick already
        self.assertEqual((p["stop"], p["target"], p["tick"], p["reward_risk"]), (2422.7, 2461.3, 0.1, 1.0))
        p = self.tick_plan(1500, 1498.05, 1490.20, "--target", "1R")           # midpoint 1494.125: down to 1494.10
        self.assertEqual((p["stop"], p["target"], p["risk_per_share"]), (1494.1, 1505.9, 5.9))
        self.assertIn("rounded down to the 0.10 tick", p["stop_detail"])
        p = self.tick_plan(1500, 1498.05, 1490.20, "--target", "1.5R")         # 1508.85: an R target rounds up
        self.assertEqual(p["target"], 1508.9)
        self.assertGreaterEqual(p["reward_risk"], 1.5)
        p = self.tick_plan(187.44, 187.30, 186.40, "--target", "1R")           # under 250 the tick is the paisa
        self.assertEqual((p["stop"], p["tick"]), (186.85, 0.01))
        p = self.tick_plan(1500, 1498.05, 1490.20, "--target", "1R", "--tick", "0.05")
        self.assertEqual((p["stop"], p["tick"]), (1494.1, 0.05))
        p = self.tick_plan(1500, 1498.05, 1490.25, "--target", "1R", "--tick", "0.05")   # 1494.15 is on a 0.05 tick
        self.assertEqual(p["stop"], 1494.15)


def order(sym=SYM, qty=1, entry_px=1500.0, stop=1495.0, target=1506.0):
    return {"symbol": sym, "side": "buy", "qty": str(qty), "type": "market", "time_in_force": "day",
            "order_class": "bracket", "take_profit_limit_price": "%.2f" % target,
            "stop_loss_stop_price": "%.2f" % stop, "plan": {"entry": entry_px, "stop": stop, "target": target}}


class Risk(unittest.TestCase):
    def cfg(self):
        with open(CFG_PATH) as fh:
            return json.load(fh)

    def at(self, text, orders=None):
        check.use_market([SYM])
        return check.check(orders or [order()], self.cfg(), now=check.parse_now(text))

    def why(self, text):
        res = self.at(text)
        return res["results"][0]["verdict"], " | ".join(res["results"][0]["reasons"])

    def test_the_window_runs_on_india_time(self):
        res = self.at("2026-11-16 10:00")
        self.assertEqual(res["results"][0]["verdict"], "PASS", res["results"][0]["reasons"])
        self.assertEqual((res["date"], res["now_new_york"]), ("2026-11-16", "2026-11-16 10:00"))
        self.assertEqual(self.why("2026-11-16 09:20"),
                         ("BLOCK", "window: no new entries before 09:30 India (it is 09:20)"))
        self.assertEqual(self.why("2026-11-16 15:05"),
                         ("BLOCK", "window: no new entries after 15:00 India (it is 15:05)"))
        self.assertIn("the session is 09:15 to 15:30", self.why("2026-11-16 15:31")[1])
        self.assertIn("NSE holiday: Prakash Gurpurb Sri Guru Nanak Dev", self.why("2026-11-24 10:00")[1])
        self.assertIn("check nseindia.com", " ".join(self.at("2027-01-04 10:00")["warnings"]))

    def test_ns_tickers_are_stock_tickers(self):
        for sym in (SYM, "M&M.NS", "BAJAJ-AUTO.NS", "360ONE.NS"):
            res = self.at("2026-11-16 10:00", [order(sym)])
            self.assertEqual(res["results"][0]["verdict"], "PASS", (sym, res["results"][0]["reasons"]))

    def test_a_mixed_file_is_refused_and_a_us_one_is_unchanged(self):
        with self.assertRaises(check.RiskError):
            check.check([order(), order("TSLA", 1, 364.18, 358.32, 370.04)], self.cfg())
        check.use_market(["TSLA"])
        res = check.check([order("TSLA", 8, 364.18, 358.32, 370.04)], self.cfg(), now=check.parse_now("2026-10-19 10:15"))
        self.assertEqual(res["results"][0]["verdict"], "PASS", res["results"][0]["reasons"])
        res = check.check([order("TSLA", 8, 364.18, 358.32, 370.04)], self.cfg(), now=check.parse_now("2026-10-19 09:40"))
        self.assertIn("no new entries before 09:45 New York", " | ".join(res["results"][0]["reasons"]))


def sessions_text(n=25, last_day=DAY, last_bars=5):
    """n NSE sessions before last_day the way Yahoo sends them (75 stamps from 09:15 to
    15:25, the 15:20 bar always empty), then last_day's first bars."""
    rng = random.Random(7)
    days, d = [], last_day
    while len(days) < n:
        d -= datetime.timedelta(days=1)
        if d.weekday() < 5:
            days.append(d)
    bars, px = [], 1480.0
    for day in sorted(days) + [last_day]:
        for k in range(last_bars if day == last_day else 75):
            start = DT.combine(day, datetime.time(9, 15)) + datetime.timedelta(minutes=5 * k)
            stamp = ts(day, start.strftime("%H:%M"))
            if start.strftime("%H:%M") == "15:20":
                bars.append((stamp, None, None, None, None, None))
                continue
            o = px
            c = round(o * (1 + rng.uniform(-0.002, 0.002)), 2)
            bars.append((stamp, o, round(max(o, c) + 0.6, 2), round(min(o, c) - 0.6, 2), c, 5000))
            px = c
    return json.dumps(chart_doc(bars)), bars[-1]


class TimeMachine(unittest.TestCase):
    def test_the_replay_session_is_72_bars_to_the_1515_flat_by(self):
        text, last = sessions_text()
        plan = tm.normalize_plan(dict(PLAN, entry=last[4], stop=last[4] - 5, target=last[4] + 6))
        self.assertEqual((tm.SESSION_BARS, plan["entry_time"], plan["entry_bar"]), (72, "9:40 AM", 4))
        doc = tm.time_machine(text, plan, tm.parse_now("2026-11-16 09:41"), replays=200)
        m = doc["mc"]
        # Yahoo's empty 15:20 bars do not cost a session: the replay stops at 15:15
        self.assertEqual((m["until"], m["pool_sessions"], m["bars_left"]), ("15:15", 25, 67))
        self.assertEqual((m["band_times"][0], m["band_times"][-1]), ("09:40", "15:15"))
        self.assertTrue(doc["data"]["last_bar"].endswith("09:35 IST"), doc["data"]["last_bar"])
        self.assertEqual(doc["data"]["short_sessions_left_out"], [])
        self.assertIn("still open at 3:15 PM", "\n".join(tm.report(doc)))
        early = tm.time_machine(text, plan, tm.parse_now("2026-11-16 09:41"), replays=200, until="14:00")
        self.assertEqual((early["mc"]["until"], early["mc"]["band_times"][-1]), ("14:00", "14:00"))
        with self.assertRaises(tm.TMError) as cm:
            tm.time_machine(text, plan, tm.parse_now("2026-11-16 09:41"), replays=200, until="15:20")
        self.assertIn("no later than 3:15 PM", str(cm.exception))

    def test_the_entry_must_leave_bars_before_1515(self):
        with self.assertRaises(tm.TMError) as cm:
            tm.normalize_plan(dict(PLAN, entry_time="3:15 PM", entry_bar=None))
        self.assertIn("between 9:20 AM and 3:10 PM", str(cm.exception))

    def test_a_us_plan_is_still_78_bars(self):
        tm.normalize_plan(PLAN)
        p = tm.normalize_plan(dict(PLAN, symbol="TSLA", entry_time="10:15 AM", entry_bar=8))
        self.assertEqual((tm.SESSION_BARS, tm.OPEN_MIN, tm.CLOSE_MIN, p["entry_bar"]), (78, 570, 960, 8))


class Alerts(Files):
    def test_the_flat_by_alert_rings_at_1515_india_time(self):
        rules = alerts.rules_from_plan(PLAN)
        self.assertEqual([(r["id"], r.get("at")) for r in rules][-1], ("reliance.ns-flat-by", "15:15"))
        flat = [rules[-1]]

        def at(text, state=None):
            now = alerts.parse_now(text)
            return alerts.evaluate(flat, {}, alerts.market_status(now), state, now)
        self.assertEqual(at("2026-11-16 15:14")[0], [])
        rings, state = at("2026-11-16 15:15")
        self.assertIn("Flat by close: it is 15:15 India (set for 15:15), the market closes at 15:30.",
                      rings[0]["message"])
        self.assertEqual(at("2026-11-16 15:20", state)[0], [])            # once a day

    def test_add_from_plan_and_check(self):
        plan = self.write("plan.json", PLAN)
        rules, state = self.path("alerts.json"), self.path("state.json")
        code, out, err = run(alerts, ["add", "--from-plan", "--plan", plan, "--rules", rules, "--state", state,
                                      "--config", CFG_PATH])
        self.assertEqual(code, 0, err)
        with open(rules) as fh:
            self.assertEqual([r.get("at") for r in json.load(fh)["rules"]], [None, None, "15:15"])
        self.write("yahoo-RELIANCE.NS.json", {"chart": {"error": None, "result": [{"meta": {
            "symbol": SYM, "regularMarketPrice": 1501.0, "previousClose": 1480.0}, "indicators": {"quote": [{}]}}]}})
        code, out, err = run(alerts, ["check", "--rules", rules, "--state", state, "--no-write",
                                      "--offline", self.tmp.name, "--now", "2026-11-16 15:16"])
        self.assertEqual(code, 0, err)
        self.assertIn("NSE OPEN (2026-11-16 15:16 India, regular session).", out)
        self.assertIn("ALERT Flat by close: it is 15:16 India (set for 15:15)", out)

    def test_the_opening_bell(self):
        rules, state = self.path("alerts.json"), self.path("state.json")
        run(alerts, ["add", "--opening-bell", "--symbol", SYM, "--rules", rules, "--state", state])
        code, out, _ = run(alerts, ["check", "--rules", rules, "--state", state, "--no-write",
                                    "--now", "2026-11-16 09:15"])
        self.assertIn("ALERT Opening bell: the NSE is open (2026-11-16 09:15 India).", out)


class BudgetAndBroker(Files):
    def test_the_size_report_is_flat_by_1515(self):
        plan = self.write("plan.json", PLAN)
        argv = ["--plan", plan, "--config", CFG_PATH, "--portfolio", self.path("none.json"),
                "--prices", self.write("prices.json", {}), "--now", "2026-11-16 09:41"]
        code, out, err = run(size, argv)
        self.assertEqual(code, 0, err)
        self.assertIn("Flat by 15:15 India:", out)
        sizing = json.loads(run(size, argv + ["--json"])[1])["sizing"]
        self.assertEqual((sizing["qty"], sizing["flat_by"]), (2, "15:15"))    # 4,000 max order / 1,500 a share
        # the plan's date is an India date: 09:41 IST on the 16th is still the 15th in New York
        self.assertEqual(sizing["date"], "2026-11-16")

    def test_the_log_stamp_is_plus_0530(self):
        ticket.use_market([SYM])
        self.assertEqual(ticket.ny_iso(DT(2026, 11, 16, 4, 45)), "2026-11-16T10:15:00+05:30")
        ticket.use_market(["TSLA"])
        self.assertEqual(ticket.ny_iso(DT(2026, 10, 19, 14, 15)), "2026-10-19T10:15:00-04:00")

    def test_flatten_closes_by_1515(self):
        orders = self.path("orders.json")
        code, out, err = run(ticket, ["flatten", "--symbol", SYM, "--qty", "2", "--orders", orders,
                                      "--config", CFG_PATH, "--plan", self.path("none.json"),
                                      "--now", "2026-11-16 15:10"])
        self.assertEqual(code, 0, err)
        self.assertIn("(flat by 15:15 India).", out)
        with open(orders) as fh:
            doc = json.load(fh)
        self.assertEqual(doc["source"], "ticket.py flatten RELIANCE.NS on 2026-11-16")
        self.assertIn("flat by 15:15 India", doc["orders"][0]["why"])


class Zerodha(Files):
    """A .NS order is ticketed for Zerodha Kite: an intraday entry, then a stop-loss order."""

    def setUp(self):
        Files.setUp(self)
        with open(CFG_PATH) as fh:
            self.cfg = json.load(fh)
        self.orders = self.write("orders.json", {"orders": [dict(order(SYM, 2), why="orb")]})
        self.state = self.path("state.json")
        self.risk = self.path("risk.json")

    def args(self, cmd, *more, **kw):
        cfg = self.write("config.json", dict(self.cfg, **kw))
        return [cmd, "--orders", self.orders, "--config", cfg, "--risk", self.risk, "--state", self.state,
                "--now", "2026-11-16 10:00"] + list(more)

    def passed(self):
        """trader-risk's PASS for the orders file, the way check.py records it."""
        with open(self.orders) as fh:
            orders = json.load(fh)["orders"]
        check.use_market([SYM])
        self.write("risk.json", check.check(orders, self.cfg, now=check.parse_now("2026-11-16 10:00")))

    def test_the_place_order_arguments(self):
        entry_call, stop_call = ticket.kite_orders(order(SYM, 2, 1500.0, 1495.0, 1506.0))
        self.assertEqual(entry_call, {"variety": "regular", "exchange": "NSE", "tradingsymbol": "RELIANCE",
                                      "transaction_type": "BUY", "quantity": 2, "order_type": "MARKET",
                                      "product": "MIS", "validity": "DAY", "tag": "daytrader"})
        # the stop-loss: trigger at the plan's stop, limit 0.5% under it, down to the 0.10 tick
        self.assertEqual(stop_call, {"variety": "regular", "exchange": "NSE", "tradingsymbol": "RELIANCE",
                                     "transaction_type": "SELL", "quantity": 2, "order_type": "SL",
                                     "trigger_price": 1495.0, "price": 1487.5, "product": "MIS",
                                     "validity": "DAY", "tag": "daytrader"})
        limit = dict(order("M&M.NS", 1, 3000.0, 2990.0, 3012.0), type="limit", limit_price="3000.00")
        calls = ticket.kite_orders(limit, {"nse": {"stop_limit_buffer_pct": 1}})
        self.assertEqual((calls[0]["tradingsymbol"], calls[0]["order_type"], calls[0]["price"]), ("M&M", "LIMIT", 3000.0))
        self.assertEqual(calls[1]["price"], 2960.1)                      # 2990 less 1%
        low = ticket.kite_orders(dict(order("TATASTEEL.NS", 10, 187.44, 186.85, 188.03)))
        self.assertEqual(low[1]["price"], 185.91)                        # under 250 the tick is 0.01
        knob = dict(order(SYM, 1, 1500.0, 1494.15, 1506.0))
        knob["plan"]["tick"] = 0.05                                      # trader-exit --tick 0.05 comes through
        self.assertEqual(ticket.kite_orders(knob)[1]["price"], 1486.65)
        sell = ticket.kite_orders({"symbol": SYM, "side": "sell", "qty": "2", "type": "market"})
        self.assertEqual((len(sell), sell[0]["transaction_type"], sell[0]["order_type"]), (1, "SELL", "MARKET"))
        for bad in ({"symbol": SYM, "side": "buy", "notional": "500", "type": "market"},
                    {"symbol": SYM, "side": "buy", "qty": "1", "type": "trailing_stop"}):
            with self.assertRaises(ticket.TicketError):
                ticket.kite_orders(bad)

    def test_who_gets_the_order(self):
        self.assertEqual(ticket.broker_of(self.cfg, {"symbol": SYM}), "kite")
        self.assertEqual(ticket.broker_of(self.cfg, {"symbol": "TSLA"}), "alpaca")
        self.assertEqual(ticket.broker_of({"broker": "ibkr"}, {"symbol": "TSLA"}), "ibkr")
        self.assertEqual(ticket.broker_of({"broker": "ibkr"}, {"symbol": SYM}), "kite")
        self.assertEqual(ticket.broker_of({"nse": {"broker": "other"}}, {"symbol": SYM}), "other")

    def test_practice_mode_places_nothing(self):
        self.passed()
        code, out, err = run(ticket, self.args("show"))
        self.assertEqual(code, 0, err)
        self.assertIn("ORDER 1 of 1, PRACTICE (\"paper\": true), Zerodha Kite", out)
        self.assertIn("Practice only: Zerodha has no paper account, so nothing is placed", out)
        self.assertIn("--broker-id practice --filled-qty 2", out)
        self.assertNotIn("place_order", out)
        self.assertNotIn("Alpaca", out)
        doc = json.loads(run(ticket, self.args("show", "--index", "1", "--json"))[1])
        self.assertEqual((doc["broker"], doc["practice"], doc["tool"], doc["tool_input"]), ("kite", True, None, None))
        code, out, _ = run(ticket, self.args("approve", "--index", "1", "--reply", "yes"))
        self.assertEqual(code, 0)
        self.assertIn("Practice mode: nothing goes to Zerodha, do not place it in Kite either.", out)
        self.assertNotIn("place_order", out)
        with open(self.state) as fh:
            rec = json.load(fh)["orders"][-1]
        self.assertEqual((rec["broker"], rec["paper"], rec["at"]), ("kite", True, "2026-11-16T10:00:00+05:30"))

    def test_a_live_ticket_shows_both_ways(self):
        self.passed()
        code, out, err = run(ticket, self.args("show", paper=False))
        self.assertEqual(code, 0, err)
        self.assertIn("ORDER 1 of 1, LIVE ACCOUNT, REAL MONEY, Zerodha Kite", out)
        self.assertIn("Way 1, yourself in the Kite app:\n    NSE RELIANCE, Intraday (MIS), BUY 2, Market", out)
        self.assertIn("when it has filled: NSE RELIANCE, Intraday (MIS), SELL 2, SL, trigger 1495.00, price 1487.50", out)
        self.assertIn("Way 2, your own Kite connector: Claude calls place_order with exactly:", out)
        self.assertIn('"tradingsymbol": "RELIANCE"', out)
        self.assertIn("Zerodha's API refuses a plain market order", out)
        self.assertIn("for way 2 make it a limit order (size.py --limit).", out)
        self.assertIn("No order waits at the target 1506.00: trader-alerts rings there", out)
        self.assertIn("be flat by 15:15.", out)
        doc = json.loads(run(ticket, self.args("show", "--index", "1", "--json", paper=False))[1])
        self.assertEqual((doc["tool"], doc["practice"], len(doc["tool_input"])), ("place_order", False, 2))
        code, out, _ = run(ticket, self.args("approve", "--index", "1", "--reply", "yes", paper=False))
        self.assertIn("Now place it. In the Kite app: NSE RELIANCE, Intraday (MIS), BUY 2, Market.", out)
        self.assertIn("Confirm it with get_orders or get_positions", out)
        code, out, _ = run(ticket, self.args("show", paper=False))             # approved: still how to place it
        self.assertIn("APPROVED by you at 2026-11-16T10:00:00+05:30, waiting for the order to be placed", out)
        self.assertIn("Way 1, yourself in the Kite app:", out)

    def test_a_ticket_that_is_not_ready_gives_no_way_to_place_it(self):
        code, out, _ = run(ticket, self.args("show", paper=False))             # trader-risk has not run
        self.assertEqual(code, 1)
        self.assertIn("NOT READY: trader-risk has not checked these orders", out)
        self.assertNotIn("Way 1", out)
        self.assertNotIn("place_order", out)

    def test_flatten_for_zerodha(self):
        argv = ["flatten", "--symbol", SYM, "--qty", "2", "--limit", "1499.5", "--orders", self.orders,
                "--plan", self.path("none.json"), "--now", "2026-11-16 15:10", "--config"]
        code, out, err = run(ticket, argv + [CFG_PATH])
        self.assertEqual(code, 0, err)
        self.assertIn("Practice mode: nothing is placed at Zerodha.", out)
        self.assertNotIn("Cancel the stop-loss", out)                     # no real order is waiting
        code, out, err = run(ticket, argv + [self.write("live.json", dict(self.cfg, paper=False))])
        self.assertEqual(code, 0, err)
        self.assertIn("Cancel the stop-loss order still waiting at Zerodha first", out)
        self.assertNotIn("Alpaca", out)
        with open(self.orders) as fh:
            sell = json.load(fh)["orders"][0]
        self.assertEqual((sell["type"], sell["limit_price"]), ("limit", "1499.50"))
        self.assertIn("get_positions", sell["why"])
        self.assertEqual(ticket.kite_orders(sell)[0]["price"], 1499.5)

    def test_a_us_ticket_is_still_alpaca(self):
        us = self.write("us.json", {"orders": [order("TSLA", 8, 364.18, 358.32, 370.04)]})
        code, out, _ = run(ticket, ["show", "--orders", us, "--config", CFG_PATH, "--risk", self.risk,
                                    "--state", self.state, "--now", "2026-10-19 10:15"])
        self.assertIn("ORDER 1 of 1, PAPER account, Alpaca", out)
        self.assertIn("Claude will call place_stock_order with exactly:", out)
        self.assertNotIn("Zerodha", out)


class Costs(Files):
    """Zerodha's intraday charges: every .NS plan, size and report shows the result after them."""

    def test_the_charges_on_one_trade_to_the_paisa(self):
        # buy 1 TCS at 2442.00, sell at 2461.30 (zerodha.com/charges, equity intraday, read 2026-11-15)
        c = ticket.nse_charges(2442.0, 2461.3)
        self.assertEqual(c, {"brokerage": 1.47,      # 0.03% of 2442.00 + 0.03% of 2461.30
                             "stt": 0.62,            # 0.025% of the 2461.30 sold
                             "exchange": 0.15,       # 0.00307% of the 4903.30 traded
                             "sebi": 0.0,            # Rs 10 a crore: half a paisa here
                             "stamp": 0.07,          # 0.003% of the 2442.00 bought
                             "gst": 0.29,            # 18% of brokerage + exchange + SEBI
                             "total": 2.6})
        big = ticket.nse_charges(100000.0, 101000.0)                 # 0.03% would be 30: the Rs 20 cap applies
        self.assertEqual(big["brokerage"], 40.0)
        self.assertEqual(ticket.nse_charges(2442.0, 2461.3, {"brokerage_pct": 0})["brokerage"], 0.0)

    def test_the_three_tools_and_the_example_config_agree(self):
        self.assertEqual(exitp.NSE_CHARGES, size.NSE_CHARGES)
        self.assertEqual(size.NSE_CHARGES, ticket.NSE_CHARGES)
        for mod in (exitp, size):
            self.assertEqual(mod.nse_charges(2442.0, 2461.3), ticket.nse_charges(2442.0, 2461.3))
        with open(os.path.join(ROOT, "trader-budget", "config.nse.example.json")) as fh:
            cfg = json.load(fh)
        self.assertEqual({k: float(v) for k, v in cfg["nse"]["charges"].items()}, ticket.NSE_CHARGES)
        self.assertIs(cfg["paper"], True)
        self.assertEqual((cfg["nse"]["flat_by"], cfg["nse"]["broker"]), ("15:15", "kite"))

    def plan(self, *more):
        return run(exitp, ["plan", "--symbol", "TCS.NS", "--entry", "2442", "--or-high", "2434.90", "--or-low",
                           "2410.50", "--date", "2026-11-16", "--time", "9:40 AM", "--target", "1R",
                           "--now", "2026-11-16 09:41"] + list(more))

    def test_a_plan_shows_the_reward_to_risk_after_costs(self):
        code, out, err = self.plan("--config", self.path("none.json"), "--json")
        self.assertEqual(code, 0, err)
        k = json.loads(out)["costs"]
        # risk 19.30 a share: +19.30 or -19.30 before costs, +16.70 or -21.88 after
        # (a sell at the 2422.70 stop costs 2.58: brokerage 1.46, STT 0.61, exchange 0.15, stamp 0.07, GST 0.29)
        self.assertEqual((k["per_share_at_target"], k["per_share_at_stop"]), (2.6, 2.58))
        self.assertEqual((k["net_at_target"], k["net_at_stop"], k["reward_risk_after_costs"]), (16.7, -21.88, 0.76))
        text = self.plan("--config", self.path("none.json"))[1]
        self.assertIn("After costs   about Rs 2.60 a share for the buy and the sell (Zerodha, equity intraday): "
                      "+Rs 16.70 at the target,", text)
        self.assertIn("-Rs 21.88 at the stop, reward:risk 0.76", text)
        free = self.write("config.json", {"nse": {"charges": {"brokerage_pct": 0, "stt_sell_pct": 0, "exchange_pct": 0,
                                                             "sebi_per_crore": 0, "stamp_buy_pct": 0}}})
        self.assertEqual(json.loads(self.plan("--config", free, "--json")[1])["costs"]["reward_risk_after_costs"], 1.0)

    def test_a_us_plan_has_no_costs_block(self):
        code, out, _ = run(exitp, ["plan", "--symbol", "TSLA", "--entry", "364.18", "--or-high", "362.18", "--or-low",
                                   "354.47", "--date", "2026-10-19", "--now", "2026-10-19 10:16",
                                   "--config", self.path("none.json")])
        self.assertNotIn("After costs", out)
        self.assertIn("Entry         $364.18", out)                   # dollars, as before

    def test_the_size_report_shows_the_costs_in_rupees(self):
        plan = self.write("plan.json", dict(PLAN, symbol="TCS.NS", entry=2442.0, stop=2422.7, target=2461.3,
                                            opening_range={"high": 2434.9, "low": 2410.5, "minutes": 15}))
        argv = ["--plan", plan, "--config", os.path.join(ROOT, "trader-budget", "config.nse.example.json"),
                "--portfolio", self.path("none.json"), "--prices", self.write("prices.json", {}),
                "--now", "2026-11-16 09:41"]
        code, out, err = run(size, argv)
        self.assertEqual(code, 0, err)
        # Rs 500 max loss / 19.30 risk = 25 shares, but the position cap and the max order stop at 15
        self.assertIn("Size: 15 shares of TCS.NS = Rs 36,630 at 2442.00. Max loss at the stop: 15 x 19.30 = Rs 289.50.", out)
        # 36,630.00 bought, 36,919.50 sold at the target: brokerage 22.06, STT 9.23, exchange 2.26, SEBI 0.07,
        # stamp 1.10, GST 4.39 = 39.11. Sold at the stop for 36,340.50 instead: 38.75.
        self.assertIn("Costs (Zerodha, equity intraday, about): Rs 39.11 if the target fills, Rs 38.75 if the stop fills.", out)
        self.assertIn("brokerage Rs 22.06, STT Rs 9.23, exchange and SEBI Rs 2.33, stamp duty Rs 1.10, GST Rs 4.39.", out)
        self.assertIn("After costs: +Rs 250.39 at the target, -Rs 328.25 at the stop.", out)
        self.assertNotIn("$", out)
        k = json.loads(run(size, argv + ["--json"])[1])["sizing"]["costs"]
        self.assertEqual((k["at_target"], k["net_at_target"], k["net_at_stop"]), (39.11, 250.39, -328.25))
        tight = self.write("tight.json", {"budget": 50000, "max_loss_per_trade_usd": 290, "max_order_usd": 40000})
        code, out, _ = run(size, argv[:2] + ["--config", tight] + argv[4:])
        self.assertIn("With costs the loss at the stop is Rs 328.25, over your Rs 290 max loss per trade.", out)


class Report(Files):
    def log(self, *fills, **kw):
        recs = [{"at": d + "T10:00:00+05:30", "date": d, "status": "filled", "symbol": s, "side": side,
                 "qty": str(q), "price": p} for d, s, side, q, p in fills]
        recs += kw.get("extra", [])
        return self.write("broker.json", {"orders": recs})

    def test_before_costs_costs_and_after_costs(self):
        entry_rec = {"at": "2026-11-13T09:40:00+05:30", "date": "2026-11-13", "status": "placed", "symbol": "TCS.NS",
                     "side": "buy", "kind": "entry", "max_loss": 19.3}
        state = self.log(("2026-11-13", "TCS.NS", "buy", 1, 2442.0), ("2026-11-13", "TCS.NS", "sell", 1, 2461.3),
                         ("2026-11-16", "INFY.NS", "buy", 10, 1149.0), ("2026-11-16", "INFY.NS", "sell", 10, 1143.0),
                         ("2026-11-16", SYM, "buy", 2, 1500.0), extra=[entry_rec])
        argv = ["report", "--state", state, "--config", self.path("none.json"), "--now", "2026-11-16 15:20"]
        code, out, err = run(ticket, argv)
        self.assertEqual(code, 0, err)
        self.assertIn("Trade report: 2 closed trades, 2026-11-13 to 2026-11-16.", out)
        self.assertIn("2026-11-13  TCS.NS        1 x 2442.00 -> 2461.30   before costs +Rs 19.30   costs Rs 2.60   "
                      "after costs +Rs 16.70   +0.87R", out)
        # INFY: 11,490 bought, 11,430 sold: brokerage 6.88, STT 2.86, exchange 0.70, SEBI 0.02, stamp 0.34, GST 1.37
        self.assertIn("2026-11-16  INFY.NS       10 x 1149.00 -> 1143.00   before costs -Rs 60   costs Rs 12.17   "
                      "after costs -Rs 72.17", out)
        self.assertIn("Before costs: -Rs 40.70. Costs: Rs 14.77. After costs: -Rs 55.47.", out)
        self.assertIn("Won 1, lost 1: win rate 50%. Average win Rs 16.70, average loss Rs 72.17, biggest loss Rs 72.17.", out)
        self.assertIn("Average result a trade, after costs: -Rs 27.73.", out)
        self.assertIn("Still open: 2 shares of RELIANCE.NS bought on 2026-11-16 with no sell recorded", out)
        self.assertNotIn("$", out)
        doc = json.loads(run(ticket, argv + ["--json"])[1])
        self.assertEqual((doc["summary"]["trades"], doc["summary"]["net"], doc["trades"][0]["r"]), (2, -55.47, 0.87))
        code, out, _ = run(ticket, argv + ["--days", "1"])            # today only
        self.assertIn("Trade report: 1 closed trade, 2026-11-16 to 2026-11-16.", out)

    def test_no_trades_and_a_us_log(self):
        code, out, _ = run(ticket, ["report", "--state", self.path("none.json"), "--config", self.path("none.json")])
        self.assertEqual(code, 1)
        self.assertIn("No closed trades in", out)
        us = self.log(("2026-10-19", "TSLA", "buy", 8, 364.2), ("2026-10-19", "TSLA", "sell", 8, 370.04))
        code, out, _ = run(ticket, ["report", "--state", us, "--config", self.path("none.json")])
        self.assertIn("before costs +$46.72   costs $0   after costs +$46.72", out)      # dollars, no Zerodha charges


class Printing(Files):
    def test_a_character_the_console_cannot_print_does_not_crash(self):
        class Cp1252(io.StringIO):
            encoding = "cp1252"

            def write(self, text):
                text.encode("cp1252")             # what a Windows pipe does: raises on the rupee sign
                return io.StringIO.write(self, text)
        for mod in (entry, exitp, alerts, check, scan, tm, size, ticket, news):
            mod.use_market(["TSLA"])
            real, out = Cp1252(), None
            out = mod._Out(real)
            out.write(u"price ₹2,442 ☃ $5\n")              # a rupee sign and a snowman
            self.assertEqual(real.getvalue(), "price Rs 2,442 ? $5\n", mod.__name__)
        news.use_market([SYM])
        real = Cp1252()
        news._Out(real).write(u"gains ₹500 or $6\n")
        self.assertEqual(real.getvalue(), "gains Rs 500 or Rs 6\n")
        news.use_market(["TSLA"])


class Universe(Files):
    def test_a_nifty_list_becomes_ns_symbols(self):
        nse_dir = os.path.join(ROOT, "tests", "fixtures", "trader-scanner", "nse")   # 7 real rows of the Nifty 50 list
        out_file = self.path("universe.txt")
        code, out, err = run(scan, ["universe", "--nse", "nifty50", "--offline", nse_dir, "--out", out_file])
        self.assertEqual(code, 0, err)
        self.assertIn("NSE nifty50 list: 7 stocks (ordinary shares, series EQ), as .NS symbols.", out)
        with open(out_file, encoding="utf-8") as fh:
            lines = fh.read().splitlines()
        self.assertEqual(lines[0], "BAJAJ-AUTO.NS|Bajaj Auto Ltd.")
        self.assertIn("M&M.NS|Mahindra & Mahindra Ltd.", lines)
        self.assertEqual(scan.symbols_from_file(out_file)[:2], ["BAJAJ-AUTO.NS", "HDFCBANK.NS"])
        self.assertTrue(scan.use_market(scan.symbols_from_file(out_file)))        # a scan of it runs on the NSE clock
        scan.use_market(["TSLA"])
        self.assertEqual(scan.parse_nse_list("Company Name,Industry,Symbol,Series,ISIN Code\nA Ltd.,X,AAA,BE,I1\n"), [])
        with self.assertRaises(scan.ScanError):
            scan.parse_nse_list("Symbol|Security Name\nAAPL|Apple\n")
        code, _, err = run(scan, ["universe", "--nse", "nifty100", "--offline", nse_dir, "--no-write"])
        self.assertIn("no ind_nifty100list.csv in", err)


class Scanner(Files):
    def test_the_opening_range_runs_from_915(self):
        scan.use_market([SYM])
        day, cutoff = scan.orb_window(scan.parse_now("2026-11-16 10:00"), None, 15, datetime.time(15, 0))
        self.assertEqual((day, cutoff), (DAY, DT(2026, 11, 16, 10, 0)))
        with self.assertRaises(scan.ScanError) as cm:
            scan.orb_window(scan.parse_now("2026-11-16 09:25"), None, 15, datetime.time(15, 0))
        self.assertIn("It is 9:25 AM IST: the 15-minute opening range runs 9:15 to 9:30 AM", str(cm.exception))
        with self.assertRaises(scan.ScanError) as cm:
            scan.orb_window(scan.parse_now("2026-11-24 10:00"), None, 15, datetime.time(15, 0))
        self.assertIn("NSE holiday", str(cm.exception))

    def test_an_orb_scan_of_ns_symbols(self):
        f = self.write("bundle.json", {SYM: chart_doc(morning())})
        code, out, err = run(scan, ["orb", "--symbols", SYM, "--offline", f, "--now", "2026-11-16 10:00",
                                    "--config", CFG_PATH, "--no-write", "--json"])
        self.assertEqual(code, 0, err)
        doc = json.loads(out)
        self.assertEqual(doc["as_of"], "2026-11-16 10:00 IST")
        hit = doc["hits"][0]
        self.assertEqual((hit["symbol"], hit["at"], hit["bar_start"], hit["or_high"], hit["or_low"]),
                         (SYM, "9:40 AM", "09:35", 1498.0, 1490.0))
        code, out, err = run(scan, ["orb", "--symbols", SYM, "--offline", f, "--now", "2026-11-16 15:05",
                                    "--config", CFG_PATH, "--no-write"])
        self.assertEqual(code, 1)
        self.assertIn("after 15:00, your last time for new entries", err)      # the "nse" block's cutoff
        code, _, err = run(scan, ["orb", "--symbols", "TSLA," + SYM, "--offline", f, "--now", "2026-11-16 10:00",
                                  "--no-write"])
        self.assertIn("NSE (.NS) and US symbols in one scan", err)


class News(unittest.TestCase):
    def test_times_print_in_india_time_for_ns_tickers(self):
        self.assertTrue(news.use_market([SYM, "TCS.NS"]))
        self.assertEqual(news.to_eastern(DT(2026, 11, 16, 4, 45)), DT(2026, 11, 16, 10, 15))
        self.assertIn("Checked 2026-11-16 10:15 IST.", news.render([], [], DT(2026, 11, 16, 4, 45)))
        self.assertFalse(news.use_market([SYM, "TSLA"]))                   # a mixed list stays on New York time
        self.assertIn("Checked 2026-10-19 10:15 ET.", news.render([], [], DT(2026, 10, 19, 14, 15)))


if __name__ == "__main__":
    unittest.main()
