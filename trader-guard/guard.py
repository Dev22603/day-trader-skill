#!/usr/bin/env python3
"""Risk warnings for trader-guard: describe ANY trade and it lists what can go
wrong, with rupee numbers, before you place it. Shares, intraday, borrowed
money (MTF), futures, options and pledging, for the Indian market (Zerodha).
Standard library only, no network. It never places or blocks anything: it warns.

    python3 guard.py check --kind equity-intraday --symbol TCS.NS --qty 15 --price 2442 --stop 2422.70
    python3 guard.py check --kind equity-delivery --symbol INFY --qty 20 --price 1149
    python3 guard.py check --kind mtf --symbol RELIANCE --qty 100 --price 1330 --own 40000
    python3 guard.py check --kind future --symbol NIFTY --lots 1 --lot-size 65 --price 24550 --expiry 2026-11-24
    python3 guard.py check --kind option-buy --symbol NIFTY --option call --strike 24600 --lots 1 --lot-size 65 \\
        --price 120 --underlying 24500 --expiry 2026-11-17
    python3 guard.py check --kind option-sell --symbol RELIANCE --option put --strike 1300 --lots 1 --lot-size 500 \\
        --price 12 --underlying 1330 --expiry 2026-11-24
    python3 guard.py check --kind pledge --symbol HDFCBANK --qty 50 --price 1650
    python3 guard.py check --orders trader/orders.json        # the order trader-budget proposed

What you give it
  --kind      equity-intraday | equity-delivery | mtf | future | option-buy | option-sell | pledge
  --qty N, or --lots N with --lot-size N (futures and options trade in lots)
  --price     the share price, the future's price, or the option's premium (per share)
  --side      buy (default) or sell: a sell of shares or a future is a short
  --stop      the price where you would get out, if you have one
  --underlying, --strike, --option call|put, --expiry YYYY-MM-DD   for futures and options
  --own       for mtf: how much of the purchase is your own money
  --margin    for a future or an option sale: the margin the broker blocks, if you know it
  --hedged    this option sale is covered by another option
  --capital   your trading money (default: "budget" in trader/config.json)
  --bid, --ask                         the two prices now, to judge the spread
  --event "results today"              something scheduled that can move the price
  --lost-today N, --trades-today N     how the day has gone so far
  --in-ban                             the share is in the F&O ban period
  --now "2026-11-16 10:00"             pin the clock (India time)

What it prints: the trade in plain words, the money you put in, what the
position controls, the worst case it can put a number on, what a 1%, 2%, 5%
and 10% move against you costs, the costs of getting in and out, and then
every warning that applies, most serious first: EXTREME, HIGH, CAREFUL, INFO.
The overall level is the worst one.

Exit code 0 when nothing is above CAREFUL, 1 when a warning is HIGH or EXTREME.

Facts and rates (read 2026-11-15; they change, check them):
  zerodha.com/charges: brokerage, STT, exchange charges, stamp duty and GST for
    intraday, delivery, futures and options; MTF interest 0.04% a day; pledge
    request Rs 30 + GST; debit interest 0.05% a day; auto square-off Rs 50 an order.
  support.zerodha.com: physical settlement of stock F&O, and pledging (half the
    F&O margin in cash, 0.035% a day on a shortfall).
  SEBI: 71% of individual intraday traders lost money (year to March 2023, press
    release 13/2024); about 91% of individual F&O traders did (year to March 2025).
"""

import argparse
import datetime
import json
import os
import sys

