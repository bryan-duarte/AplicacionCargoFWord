# Business Reasoning and Considerations

This document outlines the business reasoning and considerations that went into designing the portfolio rebalancing system. The focus is on considering what is NOT immediately evident in a real-world use case scenario.

## Scenario Simulation

**First Day Scenario:**
"Hello Bryan, welcome to the team! You'll be joining the group working on 'Portfolio Juggler' functionality that balances portfolios. Go ahead and contribute."

Below is what I would bring to the conversation, and in some cases, my approach to the points.

## Reasoning

<...deep human thinking mode>

### Initial Questions

**1. Broker Commissions. Which broker does the platform use?**

**2. Can I buy fractional shares?**

The platform uses Alpaca Securities (good name), which does allow fractional trading and states they don't charge commissions. They apparently have a decent API.

**3. Do capital gains taxes in Chile and Mexico affect the use case?**

Absolutely, muchacho. SII and SAT see everything.

**My opinion to the team:** Whoever activates the feature should know the tax impact, but we need to make their life easy regarding collecting the income and losses obtained from these auto-executed asset sales.

### Additional Considerations

- The minimum for an asset on the platform is $1 USD.
- The broker account type is likely margin, not cash.

A margin account enables "atomic rebalancing": selling Meta and buying Apple instantly, using the money from the sale before it officially settles.

This account type leads us to "The Big Mamma Rule":

If an account has less than $25,000 USD (Retail Account), it cannot make more than 3 "Day Trades" (buying and selling the same stock on the same day) within a 5-business-day period.

**My opinion to the team:** People, to avoid constant rebalancing, we need a rebalancing trigger and handle retail account limits at the broker. We could use:
- Percentage variation in portfolio participation that triggers rebalancing.
For example, only rebalance differences of 1% or more.

<.../deep human thinking mode>

## Team Decisions

**Is portfolio rebalancing something that happens in the background, "your portfolio rebalances while you watch Netflix," or should it be an "Execute Rebalance" feature that the user runs?**

**My opinion to the team:** Full support for auto-rebalancing while watching Netflix.

At the system level, when there's a change in the price attribute of a stock, it should launch an evaluation (or not) of portfolios containing that stock to rebalance them if appropriate.

**What options does Alpaca have to avoid making requests to their endpoint constantly? Is there a webhook that notifies me of significant price changes in a stock?**

Does anyone have historical data on price changes for the stocks we have available in the feature? This way we could define rebalancing check times based on history. [-Bryan proceeds to get the data from the deep web if the platform doesn't have it-]

I saw Alpaca has a websocket to subscribe to events every 1 minute.

But, given the feature's value proposition, is it worth it? If yes, we need to consider the cost of scaling at the server level based on the variety of assets and portfolios managed.

**EDGE CASE:** If the WallStreet Bets reddit crowd decides to pump and dump a stock, should our system react to this or should it magically ignore it?

**My opinion to the team:** Yes, it should affect it. Clearly it's not pleasant, but it's part of investing and the trading module.

## Implementation Requirements

**The architecture should (IMO) be event-based:** Significant price changes in stocks will trigger rebalance evaluations.

There should be a websocket listening every 1 second to price variations in portfolio stocks. We should only listen to symbols in our portfolios, not all broker stocks.

After a significant change in a stock, portfolio change evaluation should be triggered. If evaluation shows something to consider, rebalancing should execute to maintain the percentage distribution of stocks in the collection.

**Handle thresholds to avoid over-evaluating rebalances:**
At what percentage of stock price variation should we evaluate if rebalancing is needed? Get from config, use 1%.
