# The course

43 short lessons, from zero. Every lesson has a goal, the points to teach, one
worked example in rupees, check questions with their answers, and where the
idea shows up in the other skills. `learn.py` reads this file: keep the shape
(`### ID Title`, `Goal:`, `- point`, `Example:`, `Check:`, `In the pack:`).

Facts about India that can change were checked on 2026-11-15: the NSE session
times (nseindia.com), Zerodha's charges, MTF interest, pledge fee and the
15:20 square-off (zerodha.com/charges), its rules on pledging and on the
delivery of stock contracts at expiry (support.zerodha.com), the NSE tick
sizes (NSE circular 33/2025), SEBI's study of intraday traders (press release
13/2024) and of F&O traders (July 2025), and how intraday profit is taxed
(Income-tax Act, section 43(5)). Check them again before relying on a number.
Nothing here is financial or tax advice.

## A A business in numbers

### A1 Revenue: the money that comes in
Goal: know what revenue is and that it is not profit.
- Revenue is all the money a business takes in from selling, before any cost is taken off. Sales and turnover mean the same thing.
- Revenue says how big a business is, not whether it earns anything. A shop can sell a lot and still lose money.
- When news says "revenue grew 10%", it means sales this period were 10% higher than the same period before.
Example: A chai stall sells 200 cups a day at Rs 10 a cup. Its revenue for the day is 200 x 10 = Rs 2,000.
Check:
1. A stall sells 150 samosas at Rs 20 each. What is its revenue? :: Rs 3,000 (150 x 20).
2. A company's revenue went up. Does that mean it made more profit? :: No. Revenue is before costs; costs may have gone up more.
In the pack: trader-analyst prints revenue by quarter for US companies; news headlines talk about it in results season.

### A2 Gross profit: after the cost of what you sold
Goal: know gross profit and the cost of goods sold.
- The cost of goods sold is what it cost to make or buy the things that were sold: for chai, the tea, milk, sugar and cups.
- Gross profit = revenue minus the cost of goods sold.
- It answers one question: is each sale worth making at all?
Example: The stall's revenue is Rs 2,000. The tea, milk, sugar and cups for those 200 cups cost Rs 800. Gross profit = 2,000 - 800 = Rs 1,200.
Check:
1. Revenue Rs 5,000, cost of the goods sold Rs 3,500. Gross profit? :: Rs 1,500.
2. Is the stall's rent part of the cost of goods sold? :: No. Rent is paid whether it sells 1 cup or 200; it comes later, as an expense.
In the pack: the same idea as a trade's result before costs: what you made on the price alone.

### A3 Expenses and net profit: what is really left
Goal: know the difference between gross profit and net profit.
- Operating expenses are the costs of running the business that are not tied to one sale: rent, salaries, electricity.
- Operating profit = gross profit minus operating expenses.
- Net profit = what is left after everything, including loan interest and tax. It is the "bottom line", the number the owners actually keep.
- Gross is before costs are taken off, net is after. That is true for a salary, a business and a trade.
Example: Gross profit Rs 1,200. Rent Rs 300, helper Rs 400, gas Rs 100: operating expenses Rs 800, so operating profit is Rs 400. Loan interest Rs 50 and tax Rs 50 leave a net profit of Rs 300.
Check:
1. Gross profit Rs 900, expenses Rs 600, interest and tax Rs 100. Net profit? :: Rs 200.
2. Which is bigger for a healthy business, gross profit or net profit? :: Gross profit. Net is what is left after more costs are taken off.
3. Your salary is Rs 50,000 "gross" and Rs 44,000 arrives in the bank. What is the Rs 44,000 called? :: Net (after tax and other deductions).
In the pack: trader-exit and trader-budget show a trade "after costs", and ticket.py report shows "before costs, costs, after costs": gross and net for a trade.

### A4 Margin: profit as a percent
Goal: read a profit margin.
- A margin is a profit divided by revenue, as a percent. It lets you compare a small business with a big one.
- Gross margin = gross profit / revenue. Net margin = net profit / revenue.
- A high margin means more of each rupee of sales is kept.
Example: The stall: gross margin 1,200 / 2,000 = 60%. Net margin 300 / 2,000 = 15%. Of every Rs 10 cup, Rs 1.50 is finally kept.
Check:
1. Revenue Rs 1,000, net profit Rs 80. Net margin? :: 8%.
2. Shop A earns Rs 50,000 net on Rs 10 lakh of sales, shop B earns Rs 30,000 on Rs 2 lakh. Which has the better margin? :: B (15% against 5%).
In the pack: "margin" has a second, different meaning in trading (borrowed money, lesson H5). This one is about profit.

### A5 Profit is not cash
Goal: know that a profit on paper is not money in hand.
- A sale counts as revenue when it is made, even if the customer pays later.
- So a business can show a profit and still run out of cash, and a business with cash can be making a loss.
- For a trader the same split exists: an open trade's profit is "unrealised" (on paper); it is "realised" only when the trade is closed.
Example: The stall sold Rs 500 of chai to an office on credit. The Rs 500 is in today's revenue and profit, but the cash comes next month.
Check:
1. Your share is up Rs 200 and you have not sold. Is that Rs 200 yours? :: Not yet. It is unrealised; the price can fall back before you sell.
2. Can a profitable company fail to pay its bills? :: Yes, if its customers have not paid it yet: profit is not cash.
In the pack: a trade counts in ticket.py report only when both the buy and the sell are recorded.

