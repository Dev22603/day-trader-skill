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
        self.assertIn("Opening range 9:15-9:30: high $1498.00, low $1490.00 (3 of 3 bars).", out)
        self.assertIn("TRIGGERED 9:40 AM at $1500.00: the 9:35 bar (bar 4) closed above the range high", out)

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
        self.assertEqual(json.loads(out)["flat_by"], "15:55", err)


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