LEVELS = ("INFO", "CAREFUL", "HIGH", "EXTREME")
KINDS = ("equity-intraday", "equity-delivery", "mtf", "future", "option-buy", "option-sell", "pledge")
INDEXES = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50", "SENSEX", "BANKEX", "SENSEX50"}
# Zerodha's charges by product, zerodha.com/charges (read 2026-11-15). Percent of the value
# traded (for an option: of the premium). "flat" is rupees per executed order.
CHARGES = {
    "equity-intraday": {"brokerage_pct": 0.03, "brokerage_max": 20.0, "stt_buy_pct": 0.0, "stt_sell_pct": 0.025,
                        "exchange_pct": 0.00307, "stamp_buy_pct": 0.003},
    "equity-delivery": {"brokerage_pct": 0.0, "brokerage_max": 0.0, "stt_buy_pct": 0.1, "stt_sell_pct": 0.1,
                        "exchange_pct": 0.00307, "stamp_buy_pct": 0.015},
    "future": {"brokerage_pct": 0.03, "brokerage_max": 20.0, "stt_buy_pct": 0.0, "stt_sell_pct": 0.05,
               "exchange_pct": 0.00183, "stamp_buy_pct": 0.002},
    "option": {"brokerage_flat": 20.0, "stt_buy_pct": 0.0, "stt_sell_pct": 0.15, "exchange_pct": 0.03553,
               "stamp_buy_pct": 0.003},
}
SEBI_PER_CRORE = 10.0
GST_PCT = 18.0
MTF_INTEREST_PCT_A_DAY = 0.04      # on the amount the broker lends
SQUARE_OFF = "3:20 pm"             # Zerodha closes intraday share positions itself, Rs 50 + GST an order
LATE_ENTRY = datetime.time(15, 0)


class GuardError(Exception):
    pass


def rs(x):
    """Rs 7,800, Rs 2.60, Rs 15,92,500: Indian grouping (lakh, crore), no paise on a whole amount."""
    paise = int(round(abs(float(x)) * 100))
    whole, frac = str(paise // 100), paise % 100
    head, groups = whole[:-3], [whole[-3:]]
    while head:
        head, groups = head[:-2], [head[-2:]] + groups
    return "%sRs %s%s" % ("-" if float(x) < 0 and paise else "", ",".join(groups), (".%02d" % frac) if frac else "")


def pct(part, whole):
    return 100.0 * part / whole if whole else None


def of_money(amount, capital):
    """' (2.9% of your Rs 50,000)', or ' (12.9 times your Rs 50,000)' when it is far more than you have."""
    if not capital:
        return ""
    share = pct(amount, capital)
    return " (%s your %s)" % ("%.1f times" % (share / 100.0) if share >= 200 else "%.1f%% of" % share, rs(capital))


def charges(product, buy_value, sell_value):
    """Zerodha's charges for one buy and one sell of this product, in rupees (about)."""
    r = CHARGES[product]
    b, s = float(buy_value), float(sell_value)
    if "brokerage_flat" in r:
        brokerage = r["brokerage_flat"] * sum(1 for v in (b, s) if v > 0)
    else:
        brokerage = sum(min(v * r["brokerage_pct"] / 100.0, r["brokerage_max"]) for v in (b, s) if v > 0)
    exchange = (b + s) * r["exchange_pct"] / 100.0
    sebi = (b + s) * SEBI_PER_CRORE / 1e7
    out = {"brokerage": brokerage, "stt": b * r["stt_buy_pct"] / 100.0 + s * r["stt_sell_pct"] / 100.0,
           "exchange": exchange, "sebi": sebi, "stamp": b * r["stamp_buy_pct"] / 100.0,
           "gst": (brokerage + exchange + sebi) * GST_PCT / 100.0}
    out = {k: round(v, 2) for k, v in out.items()}
    out["total"] = round(sum(out.values()), 2)
    return out


def india_now(text=None):
    """Naive India time (UTC+5:30, no daylight time). --now pins it."""
    if text:
        try:
            return datetime.datetime.fromisoformat(text.strip())
        except ValueError:
            raise GuardError('--now wants an India time like "2026-11-16 10:00"')
    utc = datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)
    return utc + datetime.timedelta(hours=5, minutes=30)


def is_index(symbol):
    return str(symbol).upper().replace(".NS", "") in INDEXES