## B Companies and shares

### B1 A share: a small piece of a company
Goal: know what you own when you own a share.
- A company is split into equal pieces called shares. Owning shares makes you a part-owner, a shareholder.
- Stock, share and equity mean the same thing in everyday use.
- You make or lose money in two ways: the share's price changes, and the company may pay part of its profit to shareholders.
Example: A company has 1,00,000 shares. You own 100, so you own 0.1% of it.
Check:
1. A company has 10,000 shares and you hold 500. What part do you own? :: 5%.
2. Does owning a share mean the company owes you money? :: No. You are an owner, not a lender. A share can fall to zero.
In the pack: every order is a number of shares of one company; RELIANCE.NS is Reliance's share on the NSE.

### B2 Price and market cap
Goal: know why a Rs 50 share is not "cheaper" than a Rs 5,000 one.
- The market price is what one share last traded at. It changes all day as people buy and sell.
- Market capitalisation (market cap) = price x number of shares. It is what the whole company is valued at.
- The price of one share alone says nothing about size or value: the number of shares matters too.
- Large caps are the biggest companies, then mid caps, then small caps. Smaller companies usually move more and trade less.
Example: Price Rs 500 and 1,00,000 shares: market cap = Rs 5 crore. A share priced Rs 50 with 20,00,000 shares is valued at Rs 10 crore: the "cheap" share is the bigger company.
Check:
1. Price Rs 200, 50 lakh shares. Market cap? :: Rs 100 crore.
2. Share A is Rs 30, share B is Rs 3,000. Which company is bigger? :: You cannot tell from the price; you need the number of shares.
In the pack: the scanner's Nifty lists are the largest companies by market cap.

### B3 Dividends, bonus shares and splits
Goal: know three things companies do with shares, and that two of them do not make you richer.
- A dividend is part of the profit paid in cash to shareholders, so much per share.
- A split cuts each share into more shares; the price falls in the same proportion. A bonus issue gives extra shares free; the price also adjusts.
- After a split or a bonus you hold more shares at a lower price: the value is the same. Charts are adjusted so the old prices line up.
- On the "ex-date" the price drops by about the dividend, because buyers from that day do not get it.
Example: A dividend of Rs 10 a share on 100 shares pays Rs 1,000. In a 1-into-2 split, 100 shares at Rs 500 become 200 shares at Rs 250: still Rs 50,000.
Check:
1. You hold 50 shares at Rs 400 and the company splits each share into 2. What do you hold? :: 100 shares at about Rs 200: the same Rs 20,000.
2. A share falls 2% on its ex-dividend date with no news. Is that a crash? :: No. The price adjusts for the dividend that is being paid out.
In the pack: a sudden gap in a chart can be a split or an ex-date, not a real move. Check the news before trusting a scan.

### B4 IPO and listing
Goal: know how shares come to the market.
- A private company sells shares to the public for the first time in an IPO (initial public offering).
- After that its shares are "listed": anyone can buy and sell them on the exchange.
- When you buy a listed share you buy from another investor, not from the company. The company gets nothing from that trade.
Example: A company sells 10 lakh new shares at Rs 100 in its IPO and raises Rs 10 crore. On listing day the share may open at Rs 130 or Rs 80: the market decides.
Check:
1. You buy 10 shares of TCS on the NSE today. Who gets your money? :: The investor who sold them, not TCS.
2. Is an IPO share sure to rise on listing day? :: No. It can open below the IPO price.
In the pack: the tools need recent price history, so a newly listed share will not work well in the scanner or the time machine.

## C The market

### C1 Exchanges and indexes
Goal: know what the NSE, the BSE, the Nifty and the Sensex are.
- A stock exchange is the marketplace where shares are bought and sold. India has two main ones: the NSE and the BSE.
- An index is one number that tracks a basket of shares. The Nifty 50 follows 50 large companies on the NSE; the Sensex follows 30 on the BSE.
- "The market is up 1%" usually means the Nifty or the Sensex is up 1%.
- On most days most shares move in the same direction as the index.
Example: If the Nifty goes from 24,000 to 24,240, it rose 240 points, which is 1%.
Check:
1. What does the Nifty 50 measure? :: The combined movement of 50 large companies listed on the NSE.
2. The Sensex fell 500 points from 80,000. What percent is that? :: About 0.6% (500 / 80,000).
In the pack: symbols ending in .NS are NSE shares. scan.py universe --nse nifty100 takes its stocks from the Nifty 100 index.

### C2 Broker, demat account and SEBI
Goal: know who stands between you and the exchange.
- You cannot trade on the exchange directly. A broker (Zerodha is one) sends your orders to it.
- A trading account is where you place orders. A demat account is where your shares are kept, in electronic form, at a depository (CDSL or NSDL).
- SEBI is the regulator: it makes the rules for exchanges, brokers and listed companies.
- The broker charges brokerage for each trade; the government and the exchange add their own charges (lesson I1).
Example: You buy 10 shares through Zerodha. Zerodha sends the order to the NSE, the money leaves your trading account, and the shares appear in your demat account.
Check:
1. Where are your shares kept? :: In your demat account, in electronic form.
2. Who makes the rules that brokers must follow? :: SEBI.
In the pack: trader-broker writes tickets for Zerodha (Kite) for .NS shares. It never sends an order without your yes.

