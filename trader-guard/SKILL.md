---
name: trader-guard
description: >-
  Risk Warner. Before ANY trade the user is about to make, in this pack or
  directly at their broker, it lists what can go wrong in plain words with
  rupee numbers: the worst case, what a 1% to 10% move costs, the costs of
  getting in and out, and every warning that applies, from INFO to EXTREME.
  Covers shares bought for delivery, intraday trades, short selling, borrowed
  money (MTF), futures, buying and selling options, expiry and delivery of
  stock contracts, and pledging shares for margin, for the Indian market and
  Zerodha. It warns; it never places, sizes or blocks an order. Use when the
  user says "is this risky", "what can go wrong", "warn me", "check this
  trade", "I want to buy a call", "sell a put", "trade futures", "F&O",
  "pledge my shares", "use MTF", "buy on margin", or before any yes in
  /trader-broker.
argument-hint: "[the trade, in words]"
---

# trader-guard

The Risk Warner answers one question before a trade: **what can this cost me,
and what am I not seeing?** It is for a beginner who has heard that futures,
options and pledging are dangerous and wants to be told, each time, exactly
why. It is advisory: it gives a risk level and the reasons. The decision
stays with the user. `/trader-risk` is the gate that enforces the user's own
limits inside this pack; this skill is wider and softer. It looks at any
trade, including ones the pack will not make.

`${CLAUDE_SKILL_DIR}` below is this skill's folder (where this SKILL.md lives).

```bash
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --orders trader/orders.json            # the pack's proposed order
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind equity-intraday --symbol TCS.NS --qty 15 --price 2442 --stop 2422.70
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind equity-delivery --symbol INFY --qty 20 --price 1149
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind mtf --symbol RELIANCE --qty 100 --price 1330 --own 40000
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind future --symbol NIFTY --lots 1 --lot-size 65 --price 24550 --expiry 2026-11-24
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind option-buy --symbol NIFTY --option call --strike 24600 \
    --lots 1 --lot-size 65 --price 120 --underlying 24500 --expiry 2026-11-17
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind option-sell --symbol RELIANCE --option put --strike 1300 \
    --lots 1 --lot-size 500 --price 12 --underlying 1330 --expiry 2026-11-24
python3 "${CLAUDE_SKILL_DIR}/guard.py" check --kind pledge --symbol HDFCBANK --qty 50 --price 1650
```

`guard.py` does the arithmetic and picks the warnings. It reads no prices and
places nothing. `--json` gives the same result as data. Exit code 1 means a
HIGH or EXTREME warning. `--now "2026-11-16 10:00"` pins the clock (India time).

## What it reads