def describe(t):
    """The trade in one plain line."""
    sym, kind = t["symbol"], t["kind"]
    if kind in ("option-buy", "option-sell"):
        verb = "BUY" if kind == "option-buy" else "SELL"
        return "%s %s lot%s (%d) of %s %s %s expiring %s at %s premium" % (
            verb, _n(t["lots"]), "" if t["lots"] == 1 else "s", t["units"], sym, _n(t["strike"]),
            t["option"].upper(), t["expiry"] or "?", rs(t["price"]))
    if kind == "future":
        return "%s %s lot%s (%d) of the %s future%s at %s" % (
            t["side"].upper(), _n(t["lots"]), "" if t["lots"] == 1 else "s", t["units"], sym,
            (" expiring " + t["expiry"]) if t["expiry"] else "", rs(t["price"]))
    if kind == "pledge":
        return "PLEDGE %d shares of %s (worth %s) for margin" % (t["units"], sym, rs(t["units"] * t["price"]))
    how = {"equity-intraday": "intraday (MIS)", "equity-delivery": "delivery (CNC)", "mtf": "with borrowed money (MTF)"}[kind]
    return "%s %d shares of %s at %s, %s" % (t["side"].upper(), t["units"], sym, rs(t["price"]), how)


def _n(x):
    x = float(x)
    return str(int(x)) if x == int(x) else "%.2f" % x