### C3 Trading hours and settlement
Goal: know when the market is open and when a trade is final.
- The NSE trades shares from 9:15 in the morning to 3:30 in the afternoon, Monday to Friday, except on its holidays.
- Before that, 9:00 to 9:15 is the pre-open session where the opening price is set. After the close, 3:30 to 4:00 is the closing session.
- Settlement is the exchange of money and shares after a trade. India settles on T+1: one trading day after the trade.
- If you buy and sell the same share on the same day, nothing is delivered: only the difference in money changes hands.
Example: You buy shares on Monday and keep them. They reach your demat account on Tuesday (T+1).
Check:
1. What are the normal trading hours of the NSE? :: 9:15 am to 3:30 pm, Monday to Friday.
2. You buy on Thursday and hold. When are the shares in your demat account? :: Friday, if it is a trading day (T+1).
In the pack: for a .NS symbol every tool uses India time, 9:15 to 15:30, and the NSE holiday list. alerts.py clock RELIANCE.NS says if the market is open.

### C4 Delivery and intraday
Goal: know the two ways to buy a share and why the difference matters.
- Delivery: you buy and keep the shares for days or years. You pay the full price. At Zerodha this is the product type CNC.
- Intraday: you buy and sell within the same day. At Zerodha this is the product type MIS.
- An intraday position you have not closed is closed for you by the broker near the end of the day: Zerodha does it at 3:20 pm and charges Rs 50 plus GST for each order it has to place.
- Intraday is also called day trading. Holding overnight is not possible with MIS.
Example: You buy 15 shares as MIS at 9:40 and forget them. At 3:20 Zerodha sells them at whatever the price is and charges the square-off fee.
Check:
1. Which product type do you pick at Zerodha to buy and keep a share for a year? :: CNC (delivery).
2. Why does this pack close every trade by 3:15? :: Because Zerodha closes intraday positions itself at 3:20 and charges for it; it is better to choose your own exit.
In the pack: every .NS ticket is an intraday (MIS) order, and the flat-by time is 15:15.

## D Prices and orders

### D1 Bid, ask and spread
Goal: know that there are always two prices.
- The bid is the highest price a buyer is offering right now. The ask (or offer) is the lowest price a seller is asking.
- The spread is the gap between them. If you buy at the ask and sell at once at the bid, you lose the spread.
- The LTP (last traded price) is the price of the latest trade. It is one number; the bid and the ask are where you can actually trade next.
- Big, busy shares have a tiny spread. Small, quiet shares can have a wide one: a hidden cost.
Example: Bid 99.90, ask 100.00. You buy 100 shares at 100.00 and sell them straight away at 99.90: you lost Rs 10 without the price "moving".
Check:
1. Bid 250.00, ask 250.50. What is the spread? :: Rs 0.50.
2. You want to sell right now. Which price do you get, the bid or the ask? :: The bid.
In the pack: the tools read last prices from Yahoo, not the bid and ask. Check the real prices in Kite before you act.

### D2 Volume and liquidity
Goal: know why "how much trades" matters as much as the price.
- Volume is the number of shares traded in a period: a day, or one 5-minute candle.
- A liquid share has many buyers and sellers: you can get in and out at once, close to the price you see.
- An illiquid share has few. Your own order can move the price, and you may not be able to sell when you want.
- A price move on high volume is more convincing than one on low volume.
Example: A share trades 50 lakh shares a day: selling 100 is nothing. Another trades 2,000 a day: selling 500 could take minutes and push the price down.
Check:
1. Which is safer for a beginner to day trade, a share that trades 1 crore shares a day or one that trades 5,000? :: The one that trades 1 crore: you can always get out.
2. What does volume measure? :: How many shares changed hands in the period.
In the pack: the scanner has a minimum volume filter, and the entry timer has --min-volume-x. Stay with the Nifty 100 at first.

### D3 Market orders and limit orders
Goal: choose between "now" and "at my price".
- A market order buys or sells at once at the best price available. You are sure to trade, not sure of the price.
- A limit order names your price: buy at this or lower, sell at this or higher. You are sure of the price, not sure to trade.
- The gap between the price you expected and the price you got is called slippage. Market orders have it, most of all in fast or quiet shares.
Example: The ask is 100.00. A market buy fills at about 100.00, or 100.20 if the price is running. A limit buy at 99.50 waits, and may never fill.
Check:
1. You must get out immediately. Which order type? :: A market order.
2. What can go wrong with a limit order? :: It may never fill if the price does not come to it.
In the pack: size.py writes a market order by default and a limit order with --limit. Zerodha's API takes no plain market orders, so placing through a connector needs a limit.

### D4 Stop-loss orders
Goal: know the order that gets you out when you are wrong.
- A stop-loss order waits, and becomes active only when the price reaches a trigger price you set.
- For a share you bought, the stop-loss is a sell order with its trigger below your buy price.
- At Zerodha, SL-M sells at the market once triggered; SL sells with a limit price, so it will not sell far below what you set but can be skipped in a very fast fall.
- A stop is a plan, not a guarantee. If the price jumps past it, you get the next available price.
Example: You bought at 2,442 and put a stop-loss with trigger 2,422.70. If the price falls to 2,422.70 the order wakes up and sells, so the loss is about 19.30 a share.
Check:
1. You bought at Rs 500. Is your stop-loss trigger above or below 500? :: Below.
2. Does a stop-loss guarantee your maximum loss? :: No. In a gap or a fast market it can fill at a worse price.
In the pack: trader-exit sets the stop before you enter; a Zerodha ticket places it as an SL order once the buy has filled.