| source | what |
| --- | --- |
| the flags | the trade: kind, symbol, quantity or lots, price, stop, strike, expiry and so on |
| `trader/config.json` | `budget` (the user's trading money), `max_daily_loss_usd`, `max_trades_per_day` |
| `trader/orders.json` | with `--orders`: the order trader-budget proposed |

It writes nothing.

## When to run it

1. **Before every yes in `/trader-broker`**, practice or live:
   `guard.py check --orders trader/orders.json`, and show the result with the ticket.
2. **Whenever the user says they are about to do something in the market**
   outside the pack: buy or sell shares, a future, an option, use MTF, pledge
   shares. Run it before they do it, not after.
3. **On request, over what the account already holds.** With the Kite
   connector (reading only): `get_positions`, `get_orders` (open ones) and
   `get_holdings`. Run one `check` for each open position and each waiting
   order, and one `--kind pledge` check for each holding that is pledged.

## Getting the facts for the flags

Ask the user in plain words, or read them with the Kite connector:

| flag | where it comes from |
| --- | --- |
| `--kind` | what they are doing. In Kite: product MIS is intraday, CNC is delivery, MTF is borrowed money, NRML with exchange NFO is F&O. A tradingsymbol ending in FUT is a future, in CE a call, in PE a put. A negative quantity is something sold: a short, or an option sale. |
| `--lot-size`, `--expiry`, `--strike` | `search_instruments`. Lot sizes change: never use one from memory. |
| `--price`, `--underlying`, `--bid`, `--ask` | `get_quotes` or `get_ltp`. For an option, `--price` is the premium and `--underlying` is the share or index price. |
| `--capital` | `budget` in the config, else ask: "how much money have you set aside for trading?" |
| `--margin` | what Kite's order window shows as required margin, if the user has it. |
| `--lost-today`, `--trades-today` | today's loss in `get_positions`, or `ticket.py report --days 1`. |
| `--event` | `/trader-news` for the symbol: results, an RBI decision, the Budget. |
| `--in-ban` | the NSE's daily list of shares in the F&O ban period. |
| `--hedged` | only if another option that limits the loss is open or goes in with it. |

If a fact is missing, run it without that flag and say what was not checked.
Never invent a lot size, a price or an expiry.

## How to say it

1. Lead with the level and the worst case in rupees: "Risk level EXTREME.
   You could lose up to Rs 6,44,000; the most you can make is Rs 6,000."
2. Go through every EXTREME and HIGH warning, one at a time, in plain words.
   Explain each new word in one sentence (`/trader-learn` has them: `learn.py
   term "margin call"`). Do not skip one because the list is long.
3. Say what the "If it moves" line means with their own money: "a 2% fall
   costs Rs 31,915, more than half of what you have."
4. Mention CAREFUL and INFO points briefly.
5. If they still want to go ahead, that is their call. Say what lowers the
   risk in general terms: fewer shares or lots, a stop, more time to expiry,
   not borrowing. Never say a trade is safe, and never call a level a
   recommendation.

Do not soften a warning to be polite, and do not pile on either. The numbers
do the work.

## What it warns about

| trade | warnings it can raise |
| --- | --- |
| intraday shares | no stop; loss bigger than 1 to 2% of the trading money; more than half the money in one share; costs against the risk; the 3:20 pm square-off; a late entry; short selling (circuit lock, auction) |
| delivery shares | no exit decided; too much in one share; the overnight gap; a share under Rs 20 |
| MTF (borrowed money) | the amount borrowed and the interest each day and month; the shares stay pledged; loss on the full position; leverage against the trading money |
| a future | leverage (what a 1% and 5% move costs); loss beyond the margin; daily mark to market and margin calls; no stop; the overnight gap; delivery of a stock future at expiry |
| buying an option | the whole premium can be lost; time decay; expiry day and the last two days; a strike the price is unlikely to reach in time; costs against a small premium |
| selling an option | a loss with no limit (call) or far above the premium (put); leverage; margin calls; a hedge that only works while both options are open; delivery at expiry |
| pledging | the haircut; margin that shrinks when the shares fall; half the F&O margin in cash and the charge on a shortfall; the broker selling shares to cover a debit |
| any | scheduled news; a wide spread; today's loss against the daily limit; too many trades today; the F&O ban period; the odds from SEBI's studies |

The levels: **EXTREME** (the kind of trade that empties accounts), **HIGH**
(serious for a beginner), **CAREFUL** (worth a second look), **INFO** (good
to know). The overall level is the worst one found.

## The facts behind it

Read on 2026-11-15. They change: check them, and say the date when you quote one.

- zerodha.com/charges: brokerage, STT, exchange charges, stamp duty and GST
  for intraday, delivery, futures and options; MTF interest 0.04% a day (Rs 40
  per lakh) on the amount lent; Rs 30 + GST for each pledge request per share
  name; 0.05% a day on a debit balance; Rs 50 + GST an order for an auto
  square-off.
- support.zerodha.com, physical settlement: every stock future and stock
  option is settled by delivery; index contracts in cash. Margins rise from
  four days before expiry. Zerodha may close positions but does not have to.
- support.zerodha.com, pledging: collateral after a haircut, from the previous
  close; half the F&O margin must be cash or cash-equivalent, with 0.035% a
  day plus GST on a shortfall held overnight; a debit for five trading days
  blocks the collateral.
- SEBI: 71% of individual intraday traders in shares lost money in the year
  to March 2023 (press release 13/2024); about 91% of individual traders in
  futures and options did in the year to March 2025 (study of July 2025).

## Rules

- A missing warning is not a green light. The tool only knows what it was
  told: it cannot see news, liquidity or the user's other positions unless
  those flags are given.
- The worst case for a share with a stop is "at your stop". Say every time
  that a stop can fill worse in a gap or a fast market.
- For options the "If it moves" line is left out on purpose: an option's
  price does not move one for one with the share.
- This pack does not trade futures, options or borrowed money, and
  `/trader-risk` blocks them (`allow_options`, `allow_margin`, `allow_short`
  are false). This skill does not change that: it only warns about what the
  user does elsewhere.

## What it never does

- Never places, sizes, changes or blocks an order.
- Never says a trade is safe, good or bad, and never names something to buy
  or sell instead.
- Never guesses a lot size, a price, a margin or an expiry date.
- Never hides a warning because the user is keen on the trade.

## Safety

- Education and tooling, not financial advice. A risk level is arithmetic and
  a checklist, not a recommendation.
- Most people who day trade lose money, and almost all individual traders in
  futures and options do. Knowing the risks does not remove them.
- Nothing in this pack places an order without the user's explicit yes for
  that one order in `/trader-broker`; this skill cannot lead to an order.