def assess(t, cfg=None, now=None):
    """One trade -> {"trade", "numbers", "warnings", "level"}. Pure: no files, no clock."""
    cfg, now = cfg or {}, now or india_now()
    kind, side, price, units = t["kind"], t["side"], float(t["price"]), int(t["units"])
    capital = t.get("capital") or cfg.get("budget")
    capital = float(capital) if capital else None
    under = float(t["underlying"]) if t.get("underlying") else None
    strike = float(t["strike"]) if t.get("strike") else None
    stop = float(t["stop"]) if t.get("stop") else None
    fno = kind in ("future", "option-buy", "option-sell")
    linear = kind in ("equity-intraday", "equity-delivery", "mtf", "future")    # a 1% move is a 1% result
    warnings, n = [], {}

    def warn(level, rid, text):
        warnings.append({"id": rid, "level": level, "text": text})

    days = None
    if t.get("expiry"):
        try:
            days = (datetime.date.fromisoformat(t["expiry"]) - now.date()).days
        except ValueError:
            raise GuardError("--expiry wants a date like 2026-11-24")
        if days < 0:
            raise GuardError("that contract expired on %s" % t["expiry"])
        n["days_to_expiry"] = days

    # ---- the numbers
    value = units * price                                   # shares: what they are worth. options: the premium
    if kind == "option-buy":
        n["you_pay"] = value
        n["controls"] = units * under if under else None
        n["max_loss"], n["max_loss_is"] = value, "the whole premium"
    elif kind == "option-sell":
        n["you_receive"] = value
        n["controls"] = units * (under or strike)
        n["margin"] = float(t["margin"]) if t.get("margin") else None
        if t["option"] == "put":
            n["max_loss"], n["max_loss_is"] = units * (strike - price), "if the price goes to zero"
        else:
            n["max_loss"], n["max_loss_is"] = None, "no limit"
    elif kind == "future":
        n["controls"] = value
        n["margin"] = float(t["margin"]) if t.get("margin") else None
    elif kind == "mtf":
        own = float(t["own"]) if t.get("own") else None
        n["position"], n["you_pay"] = value, own
        n["borrowed"] = (value - own) if own is not None else None
        n["controls"] = value
    elif kind == "pledge":
        n["pledged_value"] = value
    else:
        n["you_pay"] = n["controls"] = value
    if stop is not None and linear:
        risk = (price - stop) if side == "buy" else (stop - price)
        if risk <= 0:
            raise GuardError("the stop %s is on the wrong side of the price %s for a %s" % (_n(stop), _n(price), side))
        n["max_loss"], n["max_loss_is"] = units * risk, "at your stop"
    if linear:
        n["moves"] = {m: round(n["controls"] * m / 100.0, 2) for m in (1, 2, 5, 10)}
    product = {"mtf": "equity-delivery", "option-buy": "option", "option-sell": "option"}.get(kind, kind)
    if product in CHARGES:
        n["costs"] = charges(product, value, value)["total"]

    # ---- the odds
    if fno:
        warn("HIGH", "fno-odds", "About 9 in 10 individual traders lost money in futures and options in SEBI's "
             "latest study (the year to March 2025). This is the most dangerous corner of the market for a beginner.")
    elif kind == "equity-intraday":
        warn("INFO", "intraday-odds", "7 in 10 individual intraday traders lost money in SEBI's study (the year to "
             "March 2023). A small size and a stop are what keep you in the game.")

    # ---- what the trade is
    if kind == "option-sell":
        if t.get("hedged"):
            warn("HIGH", "hedged-sale", "You say this sale is covered by another option. The loss is limited only "
                 "while both are open: close one, or let one expire, and the other is an uncovered sale.")
        elif t["option"] == "call":
            warn("EXTREME", "unlimited-loss", "You are selling a call. If the price shoots up there is no limit to "
                 "what you can lose, and the most you can make is the %s premium." % rs(value))
        else:
            warn("EXTREME", "unlimited-loss", "You are selling a put. If the price collapses you can lose up to %s, "
                 "and the most you can make is the %s premium." % (rs(n["max_loss"]), rs(value)))
    if kind == "future":
        text = ("A future makes you gain or lose on %d shares' worth (%s) with only a margin put down. The loss can "
                "be bigger than that margin." % (units, rs(value)))
        if side == "sell":
            warn("EXTREME", "unlimited-loss", text + " You are short: if the price rises there is no limit to the loss.")
        else:
            warn("HIGH", "future", text)
    if kind in ("future", "option-sell"):
        warn("HIGH", "margin-call", "While it is open, each day's loss is taken from your account (mark to market). "
             "When the margin runs short the broker asks for more money (a margin call); if you cannot pay, it "
             "closes the position at whatever the price is.")
    if kind == "equity-intraday" and side == "sell":
        warn("HIGH", "short-shares", "You are selling shares you do not own (a short). You lose if the price rises, "
             "with no ceiling. If the share locks at its upper circuit you cannot buy it back, and a short left "
             "open goes to auction with a penalty.")
    if kind == "mtf":
        if n["borrowed"] and n["borrowed"] > 0:
            day = n["borrowed"] * MTF_INTEREST_PCT_A_DAY / 100.0
            warn("HIGH", "mtf", "MTF means the broker lends you %s of this purchase. Interest is %g%% a day (Rs 40 per "
                 "lakh): about %s a day, %s a month, win or lose. The shares stay pledged to the broker; if they "
                 "fall, it asks for more money or sells them. Your loss is on the full %s, not on your %s."
                 % (rs(n["borrowed"]), MTF_INTEREST_PCT_A_DAY, rs(day), rs(day * 30), rs(value), rs(n["you_pay"])))
        else:
            warn("HIGH", "mtf", "MTF means the broker lends you part of this purchase and charges %g%% a day (Rs 40 "
                 "per lakh) on what it lends, win or lose. The shares stay pledged to the broker; if they fall, it "
                 "asks for more money or sells them. Your loss is on the full position. Give --own to see the numbers."
                 % MTF_INTEREST_PCT_A_DAY)
    if kind == "pledge":
        warn("HIGH", "pledge", "Pledging hands these shares to the broker as security for trading margin. You get "
             "less than their value (a haircut), worked out from yesterday's close. Each pledge request costs "
             "Rs 30 + GST per share name.")
        warn("HIGH", "pledge-falls", "If the pledged shares fall, your margin falls with them, usually on the same "
             "days your trades are losing. If losses leave your account in debit, the broker can sell shares to "
             "cover it: long-term holdings lost to a short-term bet.")
        warn("CAREFUL", "pledge-cash", "For futures and options half the margin must be cash. A shortfall held "
             "overnight costs 0.035% a day plus GST, and a debit left for five trading days blocks the collateral.")
        warn("HIGH", "fno-odds", "Margin from pledged shares is mostly used for futures and options, where about "
             "9 in 10 individual traders lose money (SEBI, the year to March 2025).")

    # ---- how big
    exposure = n.get("controls") if kind != "option-buy" else None
    if capital and exposure and exposure > capital * 1.0001 and (fno or kind == "mtf"):
        times = exposure / capital
        warn("EXTREME" if times >= 3 else "HIGH", "leverage",
             "This position is worth %.1f times your whole trading money (%s). A 1%% move against you is %.1f%% of "
             "that money, and a 5%% move is %.0f%%." % (times, rs(capital), times, times * 5))
    if capital and kind in ("equity-intraday", "equity-delivery") and value > capital * 1.0001:
        warn("HIGH", "leverage", "These shares cost %s, more than your trading money (%s): the rest would be "
             "borrowed from the broker, and the loss is on the full amount." % (rs(value), rs(capital)))
    elif capital and kind in ("equity-intraday", "equity-delivery", "mtf") and value > capital * 0.5:
        warn("CAREFUL", "one-share", "More than half of your trading money (%s of %s) would sit in one share."
             % (rs(value), rs(capital)))
    loss = n.get("max_loss")
    if loss is not None and capital:
        share = pct(loss, capital)
        what = "%s, %s%s" % (rs(loss), n["max_loss_is"], of_money(loss, capital))
        if share > 10:
            warn("EXTREME", "loss-size", "If this goes wrong you lose %s, in one trade. A few trades like this and "
                 "the account is gone." % what)
        elif share > 5:
            warn("HIGH", "loss-size", "If this goes wrong you lose %s. Most traders risk 1 to 2%% on one trade." % what)
        elif share > 2:
            warn("CAREFUL", "loss-size", "If this goes wrong you lose %s: more than the 1 to 2%% most traders risk "
                 "on one trade." % what)
    if stop is None and kind in ("equity-intraday", "mtf", "future"):
        warn("HIGH", "no-stop", "No stop: you have not decided where you get out if you are wrong. Decide that "
             "price before you place the order.")
    elif stop is None and kind == "equity-delivery":
        warn("INFO", "no-stop", "No stop given. For a long-term buy that can be fine, but decide now what would "
             "make you sell.")

    # ---- time
    if kind == "option-buy":
        if days == 0:
            warn("EXTREME", "expiry-day", "Today is expiry day. This option can lose most of its value in minutes, "
                 "and is worth nothing at the close unless the price has passed the strike.")
        elif days is not None and days <= 2:
            warn("HIGH", "time-decay", "Expiry is in %d day%s. An option loses value every day even if the price "
                 "stands still (time decay), fastest in the last days, and is worth nothing at expiry unless the "
                 "price has passed the strike." % (days, "" if days == 1 else "s"))
        else:
            warn("CAREFUL", "time-decay", "An option loses a little value every day even if the price stands still "
                 "(time decay), and is worth nothing at expiry unless the price has passed the strike. You can be "
                 "right about the direction and still lose.")
        if under and strike:
            away = pct((strike - under) if t["option"] == "call" else (under - strike), under)
            if away > 0 and ((days is not None and ((away >= 1 and days <= 2) or (away >= 2 and days <= 7))) or away >= 5):
                warn("HIGH", "far-strike", "The price has to move %.1f%% just to reach your strike (%s)%s. Cheap "
                     "options are cheap because that rarely happens in time."
                     % (away, _n(strike), (" and there %s %d day%s left" % ("is" if days == 1 else "are", days,
                                                                            "" if days == 1 else "s"))
                        if days is not None else ""))
    if fno and not is_index(t["symbol"]):
        lot_value = units * (under or strike or price) if kind != "future" else value
        if days is not None and days <= 4:
            warn("EXTREME" if days <= 1 else "HIGH", "delivery-at-expiry",
                 "This is a stock contract and expiry is in %d day%s. Stock futures and in-the-money stock options "
                 "are settled by delivery: you would have to pay for, or hand over, the whole lot (about %s). "
                 "Zerodha raises the margin from four days before expiry and may close the position (Rs 50 + GST). "
                 "Close it before the expiry week." % (days, "" if days == 1 else "s", rs(lot_value)))
        else:
            warn("INFO", "delivery-at-expiry", "Stock futures and options are settled by delivery at expiry, not in "
                 "cash: the whole lot (about %s) changes hands. Close the position before the expiry week."
                 % rs(lot_value))
    if kind in ("future", "option-sell", "mtf"):
        warn("HIGH", "overnight", "Held overnight, the price can open far from yesterday's close. A stop does not "
             "protect you across that gap, and with borrowed money the gap is multiplied.")
    elif kind in ("equity-delivery", "option-buy"):
        warn("INFO", "overnight", "Held overnight, the price can open well away from yesterday's close. A stop does "
             "not protect you across that gap.")
    if kind == "equity-intraday":
        if now.time() >= LATE_ENTRY:
            warn("CAREFUL", "late", "It is %s. Zerodha closes intraday positions itself at %s (Rs 50 + GST an "
                 "order): there is little time left for a new trade." % (now.strftime("%H:%M"), SQUARE_OFF))
        else:
            warn("INFO", "square-off", "Intraday (MIS): Zerodha closes what is still open at %s and charges Rs 50 + "
                 "GST an order. Be out by 3:15 yourself." % SQUARE_OFF)

    # ---- costs, price quality, the day so far
    costs = n.get("costs")
    if costs and kind in ("option-buy", "option-sell"):
        share = pct(costs, value)
        if share > 2:
            warn("HIGH" if share > 5 else "CAREFUL", "costs", "Getting in and out costs about %s, %.1f%% of the %s "
                 "premium. The flat Rs 20 an order weighs heavily on a small trade: the option must move that much "
                 "before you make anything." % (rs(costs), share, rs(value)))
    elif costs and loss and n.get("max_loss_is") == "at your stop":
        share = pct(costs, loss)
        if share > 10:
            warn("HIGH" if share > 25 else "CAREFUL", "costs", "Getting in and out costs about %s, %.0f%% of the %s "
                 "you are risking. Costs are paid on winners and losers alike." % (rs(costs), share, rs(loss)))
    if kind in ("equity-intraday", "equity-delivery", "mtf") and price < 20:
        warn("CAREFUL", "low-price", "A share priced under Rs 20. Low-priced shares often trade thinly, jump around "
             "and lock at circuit limits, where you cannot sell.")
    if t.get("bid") and t.get("ask"):
        bid, ask = float(t["bid"]), float(t["ask"])
        if ask > bid > 0:
            gap = pct(ask - bid, (ask + bid) / 2.0)
            if gap > 0.5:
                warn("HIGH" if gap > 2 else "CAREFUL", "spread", "The buying and selling prices are %.1f%% apart "
                     "(%s and %s). You lose that the moment you enter, and again if you have to leave in a hurry."
                     % (gap, _n(bid), _n(ask)))
    if t.get("event"):
        warn("HIGH", "event", "Scheduled: %s. Prices move further and faster around such news, and stops fill worse."
             % t["event"])
    if t.get("in_ban"):
        warn("HIGH", "ban", "This share is in the F&O ban period: new positions are not allowed and attract a penalty.")
    lost = float(t["lost_today"]) if t.get("lost_today") else 0.0
    limit = cfg.get("max_daily_loss_usd")
    if lost > 0 and limit:
        if lost >= float(limit):
            warn("EXTREME", "daily-loss", "You have lost %s today, at or over your own daily limit of %s. Stop for "
                 "today: trading to win it back is how a bad day becomes a disaster." % (rs(lost), rs(limit)))
        elif lost >= float(limit) / 2.0:
            warn("CAREFUL", "daily-loss", "You have lost %s today, more than half your daily limit of %s. Do not "
                 "make this trade bigger to win it back." % (rs(lost), rs(limit)))
    elif lost > 0:
        warn("CAREFUL", "daily-loss", "You have already lost %s today. Do not make this trade bigger to win it back."
             % rs(lost))
    if t.get("trades_today") and cfg.get("max_trades_per_day") and int(t["trades_today"]) >= int(cfg["max_trades_per_day"]):
        warn("HIGH", "too-many", "This would be trade number %d today; your own limit is %d. Every extra trade pays costs."
             % (int(t["trades_today"]) + 1, int(cfg["max_trades_per_day"])))
    if not capital:
        warn("INFO", "no-capital", "No trading money given (--capital, or \"budget\" in trader/config.json), so the "
             "checks that compare the trade with what you have were skipped.")

    warnings.sort(key=lambda w: -LEVELS.index(w["level"]))
    level = warnings[0]["level"] if warnings else "INFO"
    return {"trade": describe(t), "kind": kind, "symbol": t["symbol"], "numbers": n, "warnings": warnings,
            "level": level, "capital": capital}