### D5 Candles, ticks and circuit limits
Goal: read a candle and know two exchange rules about prices.
- A candle shows four prices for a period: open, high, low, close. A 5-minute candle covers 5 minutes of trading.
- Green (or white) means it closed above its open; red (or black) means it closed below.
- The tick size is the smallest step a price can move: Rs 0.10 for an NSE share priced between 1,000 and 5,000, for example. An order at a price off the tick is refused.
- A circuit limit (price band) is the most a share may rise or fall in one day, such as 5%, 10% or 20%. At the limit, trading can freeze: you may not be able to sell. Shares that have futures and options have no fixed band.
Example: A 5-minute candle: open 100, high 103, low 99, close 102. It is green, and the price travelled between 99 and 103.
Check:
1. A candle opened at 200 and closed at 195. What colour is it? :: Red: it closed below its open.
2. A share is at its lower circuit and you hold it. What is the danger? :: There may be no buyers: you cannot sell until trading resumes.
In the pack: every tool works on 5-minute candles. trader-exit puts the stop and target on the tick.

## E Reading a company

### E1 EPS and the P/E ratio
Goal: know the two numbers people quote most about a share.
- EPS (earnings per share) = net profit / number of shares. It is the company's profit for each share.
- P/E (price to earnings) = share price / EPS. It says how many rupees investors pay for each rupee of yearly profit.
- A high P/E means investors expect the profit to grow. A low P/E can mean a cheap share or a troubled company.
- P/E helps investors who hold for years. It tells a day trader almost nothing about today.
Example: Net profit Rs 10 crore, 1 crore shares: EPS = Rs 10. At a price of Rs 200 the P/E is 20.
Check:
1. Net profit Rs 50 crore, 5 crore shares. EPS? :: Rs 10.
2. EPS Rs 25, price Rs 500. P/E? :: 20.
In the pack: trader-analyst shows EPS for US companies. For day trades the pack looks at price and volume, not P/E.

### E2 Results season
Goal: know why a share can jump or drop on one day.
- Listed companies publish their results every quarter (three months): revenue, profit and what they expect next.
- The price moves on the surprise: results against what people expected, not good against bad. A good profit can still send a share down.
- On results day and the day after, moves are bigger and faster than usual. Stops slip more.
- India's financial year runs from April to March, so the quarters end in June, September, December and March.
Example: Everyone expects a profit of Rs 100 crore. The company reports Rs 110 crore, a record, but says next quarter will be weak. The share falls 5%.
Check:
1. A company reports record profit and its share falls. How can that be? :: The market expected more, or it did not like the outlook.
2. Should a beginner day trade a share on its results day? :: Better not: moves are bigger and less predictable.
In the pack: trader-news tags headlines about earnings. Check it before every entry.

## F The economy

### F1 Inflation
Goal: know what inflation is and why it matters to savings and shares.
- Inflation is prices rising over time. With 6% inflation, what cost Rs 100 last year costs about Rs 106 now.
- Money that earns less than inflation loses buying power even though the number grows.
- India measures it with the CPI (consumer price index), published every month.
- High inflation usually leads the central bank to raise interest rates (next lesson), which markets dislike.
Example: Your savings account pays 3% and inflation is 6%. After a year Rs 100 has become Rs 103, but it buys what Rs 97 bought before.
Check:
1. Inflation is 5%. A basket of groceries cost Rs 1,000 last year. About how much now? :: Rs 1,050.
2. Your money earns 4% while inflation is 6%. Are you getting richer? :: No. Your buying power falls by about 2% a year.
In the pack: an inflation number that surprises can move the whole market at once. trader-news tags such headlines as macro.

### F2 Interest rates and the RBI
Goal: know who sets interest rates and what they do to share prices.
- The RBI (Reserve Bank of India) is the central bank. Its repo rate is the rate at which it lends to banks.
- When the repo rate goes up, loans cost more: people and companies borrow and spend less. That slows inflation, and usually weighs on share prices.
- When it goes down, borrowing is cheaper, which usually helps shares.
- The RBI's committee announces its decision every two months. Markets can move sharply on those days.
Example: A company has a Rs 100 crore loan. If its interest rate goes from 9% to 10%, it pays Rs 1 crore more a year, straight out of profit.
Check:
1. What is the repo rate? :: The rate at which the RBI lends money to banks.
2. Rates are raised by surprise. What is the usual first reaction of share prices? :: They fall.
In the pack: on an RBI policy day, expect bigger moves around the announcement. It is a reasonable day to stay out.

### F3 GDP and the budget
Goal: know two big-picture words in the news.
- GDP (gross domestic product) is the value of everything a country produces in a year. GDP growth is how fast the economy is growing.
- A growing economy means companies can sell more, which supports share prices over years.
- The Union Budget, presented on 1 February, sets the government's taxes and spending. Tax changes on shares or on an industry move prices that day.
- A recession is a period when the economy shrinks.
Example: If GDP grows 7% in a year, the country produced 7% more goods and services than the year before.
Check:
1. What does GDP growth of 6% mean? :: The economy produced 6% more than in the previous year.
2. Why do traders watch the Budget? :: Changes in taxes and spending can move the whole market or single industries on the day.
In the pack: Budget day is another day with unusual moves. The risk limits stay the same; your caution should go up.

