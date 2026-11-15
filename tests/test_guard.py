"""trader-guard: the warnings for any trade (shares, MTF, futures, options, pledging)."""

import datetime
import io
import json
import os
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from _load import load, ROOT

guard = load("trader-guard", "guard")
ticket = load("trader-broker", "ticket")

NOW = datetime.datetime(2026, 11, 16, 10, 0)            # Monday, 10:00 India time
CFG = {"budget": 50000, "max_daily_loss_usd": 1500, "max_trades_per_day": 3}


def trade(kind, **kw):
    t = {"kind": kind, "symbol": "TCS.NS", "side": "buy", "price": 2442.0, "units": 15}
    t.update(kw)
    return t


def option(kind="option-buy", **kw):
    t = {"kind": kind, "symbol": "NIFTY", "side": "sell" if kind == "option-sell" else "buy", "option": "call",
         "strike": 24600.0, "lots": 1, "lot_size": 65, "units": 65, "price": 120.0, "underlying": 24500.0,
         "expiry": "2026-11-24"}
    t.update(kw)
    return t


def check(t, cfg=CFG, now=NOW):
    return guard.assess(t, cfg, now)


def ids(res, level=None):
    return [w["id"] for w in res["warnings"] if level is None or w["level"] == level]


def text(res, rid):
    return " ".join(w["text"] for w in res["warnings"] if w["id"] == rid)