VERDICT = {
    "EXTREME": "This is the kind of trade that empties accounts. A beginner should not take it with real money.",
    "HIGH": "High risk for a beginner. Make it smaller, set a stop, or skip it.",
    "CAREFUL": "Read each point before you go ahead.",
    "INFO": "Nothing unusual found. That is not a promise: every trade can lose.",
}


def report(res):
    n, cap = res["numbers"], res["capital"]

    def share(amount):
        return of_money(amount, cap)
    out = ["TRADE  " + res["trade"]]
    rows = []
    if n.get("you_pay") is not None:
        rows.append(("You pay", rs(n["you_pay"]) + share(n["you_pay"])))
    if n.get("you_receive") is not None:
        rows.append(("You receive", rs(n["you_receive"]) + " (the premium): the most this trade can make"))
    if n.get("borrowed"):
        rows.append(("Broker lends", rs(n["borrowed"])))
    if n.get("margin"):
        rows.append(("Margin blocked", rs(n["margin"]) + share(n["margin"])))
    if n.get("controls") and n["controls"] != n.get("you_pay"):
        rows.append(("It controls", rs(n["controls"]) + (" of shares" if res["kind"] == "mtf" else
                                                         " worth of the share or index behind it")))
    if n.get("pledged_value"):
        rows.append(("Pledged", rs(n["pledged_value"]) + " of your shares"))
    if "max_loss_is" in n:
        rows.append(("Worst case", (rs(n["max_loss"]) + share(n["max_loss"]) + ", " + n["max_loss_is"])
                     if n["max_loss"] is not None else "no limit to the loss"))
    elif n.get("moves"):
        rows.append(("Worst case", "not set: there is no stop. See the moves below"))
    if n.get("moves"):
        rows.append(("If it moves", ", ".join("%d%% against you = %s" % (m, rs(v)) for m, v in sorted(n["moves"].items()))))
    if "days_to_expiry" in n:
        rows.append(("Days to expiry", "%d%s" % (n["days_to_expiry"], " (today)" if n["days_to_expiry"] == 0 else "")))
    if n.get("costs"):
        rows.append(("Costs", "about %s to get in and out (Zerodha)" % rs(n["costs"])))
    out += ["  %-15s %s" % r for r in rows]
    counts = [(lv, sum(1 for w in res["warnings"] if w["level"] == lv)) for lv in reversed(LEVELS)]
    out += ["", "RISK LEVEL: %s   (%s)" % (res["level"], ", ".join("%d %s" % (c, lv.lower()) for lv, c in counts if c)), ""]
    out += ["%-8s %s" % (w["level"], w["text"]) for w in res["warnings"]]
    out += ["", VERDICT[res["level"]], "A warning is information, not an order and not advice. Nothing was placed."]
    return "\n".join(out)