### F4 The rupee and the big investors
Goal: know two forces that move Indian shares from outside.
- The exchange rate is the price of one currency in another: how many rupees one US dollar costs.
- A weaker rupee helps companies that earn in dollars (software exporters) and hurts those that pay in dollars (oil importers, airlines).
- FIIs (foreign institutional investors, also called FPIs) and DIIs (domestic institutions such as mutual funds) trade in huge sizes. Their buying and selling moves the market.
- When foreign investors sell heavily, the index usually falls and the rupee weakens.
Example: A software company bills 1 million dollars. At Rs 83 a dollar that is Rs 8.3 crore; at Rs 85 it is Rs 8.5 crore, with no extra work.
Check:
1. The rupee weakens against the dollar. Is that good or bad for a company that earns in dollars? :: Good: each dollar brings more rupees.
2. Who are FIIs? :: Foreign institutions that invest in Indian markets.
In the pack: these explain the mood of the whole market on a day. They do not decide a single trade.

## G Trading basics

### G1 Investing, trading and day trading
Goal: know what kind of activity this pack is for.
- Investing: buying part of a business and holding for years, for its growth and dividends.
- Trading: buying and selling over days or weeks to gain from price moves.
- Day trading (intraday): opening and closing a trade within one day. No position is held overnight.
- Day trading is the hardest of the three. SEBI found that 71% of individual intraday traders in shares lost money in the year to March 2023.
- A long trade buys first and gains if the price rises. A short trade sells first and gains if it falls. This pack is long only.
Example: An investor buys a share at Rs 500 and holds five years. A day trader buys it at 10:00 at Rs 500 and sells at 11:30 at Rs 504.
Check:
1. You buy at 9:45 and sell at 2:10 the same day. What kind of trading is that? :: Day trading (intraday).
2. Out of 10 individual intraday traders, about how many lost money in SEBI's study? :: About 7.
In the pack: the whole pack is for long intraday trades. Practice mode exists because most people lose.

### G2 Trend, support and resistance
Goal: read three basic shapes in a chart.
- A trend is the general direction of the price: up (higher highs and higher lows), down, or sideways.
- Support is a price level where falling prices have stopped before, because buyers showed up there.
- Resistance is a level where rising prices have stopped before, because sellers showed up.
- These are habits of the crowd, not laws. Levels break. They are useful for placing a stop and a target.
Example: A share has turned back down from 500 three times this week. 500 is resistance. If it closes above 500, buyers have finally beaten the sellers there.
Check:
1. A share keeps bouncing up from Rs 240. What is Rs 240 called? :: Support.
2. Is a support level guaranteed to hold? :: No. It is only where buyers appeared before.
In the pack: the scanner's daily setups (20-day high breakout, reclaiming an average) are built from these ideas.

### G3 Breakouts and the opening range
Goal: understand the one setup this pack trades most.
- A breakout is the price moving above resistance (or below support) and staying there.
- The opening range is the high and the low of the first minutes of the day: here, the first 15 minutes, 9:15 to 9:30.
- An opening-range breakout: after 9:30, a 5-minute candle closes above the opening range's high. That close is the entry signal.
- A candle that only pokes above the high and closes back inside is not a breakout. Many breakouts fail: the price comes back. That is why the stop is set first.
Example: From 9:15 to 9:30 a share trades between 2,410.50 and 2,434.90. At 9:40 a candle closes at 2,442, above 2,434.90: the breakout.
Check:
1. The opening range is 100 to 104. A candle goes to 105 and closes at 103.50. Is that a breakout? :: No. It must close above 104.
2. Why is the stop decided before the entry? :: Because many breakouts fail, and you must know where you get out before you are in.
In the pack: trader-scanner finds these, trader-entry times them bar by bar, trader-timemachine shows how often they worked on that share.

## H Risk

### H1 Stop, target and risk a share
Goal: define a trade by three prices.
- Entry: the price you buy at. Stop: the price where you accept you were wrong and sell. Target: the price where you take the profit.
- Risk a share = entry minus stop. It is what you lose on each share if the stop is hit.
- All three are decided before you buy. Deciding the stop after buying is how small losses become big ones.
- Never move a stop further away once you are in.
Example: Entry 2,442.00, stop 2,422.70, target 2,461.30. Risk a share = 2,442.00 - 2,422.70 = Rs 19.30.
Check:
1. Entry Rs 800, stop Rs 790. Risk a share? :: Rs 10.
2. The price falls towards your stop. Should you move the stop lower to "give it room"? :: No. The stop was your plan; moving it only makes the loss bigger.
In the pack: trader-exit writes the entry, stop, target and risk a share to trader/plan.json before anything is bought.

### H2 R and reward to risk
Goal: measure every trade in units of what you risked.
- 1R is the amount you risk on the trade. Results are counted in R: +2R means you made twice what you risked, -1R means you lost what you risked.
- Reward to risk = (target minus entry) / (entry minus stop). At 1.0 you stand to make what you risk; at 2.0, twice as much.
- Counting in R lets you compare a Rs 500 trade with a Rs 50,000 one.
- Costs always pull the result down: a planned 1.0 is less after brokerage and taxes (lesson I2).
Example: Risk a share Rs 19.30. A target at 2,461.30 is 19.30 above the entry: reward to risk 1.0, a "1R target". A target at 2,480.60 would be 2R.
Check:
1. Entry 100, stop 98, target 106. Reward to risk? :: 3.0 (6 of reward for 2 of risk).
2. You risked Rs 400 and lost Rs 400. What is that in R? :: -1R.
In the pack: trader-exit takes targets as 1R, 2R and so on; trader-risk blocks a trade under your min_reward_risk; the report shows each trade in R.