def run(argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = guard.main(argv)
    return code, out.getvalue(), err.getvalue()


class Money(unittest.TestCase):
    def test_rupees_in_lakh_and_crore(self):
        for x, want in ((0, "Rs 0"), (999, "Rs 999"), (7800, "Rs 7,800"), (100000, "Rs 1,00,000"),
                        (1592500, "Rs 15,92,500"), (12345678.9, "Rs 1,23,45,678.90"), (2.599, "Rs 2.60"),
                        (-328.25, "-Rs 328.25")):
            self.assertEqual(guard.rs(x), want)
        self.assertEqual(guard.of_money(1430, 50000), " (2.9% of your Rs 50,000)")
        self.assertEqual(guard.of_money(644000, 50000), " (12.9 times your Rs 50,000)")
        self.assertEqual(guard.of_money(100, None), "")

    def test_intraday_charges_are_the_pack_s_own(self):
        r = guard.CHARGES["equity-intraday"]
        for mine, theirs in (("brokerage_pct", "brokerage_pct"), ("brokerage_max", "brokerage_max"),
                             ("stt_sell_pct", "stt_sell_pct"), ("exchange_pct", "exchange_pct"),
                             ("stamp_buy_pct", "stamp_buy_pct")):
            self.assertEqual(r[mine], ticket.NSE_CHARGES[theirs], mine)
        self.assertEqual((guard.SEBI_PER_CRORE, guard.GST_PCT),
                         (ticket.NSE_CHARGES["sebi_per_crore"], ticket.NSE_CHARGES["gst_pct"]))
        self.assertEqual(guard.charges("equity-intraday", 2442.0, 2461.3), ticket.nse_charges(2442.0, 2461.3))

    def test_charges_for_delivery_futures_and_options(self):
        # zerodha.com/charges, read 2026-11-15. 20 shares at 1,149 bought and sold for delivery:
        d = guard.charges("equity-delivery", 22980.0, 22980.0)
        self.assertEqual((d["brokerage"], d["stt"], d["exchange"], d["sebi"], d["stamp"], d["gst"], d["total"]),
                         (0.0, 45.96, 1.41, 0.05, 3.45, 0.26, 51.13))      # no brokerage; STT 0.1% each way
        # one Nifty future lot, 65 x 24,550 = 15,95,750 each way: brokerage capped at Rs 20 an order
        f = guard.charges("future", 1595750.0, 1595750.0)
        self.assertEqual((f["brokerage"], f["exchange"], f["sebi"]), (40.0, 58.4, 3.19))
        self.assertAlmostEqual(f["stamp"], 31.92, delta=0.011)              # 0.002% on the buy: 31.915
        self.assertAlmostEqual(f["stt"], 797.88, delta=0.011)               # 0.05% on the sell: 797.875
        self.assertAlmostEqual(f["total"], 949.68, delta=0.02)
        # an option premium of 1,430 each way: a flat Rs 20 an order, STT 0.15% of the premium sold
        o = guard.charges("option", 1430.0, 1430.0)
        self.assertEqual((o["brokerage"], o["exchange"], o["stamp"], o["gst"]), (40.0, 1.02, 0.04, 7.38))
        self.assertAlmostEqual(o["total"], 50.59, delta=0.011)


class Shares(unittest.TestCase):
    def test_a_planned_intraday_trade_is_only_careful(self):
        res = check(trade("equity-intraday", stop=2422.7))
        self.assertEqual(res["level"], "CAREFUL")
        n = res["numbers"]
        self.assertEqual((n["you_pay"], round(n["max_loss"], 2), n["max_loss_is"]), (36630.0, 289.5, "at your stop"))
        self.assertEqual(n["moves"], {1: 366.3, 2: 732.6, 5: 1831.5, 10: 3663.0})
        self.assertEqual(sorted(ids(res, "CAREFUL")), ["costs", "one-share"])      # 73% of the money in one share
        self.assertIn("13% of the Rs 289.50 you are risking", text(res, "costs"))
        self.assertEqual(sorted(ids(res, "INFO")), ["intraday-odds", "square-off"])
        self.assertIn("7 in 10", text(res, "intraday-odds"))

    def test_no_stop_a_big_loss_and_a_late_entry(self):
        res = check(trade("equity-intraday"))
        self.assertEqual(res["level"], "HIGH")
        self.assertIn("no-stop", ids(res, "HIGH"))
        self.assertNotIn("max_loss", res["numbers"])
        res = check(trade("equity-intraday", stop=2300.0))                  # 15 x 142 = 2,130: 4.3% of 50,000
        self.assertIn("more than the 1 to 2%", text(res, "loss-size"))
        res = check(trade("equity-intraday", stop=2200.0))                  # 3,630: 7.3%
        self.assertEqual([w["level"] for w in res["warnings"] if w["id"] == "loss-size"], ["HIGH"])
        res = check(trade("equity-intraday", units=20, stop=2100.0))        # 6,840: 13.7%
        self.assertEqual([w["level"] for w in res["warnings"] if w["id"] == "loss-size"], ["EXTREME"])
        late = check(trade("equity-intraday", stop=2422.7), now=datetime.datetime(2026, 11, 16, 15, 5))
        self.assertIn("It is 15:05. Zerodha closes intraday positions itself at 3:20 pm", text(late, "late"))

    def test_short_selling_borrowed_shares_and_cheap_shares(self):
        res = check(trade("equity-intraday", side="sell", stop=2460.0))
        self.assertIn("short-shares", ids(res, "HIGH"))
        self.assertEqual(round(res["numbers"]["max_loss"], 2), 270.0)       # 15 x (2460 - 2442)
        res = check(trade("equity-intraday", units=30, stop=2422.7))        # 73,260 with 50,000
        self.assertIn("more than your trading money", text(res, "leverage"))
        res = check(trade("equity-delivery", symbol="XYZ", price=12.0, units=100))
        self.assertEqual((res["level"], sorted(ids(res))), ("CAREFUL", ["low-price", "no-stop", "overnight"]))
        with self.assertRaises(guard.GuardError):
            check(trade("equity-intraday", stop=2500.0))                    # a stop above the price of a buy

    def test_mtf_shows_what_is_borrowed_and_what_it_costs(self):
        res = check(trade("mtf", symbol="RELIANCE", price=1330.0, units=100, own=40000.0, stop=1290.0))
        self.assertEqual(res["level"], "HIGH")
        self.assertEqual((res["numbers"]["borrowed"], res["numbers"]["position"]), (93000.0, 133000.0))
        self.assertIn("lends you Rs 93,000", text(res, "mtf"))
        self.assertIn("0.04% a day (Rs 40 per lakh): about Rs 37.20 a day, Rs 1,116 a month", text(res, "mtf"))
        self.assertIn("2.7 times your whole trading money", text(res, "leverage"))
        self.assertIn("overnight", ids(res, "HIGH"))
        self.assertIn("Give --own to see the numbers", text(check(trade("mtf", stop=2400.0)), "mtf"))


class FuturesAndOptions(unittest.TestCase):
    def test_a_future_is_leverage(self):
        t = {"kind": "future", "symbol": "NIFTY", "side": "buy", "price": 24550.0, "lots": 1, "lot_size": 65,
             "units": 65, "expiry": "2026-11-24"}
        res = check(t)
        self.assertEqual(res["level"], "EXTREME")
        self.assertEqual(res["numbers"]["controls"], 1595750.0)
        self.assertEqual(res["numbers"]["moves"][1], 15957.5)               # 1% of the index costs 32% of 50,000
        self.assertIn("31.9 times your whole trading money", text(res, "leverage"))
        self.assertEqual(sorted(ids(res, "HIGH")), ["fno-odds", "future", "margin-call", "no-stop", "overnight"])
        self.assertIn("About 9 in 10", text(res, "fno-odds"))
        self.assertNotIn("delivery-at-expiry", ids(res))                    # an index settles in cash
        short = check(dict(t, side="sell"))
        self.assertIn("no limit to the loss", text(short, "unlimited-loss"))

    def test_buying_an_option_and_the_clock(self):
        far = check(option())                                               # 8 days out, a Rs 7,800 premium
        self.assertEqual((far["numbers"]["you_pay"], far["numbers"]["max_loss_is"]), (7800.0, "the whole premium"))
        self.assertEqual([w["level"] for w in far["warnings"] if w["id"] == "time-decay"], ["CAREFUL"])
        self.assertEqual(far["level"], "EXTREME")                           # 15.6% of the money in one premium
        self.assertEqual(ids(far, "EXTREME"), ["loss-size"])
        small = check(option(price=12.0))                                   # Rs 780: 1.6% of the money
        self.assertEqual((small["level"], sorted(ids(small, "HIGH"))), ("HIGH", ["costs", "fno-odds"]))
        self.assertIn("of the Rs 780 premium. The flat Rs 20 an order weighs heavily", text(small, "costs"))
        self.assertNotIn("moves", far["numbers"])                           # an option does not move one for one
        near = check(option(expiry="2026-11-17", strike=24900.0, price=22.0))
        self.assertIn("Expiry is in 1 day.", text(near, "time-decay"))
        self.assertIn("has to move 1.6% just to reach your strike (24900) and there is 1 day left",
                      text(near, "far-strike"))
        self.assertIn("3.5% of the Rs 1,430 premium", text(near, "costs"))
        today = check(option(expiry="2026-11-16"))
        self.assertEqual(today["level"], "EXTREME")
        self.assertIn("Today is expiry day", text(today, "expiry-day"))
        put = check(option(option="put", strike=24000.0, expiry="2026-11-18"))   # 2% below, 2 days
        self.assertIn("has to move 2.0%", text(put, "far-strike"))
        with self.assertRaises(guard.GuardError):
            check(option(expiry="2026-11-10"))                              # already expired

    def test_selling_an_option(self):
        call = check(option("option-sell"))
        self.assertEqual(call["level"], "EXTREME")
        self.assertIsNone(call["numbers"]["max_loss"])
        self.assertIn("no limit to what you can lose, and the most you can make is the Rs 7,800 premium",
                      text(call, "unlimited-loss"))
        self.assertIn("margin-call", ids(call, "HIGH"))
        put = check(option("option-sell", symbol="RELIANCE", option="put", strike=1300.0, lot_size=500, units=500,
                           price=12.0, underlying=1330.0), now=datetime.datetime(2026, 11, 20, 10, 0))
        self.assertEqual(put["numbers"]["max_loss"], 644000.0)              # 500 x (1300 - 12)
        self.assertIn("lose up to Rs 6,44,000, and the most you can make is the Rs 6,000 premium",
                      text(put, "unlimited-loss"))
        self.assertIn("13.3 times your whole trading money", text(put, "leverage"))
        hedged = check(option("option-sell", hedged=True))
        self.assertNotIn("unlimited-loss", ids(hedged))
        self.assertIn("hedged-sale", ids(hedged, "HIGH"))

    def test_a_stock_contract_is_delivered_at_expiry(self):
        t = option("option-buy", symbol="RELIANCE", strike=1340.0, lot_size=500, units=500, price=8.0,
                   underlying=1330.0)
        early = check(t)                                                    # 8 days out
        self.assertEqual([w["level"] for w in early["warnings"] if w["id"] == "delivery-at-expiry"], ["INFO"])
        week = check(dict(t, expiry="2026-11-20"))                          # 4 days out
        self.assertEqual([w["level"] for w in week["warnings"] if w["id"] == "delivery-at-expiry"], ["HIGH"])
        self.assertIn("the whole lot (about Rs 6,65,000)", text(week, "delivery-at-expiry"))
        last = check(dict(t, expiry="2026-11-17"))
        self.assertEqual([w["level"] for w in last["warnings"] if w["id"] == "delivery-at-expiry"], ["EXTREME"])


class Pledging(unittest.TestCase):
    def test_what_pledging_puts_at_risk(self):
        res = check(trade("pledge", symbol="HDFCBANK", price=1650.0, units=50))
        self.assertEqual(res["level"], "HIGH")
        self.assertEqual(res["numbers"]["pledged_value"], 82500.0)
        self.assertEqual(sorted(ids(res)), ["fno-odds", "pledge", "pledge-cash", "pledge-falls"])
        self.assertIn("a haircut", text(res, "pledge"))
        self.assertIn("Rs 30 + GST", text(res, "pledge"))
        self.assertIn("the broker can sell shares to cover it", text(res, "pledge-falls"))
        self.assertIn("half the margin must be cash", text(res, "pledge-cash"))
        self.assertIn("0.035% a day", text(res, "pledge-cash"))


class TheDay(unittest.TestCase):
    def test_news_spread_ban_and_how_the_day_went(self):
        base = trade("equity-intraday", stop=2422.7)
        res = check(dict(base, event="results today", bid=2440.0, ask=2460.0, lost_today=800.0))
        self.assertIn("Scheduled: results today.", text(res, "event"))
        self.assertIn("0.8% apart (2440 and 2460)", text(res, "spread"))
        self.assertIn("more than half your daily limit of Rs 1,500", text(res, "daily-loss"))
        over = check(dict(base, lost_today=1500.0, trades_today=3))
        self.assertEqual(over["level"], "EXTREME")
        self.assertIn("Stop for today", text(over, "daily-loss"))
        self.assertIn("trade number 4 today; your own limit is 3", text(over, "too-many"))
        self.assertIn("ban", ids(check(option("option-buy", in_ban=True)), "HIGH"))
        bare = guard.assess(trade("equity-intraday", stop=2422.7), {}, NOW)        # no trading money known
        self.assertIn("no-capital", ids(bare, "INFO"))
        self.assertNotIn("one-share", ids(bare))


class Command(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.cfg = os.path.join(self.tmp.name, "config.json")
        with open(self.cfg, "w") as fh:
            json.dump(CFG, fh)
        self.base = ["check", "--config", self.cfg, "--now", "2026-11-16 10:00"]

    def test_the_report_and_the_exit_code(self):
        code, out, err = run(self.base + ["--kind", "equity-intraday", "--symbol", "tcs.ns", "--qty", "15",
                                         "--price", "2442", "--stop", "2422.70"])
        self.assertEqual(code, 0, err)
        self.assertTrue(out.startswith("TRADE  BUY 15 shares of TCS.NS at Rs 2,442, intraday (MIS)"), out[:80])
        self.assertIn("  You pay         Rs 36,630 (73.3% of your Rs 50,000)", out)
        self.assertIn("  Worst case      Rs 289.50 (0.6% of your Rs 50,000), at your stop", out)
        self.assertIn("RISK LEVEL: CAREFUL   (2 careful, 2 info)", out)
        self.assertIn("A warning is information, not an order and not advice. Nothing was placed.", out)
        code, out, _ = run(self.base + ["--kind", "option-sell", "--symbol", "NIFTY", "--option", "call", "--strike",
                                       "24600", "--lots", "1", "--lot-size", "65", "--price", "120",
                                       "--underlying", "24500", "--expiry", "2026-11-24"])
        self.assertEqual(code, 1)                                           # HIGH or EXTREME
        self.assertIn("RISK LEVEL: EXTREME", out)
        self.assertIn("  Worst case      no limit to the loss", out)
        self.assertIn("A beginner should not take it with real money.", out)
        self.assertEqual(sorted({c for c in out if ord(c) > 127}), [])      # prints on any console

    def test_json_and_the_pack_s_own_order(self):
        doc = json.loads(run(self.base + ["--kind", "pledge", "--symbol", "HDFCBANK", "--qty", "50", "--price", "1650",
                                          "--json"])[1])
        self.assertEqual((doc["level"], doc["numbers"]["pledged_value"]), ("HIGH", 82500.0))
        orders = os.path.join(self.tmp.name, "orders.json")
        with open(orders, "w") as fh:                                       # the shape trader-budget writes
            json.dump({"orders": [{"symbol": "TCS.NS", "side": "buy", "qty": "15", "type": "market",
                                   "order_class": "bracket", "take_profit_limit_price": "2461.30",
                                   "stop_loss_stop_price": "2422.70",
                                   "plan": {"entry": 2442.0, "stop": 2422.7, "target": 2461.3}}]}, fh)
        code, out, err = run(self.base + ["--orders", orders])
        self.assertEqual(code, 0, err)
        self.assertIn("TRADE  BUY 15 shares of TCS.NS at Rs 2,442, intraday (MIS)", out)
        self.assertIn("Rs 289.50 (0.6% of your Rs 50,000), at your stop", out)

    def test_plain_errors(self):
        for argv, why in ((["--kind", "option-buy", "--symbol", "NIFTY", "--price", "10"], "give --lots and --lot-size"),
                          (["--kind", "future", "--symbol", "NIFTY", "--price", "10", "--lots", "1", "--lot-size", "65",
                            "--expiry", "soon"], "--expiry wants a date like 2026-11-24"),
                          (["--kind", "option-buy", "--symbol", "NIFTY", "--price", "10", "--lots", "1",
                            "--lot-size", "65"], "--option call|put and --strike"),
                          (["--kind", "equity-intraday", "--symbol", "TCS.NS", "--price", "2442"], "how many shares"),
                          (["--kind", "swap", "--symbol", "X", "--price", "1"], "--kind is one of"),
                          (["--orders", os.path.join(self.tmp.name, "none.json")], "no orders in")):
            code, _, err = run(self.base + argv)
            self.assertEqual(code, 1, argv)
            self.assertIn(why, err, argv)


class CourseAgrees(unittest.TestCase):
    """Module K of trader-learn teaches with the same numbers this tool prints."""

    def test_module_k_quotes_what_the_guard_computes(self):
        learn = load("trader-learn", "learn")
        with open(learn.COURSE, encoding="utf-8") as fh:
            k = {l["id"]: l for l in learn.parse_course(fh.read()) if l["id"].startswith("K")}
        self.assertEqual(sorted(k), ["K1", "K2", "K3", "K4", "K5"])
        fut = check({"kind": "future", "symbol": "NIFTY", "side": "buy", "price": 24550.0, "lots": 1, "lot_size": 65,
                     "units": 65, "expiry": "2026-11-24"})
        self.assertIn(guard.rs(fut["numbers"]["controls"]), k["K1"]["example"])            # Rs 15,95,750
        self.assertIn(guard.rs(fut["numbers"]["moves"][1]), k["K1"]["example"])            # Rs 15,957.50
        call = check(option())                                                             # 65 x 120
        self.assertIn(guard.rs(call["numbers"]["you_pay"]), k["K2"]["example"])            # Rs 7,800
        self.assertIn(guard.rs(65 * (24800 - 24600) - call["numbers"]["you_pay"]), k["K2"]["example"])   # Rs 5,200
        put = check(option("option-sell", symbol="RELIANCE", option="put", strike=1300.0, lot_size=500, units=500,
                           price=12.0, underlying=1330.0))
        self.assertIn(guard.rs(put["numbers"]["you_receive"]), k["K3"]["example"])         # Rs 6,000
        self.assertIn(guard.rs(500 * (1300 - 1200) - put["numbers"]["you_receive"]), k["K3"]["example"])  # Rs 44,000
        mtf = check(trade("mtf", symbol="RELIANCE", price=1330.0, units=100, own=40000.0))
        for quoted in (guard.rs(mtf["numbers"]["borrowed"]), "Rs 37.20", "Rs 1,116"):
            self.assertIn(quoted, k["K4"]["example"])
            self.assertIn(quoted, text(mtf, "mtf"))
        points = " ".join(k["K4"]["points"])
        self.assertIn("%g%% a day (Rs 40 per lakh)" % guard.MTF_INTEREST_PCT_A_DAY, points)
        self.assertIn("Rs 30 plus GST", points)
        self.assertIn("0.035% a day", points)
        self.assertIn(guard.rs(500 * 1300), k["K5"]["example"])                            # Rs 6,50,000 to take delivery


class Skill(unittest.TestCase):
    def test_the_skill_file_covers_every_kind(self):
        with open(os.path.join(ROOT, "trader-guard", "SKILL.md"), encoding="utf-8") as fh:
            skill = fh.read()
        for kind in guard.KINDS:
            self.assertIn("--kind %s" % kind, skill, kind)
        low = " ".join(skill.lower().split())
        self.assertIn("not financial advice", low)
        self.assertIn("never places, sizes, changes or blocks an order", low)


if __name__ == "__main__":
    unittest.main()