# ---------------------------------------------------------------- commands

def read_json(path, default=None):
    if not path or not os.path.exists(path):
        return default
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except ValueError as e:
        raise GuardError("%s is not valid JSON: %s" % (path, e))


def trade_from_args(a):
    if a.kind not in KINDS:
        raise GuardError("--kind is one of: " + ", ".join(KINDS))
    if not a.symbol:
        raise GuardError("--symbol: which share, index or contract?")
    if a.price is None or a.price <= 0:
        raise GuardError("--price wants the price (for an option: the premium), above 0")
    fno = a.kind in ("future", "option-buy", "option-sell")
    if fno:
        if not a.lots or not a.lot_size or a.lots <= 0 or a.lot_size <= 0:
            raise GuardError("futures and options trade in lots: give --lots and --lot-size (read the lot size in Kite)")
        units = int(round(a.lots * a.lot_size))
    else:
        if not a.qty or a.qty <= 0:
            raise GuardError("--qty: how many shares?")
        units = int(a.qty)
    if a.kind in ("option-buy", "option-sell"):
        if a.option not in ("call", "put") or not a.strike:
            raise GuardError("an option needs --option call|put and --strike")
    return {"kind": a.kind, "symbol": a.symbol.upper(), "side": "sell" if a.kind == "option-sell" else a.side,
            "price": a.price, "units": units, "lots": a.lots, "lot_size": a.lot_size, "stop": a.stop,
            "underlying": a.underlying, "strike": a.strike, "option": a.option, "expiry": a.expiry, "own": a.own,
            "margin": a.margin, "hedged": a.hedged, "capital": a.capital, "bid": a.bid, "ask": a.ask,
            "event": a.event, "lost_today": a.lost_today, "trades_today": a.trades_today, "in_ban": a.in_ban}