### H3 Position size: how many shares
Goal: let the stop decide the size, not your mood.
- Decide first the most you accept to lose on one trade: the max loss per trade. A common starting point is about 1% of the money set aside for trading.
- Shares = max loss per trade / risk a share, rounded down.
- A far stop means fewer shares; a near stop means more. The loss at the stop stays the same.
- Other limits can make it smaller still: the biggest position you allow, and the cash you have.
Example: Max loss Rs 500, risk a share Rs 19.30: 500 / 19.30 = 25.9, so 25 shares at most. If the position limit only allows 15 shares, you buy 15 and the loss at the stop is 15 x 19.30 = Rs 289.50.
Check:
1. Max loss Rs 300, risk a share Rs 6. How many shares? :: 50.
2. Your stop is twice as far away as usual. What happens to the number of shares? :: It halves, so the loss at the stop is the same.
In the pack: trader-budget does exactly this and says which limit decided the size.

### H4 Win rate and expectancy
Goal: know why winning often is not the same as making money.
- The win rate is the share of your trades that win.
- Expectancy is the average result of a trade: (win rate x average win) minus (loss rate x average loss).
- A trader who wins 40% of the time can make money if wins are twice the size of losses. One who wins 60% can lose money if losses are bigger than wins.
- A few trades prove nothing. Judge a method over dozens of trades, after costs.
Example: Win 40% of trades at +2R, lose 60% at -1R: 0.4 x 2 - 0.6 x 1 = +0.2R a trade on average. Win 50% at +0.76R and lose 50% at -1.13R (a 1R plan after costs): a loss of about 0.19R a trade.
Check:
1. You win 30% of trades at +3R and lose 70% at -1R. Expectancy? :: +0.2R a trade (0.9 - 0.7).
2. A method wins 70% of the time. Is it surely profitable? :: No. It depends on how big the losses are next to the wins.
In the pack: ticket.py report gives the win rate, average win and average loss. trader-timemachine estimates the odds before a trade.

### H5 Leverage: trading with borrowed money
Goal: know why leverage, futures, options and pledging are dangerous for a beginner.
- Leverage means controlling more shares than your money could buy, with the broker lending the rest. The money you put up is called margin.
- Leverage multiplies everything: with 5 times leverage a 2% move against you is a 10% loss of your own money. You can lose more than you put in.
- Futures and options (F&O) are contracts with leverage built in. SEBI found that about 91% of individual traders in them lost money in the year to March 2025.
- Pledging means handing your own shares to the broker as security to get margin. If the trade goes wrong, the broker can sell those shares.
- When your margin is no longer enough, the broker asks for more money (a margin call) or closes your position at whatever the price is.
Example: You have Rs 10,000 and use 5 times leverage to hold Rs 50,000 of shares. The price falls 2%: you lose Rs 1,000, which is 10% of your money.
Check:
1. With 4 times leverage, the share falls 5%. How much of your own money is lost? :: About 20%.
2. What is pledging? :: Giving your shares to the broker as security in return for margin to trade with.
3. Out of 10 individual F&O traders, about how many lost money in SEBI's study? :: About 9.
In the pack: leverage is off: "allow_margin", "allow_options" and "allow_short" are false, and trader-risk blocks such orders. Leave them off while you learn. Module K goes through futures, options, MTF and pledging one by one, and trader-guard warns before any such trade.

## I Costs and tax in India

### I1 What every trade costs
Goal: name each charge on an intraday trade at Zerodha.
- Brokerage: the broker's fee. For intraday shares, 0.03% of the order's value or Rs 20, whichever is lower, on the buy and again on the sell.
- STT (securities transaction tax): a tax of 0.025% on the sell side of an intraday trade.
- Exchange transaction charge (0.00307% on the NSE) and SEBI's fee (Rs 10 for each crore traded): tiny, on both sides.
- Stamp duty: 0.003% on the buy side.
- GST: 18% on the brokerage, the exchange charge and SEBI's fee.
- Together: about 0.1% of the trade's value for a buy and a sell. Small each time, large over hundreds of trades.
Example: Buy 1 share at 2,442.00 and sell it at 2,461.30: brokerage 1.47, STT 0.62, exchange 0.15, stamp duty 0.07, GST 0.29. Total Rs 2.60.
Check:
1. Which charge is the broker's own fee? :: Brokerage.
2. Is STT charged on the buy or the sell of an intraday trade? :: The sell.
3. Roughly what share of a trade's value do all the charges take for a buy and a sell? :: About 0.1%.
In the pack: the rates are in NSE_CHARGES in the tools and in config.nse.example.json. Check them against zerodha.com/charges now and then.