def trades_from_orders(a):
    """trader-budget's proposed orders (trader/orders.json) as intraday share trades."""
    doc = read_json(a.orders)
    orders = (doc.get("orders", doc) if isinstance(doc, dict) else doc) or []
    if not isinstance(orders, list) or not orders:
        raise GuardError("no orders in %s (trader-budget writes them)" % a.orders)
    out = []
    for o in orders:
        plan = o.get("plan") if isinstance(o.get("plan"), dict) else {}
        price = o.get("limit_price") or plan.get("entry")
        if not price or not o.get("qty"):
            raise GuardError("an order in %s has no quantity or no price to check" % a.orders)
        out.append({"kind": "equity-intraday", "symbol": str(o.get("symbol", "?")).upper(),
                    "side": str(o.get("side", "buy")).lower(), "price": float(price), "units": int(float(o["qty"])),
                    "stop": o.get("stop_loss_stop_price") or plan.get("stop"), "capital": a.capital, "bid": a.bid,
                    "ask": a.ask, "event": a.event, "lost_today": a.lost_today, "trades_today": a.trades_today,
                    "in_ban": False})
    return out


def cmd_check(a):
    cfg = read_json(a.config, {}) or {}
    now = india_now(a.now)
    trades = trades_from_orders(a) if a.orders else [trade_from_args(a)]
    results = [assess(t, cfg, now) for t in trades]
    if a.json:
        print(json.dumps(results[0] if len(results) == 1 else results, indent=2))
    else:
        print("\n\n".join(report(r) for r in results))
    worst = max(LEVELS.index(r["level"]) for r in results)
    return 1 if worst >= LEVELS.index("HIGH") else 0