### I2 Gross and net result of a trade
Goal: always judge a trade after costs.
- The gross result is what the price move gave you: (sell price minus buy price) x shares.
- The net result is the gross result minus all the charges. Only the net result reaches your account.
- Costs are paid on winners and losers alike: they shrink every win and deepen every loss.
- So a plan that risks 1 to make 1 before costs is worse than even after costs.
Example: One share, risk 19.30. A win: +19.30 gross, +16.70 net. A loss: -19.30 gross, -21.88 net. Reward to risk after costs is 0.76, and you would need to win about 57% of such trades just to break even.
Check:
1. Gross profit on a trade Rs 300, charges Rs 40. Net? :: Rs 260.
2. Gross loss Rs 300, charges Rs 40. Net? :: A loss of Rs 340.
3. Why does a 1 to 1 plan lose money at a 50% win rate? :: Because costs make each win smaller than each loss.
In the pack: the "After costs" lines in trader-exit and trader-budget, and the three columns of ticket.py report.

### I3 Tax on intraday profit
Goal: know that trading profit is taxed and how, in outline.
- In India, profit from intraday trading in shares is treated as speculative business income, not as capital gains.
- It is added to your other income and taxed at your income-tax slab rate. Charges such as brokerage can be deducted as expenses.
- A loss from intraday trading can be set off only against speculative profit, and carried forward for four years.
- Traders usually have to file the ITR-3 form. Keep the broker's reports for the whole year.
- This is an outline, not advice: the rules have details and change. Ask a chartered accountant (CA) before you file.
Example: Your salary is taxed in the 20% slab and you made a net intraday profit of Rs 10,000 this year. Roughly Rs 2,000 of it goes in tax.
Check:
1. Is intraday profit taxed like a long-term investment gain? :: No. It is speculative business income, taxed at your slab rate.
2. You made an intraday loss this year. Can it reduce your salary income for tax? :: No. It can only be set off against speculative profit, now or in the next four years.
In the pack: nothing in the pack does tax. ticket.py report and Zerodha's tax P&L statement are what you take to a CA.

## J Using this pack

### J1 The flow of the skills
Goal: know what each skill does and in which order.
- trader-scanner finds shares whose chart matches a setup. trader-news shows what is being said about one of them.
- trader-entry watches that share and says the moment the setup triggers. trader-exit sets the stop and the target before you buy.
- trader-timemachine shows how such trades have gone on that share. trader-budget works out how many shares.
- trader-risk checks the order against your limits. trader-broker shows the ticket and asks for your yes.
- trader-alerts watches the stop, the target and the 15:15 flat-by time while the trade is open.
Example: Scan the Nifty 100 at 10:00, pick one hit, read its news, check the entry, plan the exit, replay it, size it, risk-check it, then the ticket.
Check:
1. Which skill decides how many shares you buy? :: trader-budget.
2. Which skill is the only one that can lead to an order? :: trader-broker, and only after trader-risk passes and you say yes.
In the pack: each skill writes a file in the trader/ folder that the next one reads.

### J2 Practice mode and reading a ticket
Goal: use the pack safely before any real money is involved.
- "paper": true in trader/config.json is practice mode. For Indian shares nothing is sent to Zerodha: the trade is only written in the pack's own log.
- A ticket shows the order in plain words: what, how many, the stop-loss, the target, and the max loss if the stop fills.
- READY means trader-risk passed this exact order today. BLOCKED means it broke one of your limits, and the ticket says which.
- Real orders need "paper": false, which only you set, and then your yes for each single order.
Example: "BUY 15 TCS.NS, market / stop-loss 2422.70 / take-profit 2461.30 / max loss about Rs 289.50": 15 shares, out at 2,422.70 if wrong, out at 2,461.30 if right.
Check:
1. In practice mode, is anything sent to Zerodha? :: No. The trade exists only in the pack's log.
2. A ticket says BLOCKED. What do you do? :: Read the reason; change the order or your limits and check again. Do not place it by hand.
In the pack: stay in practice mode until the report shows you can follow your own rules for a few weeks.

### J3 The report and the usual mistakes
Goal: learn from your own trades instead of your memory.
- ticket.py report lists each closed trade: before costs, costs, after costs, and the result in R. Read the after-costs total first.
- Revenge trading: trading bigger or more often to win back a loss. The daily loss limit and the trade limit exist to stop it.
- Moving the stop, adding to a losing trade, and trading without a plan turn small losses into large ones.
- Overtrading: every extra trade pays costs. Fewer, planned trades usually do better.
- Being bored, being afraid of missing out, or wanting to be right are feelings, not setups.
Example: A week of 10 trades: gross result +Rs 150, costs Rs 390, net result -Rs 240. The trades "worked"; the costs ate them.
Check:
1. You lost twice this morning and want to double the size on the next trade. What is this called? :: Revenge trading.
2. Which line of the report tells you what really happened to your money? :: The after-costs line.
In the pack: trader-risk enforces max_daily_loss_usd and max_trades_per_day so that a bad day stays a small one.

## K Futures, options and borrowed money

### K1 Futures
Goal: know what a future is and why a small move is a big loss.
- A future is a contract to buy or sell a share or an index at a fixed price on a set date. You do not pay the full value: you put down a margin, a fraction of it.
- Futures trade in lots: a fixed number of shares per contract, set by the exchange. The lot size changes from time to time: read it in Kite, never from memory.
- Each day the gain or loss on the whole contract is added to or taken from your account. This is called mark to market.
- Because the contract is worth many times your margin, the loss can be bigger than the money you put down.
Example: One lot of 65 of an index future at 24,550 is a contract worth 65 x 24,550 = Rs 15,95,750. A fall of 1% costs Rs 15,957.50, whatever margin you put down.
Check:
1. A future's lot is 500 shares and the price is Rs 1,000. What is one contract worth? :: Rs 5,00,000.
2. That contract's price falls 2%. How much do you lose? :: Rs 10,000.
3. Can you lose more than the margin you put down on a future? :: Yes. The loss is on the whole contract value.
In the pack: the pack does not trade futures. trader-guard shows what a 1%, 2%, 5% and 10% move would cost before you place one yourself.