def main(argv=None):
    ap = argparse.ArgumentParser(description="Risk warnings for any trade (trader-guard). It warns; it never places or blocks.")
    sub = ap.add_subparsers(dest="cmd")
    p = sub.add_parser("check", help="list what can go wrong with one trade")
    p.add_argument("--kind", help=" | ".join(KINDS))
    p.add_argument("--orders", metavar="FILE", help="check the order(s) trader-budget proposed instead")
    p.add_argument("--symbol")
    p.add_argument("--side", default="buy", choices=["buy", "sell"])
    p.add_argument("--qty", type=float, help="shares")
    p.add_argument("--lots", type=float)
    p.add_argument("--lot-size", type=float, help="shares in one lot (read it in Kite; it changes)")
    p.add_argument("--price", type=float, help="share price, future price, or the option's premium per share")
    p.add_argument("--stop", type=float)
    p.add_argument("--underlying", type=float, help="the share or index price now, for an option")
    p.add_argument("--strike", type=float)
    p.add_argument("--option", choices=["call", "put"])
    p.add_argument("--expiry", help="YYYY-MM-DD")
    p.add_argument("--own", type=float, help="mtf: your own money in the purchase")
    p.add_argument("--margin", type=float, help="the margin the broker blocks, if you know it")
    p.add_argument("--hedged", action="store_true", help="this option sale is covered by another option")
    p.add_argument("--capital", type=float, help="your trading money (default: budget in the config)")
    p.add_argument("--bid", type=float)
    p.add_argument("--ask", type=float)
    p.add_argument("--event", help="scheduled news, e.g. \"results today\"")
    p.add_argument("--lost-today", type=float)
    p.add_argument("--trades-today", type=int)
    p.add_argument("--in-ban", action="store_true")
    p.add_argument("--config", default="trader/config.json")
    p.add_argument("--now", help='pretend it is this India time, e.g. "2026-11-16 10:00"')
    p.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    if not a.cmd:
        ap.print_help()
        return 1
    try:
        return cmd_check(a)
    except GuardError as e:
        print("guard.py: %s" % e, file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