### K2 Options: calls and puts
Goal: know what an option is and what the buyer pays for.
- An option is a contract that gives its buyer the right, but not the duty, to buy or sell at a fixed price (the strike) until a set date (the expiry).
- A call is the right to buy: it gains when the price rises. A put is the right to sell: it gains when the price falls.
- The price of the option is the premium. The buyer pays it and can never lose more than that.
- Options also trade in lots, and the premium is quoted per share: the cost is premium x lot size x lots.
Example: You buy one lot (65) of a 24,600 call at a premium of Rs 120: you pay 65 x 120 = Rs 7,800. If the index is at 24,800 at expiry the option is worth 200 x 65 = Rs 13,000, a profit of Rs 5,200. If it is at 24,600 or lower, the option is worth nothing and the Rs 7,800 is gone.
Check:
1. You expect a share to fall. Which option gains from that, a call or a put? :: A put.
2. A premium is Rs 40 and the lot is 250. What does one lot cost? :: Rs 10,000.
3. What is the most the buyer of an option can lose? :: The premium paid.
In the pack: trader-guard takes --option call or put, --strike, --price (the premium) and --lot-size, and shows the premium as the worst case.

### K3 Buying and selling options
Goal: know why the two sides of an option carry very different risks.
- The buyer pays the premium. The loss is limited to it, but an option loses a little value every day (time decay) and is worth nothing at expiry unless the price has passed the strike. You can be right about the direction and still lose.
- The seller (also called the writer) receives the premium and keeps it if the option expires worthless. That happens often, which is what makes selling look easy.
- But the seller must pay whatever the option becomes worth. For a call sold, there is no limit to that. For a put sold, it can be many times the premium.
- So the seller needs a large margin, and can be asked for more when the price moves against them.
Example: You sell one lot of 500 of a 1,300 put at Rs 12 and receive Rs 6,000. If the share is at 1,200 at expiry you must pay (1,300 - 1,200) x 500 = Rs 50,000: a loss of Rs 44,000 to earn Rs 6,000.
Check:
1. Who can lose more than the premium, the buyer or the seller of an option? :: The seller.
2. The price has not moved for a week. What has happened to the value of an option you bought? :: It has fallen: time decay.
3. You sold a call and the price doubles. Is your loss limited? :: No. A sold call has no limit to its loss.
In the pack: trader-guard marks an uncovered option sale EXTREME, and shows the most it can make next to the most it can lose.

### K4 Margin, MTF and pledging
Goal: know three ways of trading with more than your own money, and what each costs.
- Margin is the money the broker blocks as security for a position. If the position loses, the broker asks for more (a margin call), or closes it at whatever the price is.
- MTF (margin trading facility): you buy shares for delivery and the broker lends part of the price. Zerodha charges 0.04% a day (Rs 40 per lakh) on what it lends, and the shares stay pledged to it.
- Pledging: you hand shares you own to the broker as security and get margin to trade with, less a cut called the haircut. Each pledge request costs Rs 30 plus GST per share name.
- For futures and options, half the margin must be in cash: a shortfall held overnight is charged 0.035% a day plus GST.
- In all three, a fall in price hurts twice: the trade loses, and the security behind it shrinks. The broker can sell your shares to cover what you owe.
Example: You buy shares worth Rs 1,33,000 with Rs 40,000 of your own money through MTF. The broker lends Rs 93,000: about Rs 37.20 of interest a day, Rs 1,116 a month, whether the shares rise or fall.
Check:
1. What is a margin call? :: The broker asking for more money because the position's losses have used up the margin.
2. You pledge shares and they fall 10%. What happens to your margin? :: It falls too.
3. The broker lends you Rs 2,00,000 under MTF at 0.04% a day. What is the interest for one day? :: Rs 80.
In the pack: borrowed money is off in the pack ("allow_margin": false). trader-guard has --kind mtf and --kind pledge for what you do outside it.

### K5 Expiry and delivery
Goal: know what happens when a contract ends.
- Every future and option has an expiry date. After it the contract no longer exists.
- An option is in the money when using it would pay: a call whose strike is below the price, a put whose strike is above. Otherwise it is out of the money and expires worthless.
- Index contracts are settled in cash: only the difference in money changes hands.
- Stock futures and in-the-money stock options are settled by delivery: at expiry you must pay for, or hand over, the whole lot of shares.
- The margin on stock contracts rises from four days before expiry, and the broker may close the position for a fee. Close stock contracts before the expiry week.
Example: You hold one lot of 500 of a 1,300 call on a share that is at 1,330 at expiry. It is in the money, so you must buy 500 shares at 1,300: Rs 6,50,000, from an option that cost a few thousand.
Check:
1. A call has a strike of 500 and the share is at 480 at expiry. What is the option worth? :: Nothing: it is out of the money.
2. Which are settled by handing over shares at expiry, index contracts or stock contracts? :: Stock contracts.
3. Why close a stock option before the expiry week? :: Margins rise, and at expiry you may have to pay for or deliver the whole lot.
In the pack: trader-guard counts the days to --expiry and warns from four days out on a stock contract, more strongly in the last two.
