
# CMU Physics 🐚🐚🐚 
This repo documents our research, strategy development and tools for **Prosperity 3 (2025)**, with ~12,000 teams we finished 7th Globally & 1st USA.

<br>

## 📜 What is Prosperity?

Prosperity is a 15-day long trading competition where players earn "seashells" to grow their "archipelago" in 5 rounds (each 3 days long). Each round new products are introduced that each have their own unique properties resembling real world tradable assets; you can always trade products from previous rounds so it's a game of finding alpha and optimizing previous strategies. To trade these products we researched the products (using provided sample data) then wrote and submitted a python file that performed systematic trades. Every round also had a manual trading aspect to it these challenges were typically centered around game theory decisions and had us playing around other participants' choices. 

At the end of each round, the algorithmic trading scripts and manual trading challenges were evaluated and added to our islands' PNL.

[Prosperity 3 Wiki](https://imc-prosperity.notion.site/Prosperity-3-Wiki-19ee8453a09380529731c4e6fb697ea4)

<br>

## 👥 The Team
| Chris Berman | [@chrispyroberts](https://github.com/chrispyroberts) |

| Nirav Koley | [@n-kly](https://github.com/n-kly) |

| Aditya Dabeer | [@Aditya-Dabeer](https://github.com/Aditya-Dabeer) |

| Timur Takhtarov | [@timtakcs](https://github.com/timtakcs) | 

<br>

## 🗂 Repo Structure
Our code is split into the rounds that they were built for, all of the EDA, research, manual, and trader code is located within them.

Good luck parsing it, things got a little scrappy near the end...

<br>

## 🧠 What you're probably here for

Below are descriptions for both our algorithmic and manual trading strategies. We tried to play things safe and focused on market neutral strategies (straight line pnl)
<details>
<summary><h2>Round 1</h2></summary>
  
<h3>Algo</h3>

Round 1 introduced 3 new products: Rainforest Resin, Kelp, and Squid Ink. All of these products were relatively distinct but traded like stocks would in the real world -- nothing fancy just an order book and market price.

Rainforest Resin was by far the easiest product to trade, and probably one of the most consistently profitable across the entire competition. The sample data revealed that the fair value hovered exactly around 10,000 seashells, with almost no drift and extremely low volatility (typically deviating by no more than ±4 seashells). Market taking was straightforward: any time there was a bid above 10,000 or an ask below 10,000, we would immediately execute against it. On top of that, the order book had relatively wide spreads, which opened up market making opportunities by posting liquidity just inside the standing bids and asks. One thing we noticed was that there were often bids and asks in the order book at exactly the fair value. We used these orders to our advantage by checking if taking them would reduce our overall position and better balancing our market making and taking position. This small addition boosted our PNL performance quite a bit as often we were fully long or fully short Resin due to the volume of orders.

Kelp was a little more complicated. It displayed some mild price drift and a small but noticeable amount of volatility, making it dangerous to blindly market take at a fixed value. We noticed that there was another market maker always present in the order book, and found that on submission to the website our PNL was calculated based on the mid price of this market participant. This told us that the fair value at any given moment was the mid-price of their market. We copied our market making stratey from resin using this mechanic as the fair value. Because Kelp had such low volatility, often only moving a total of 40 seashells over the course of 10,000 steps, we didn't incoporate any directional aspect as simply market making and taking made so much more.

Then came Squid Ink, which was basically trading meme-coins, with consistent 100 seashells swings in a single step and seemingly no clear pattern. The IMC parrot kept hinting that “there’s a pattern if you look closely,” but to be honest, we don't believe any real exploitable structure existed. We tested a variety of strategies, including rolling z-scores, volatility breakouts, and MACD signals, but none offered any consistent edge. Employing the same market making and taking strategy as Kelp and Resin proved useful, since we found the same mechanic present for squid ink as we did for Kelp, but the massive spikes in price that appeared randomly would either instantly double take away any PNL we had made for the day. We decided to take a gamble on this and see what would happen on the submission day. 

<h3>Manual</h3>

This manual was pretty simple, it was a currency exchange problem were it was possible to exchange currencies in a way to profit of of it.

See [Leetcode 3387. Maximize Amount After Two Days of Conversions](https://leetcode.com/problems/maximize-amount-after-two-days-of-conversions/description/) 😂.

Seriously though, this was a relativley trivial manual and all we had to do was a breadth first search across all possible currency conversions.

<h3>Results and Post-Round Analysis</h3>

First round results were kind of controversial, it was kind of obvious that the round 1 data on the website was actual price history for the first 1000 timestamps on day 1 (instead of 1000 time stamps from previous test days) so a bunch of people ended up hardcoding in their trades on the first 1000 timestamps. This combined with squid ink spiking in the opposite direction as our market making position, meant we actually lost seashells off squid ink and ended up in 771'st place. However, the round was re-run due to the hard-coding being considered cheating and we shot up to 9th place with a total PNL of 107,237 seashells (43,243 algo + 44,340 manual). We got incredibly lucky on the re-run because squid ink spiked in our favor rather than agaisnt it.  The top 3 teams seemed to have some how found something out, that meant they were ~100k seashells ahead of everyone else, but between us and 4th place was only a couple thousand seashells. 

After the round we decided it was too volatile to keep trading squid ink using our current strategy, and adapted it to do market making and taking but only with 10% of our total position allocated at any given moment. This reduced the total PNL made from market making and taking on squid ink by around 50%, but to make up for this, we added in a spike detection indicator, with the hypothesis that the moment price spikes, it will quickly mean-revert. This made our PNL across all days for squid-ink much more stable. For our spike detection algorithm, we used a small window rolling standard deviation on price difference, and when this standard deviation was larger than 20, we would fully enter into the opposite direction price just moved.

![](images/squid_ink.png)


---

</details>

<details>
<summary><h2>Round 2</h2></summary>
  
<h3>Algo</h3>
Round two introduced new products: CROISSANTS, JAMS, DJEMBES, PICNIC_BASKET1 and PICNIC_BASKET2. Specifically, PICNIC_BASKET1 is said to contain 6 CROISSANTS, 3 JAMS and 1 DJEMBE and PICNIC_BASKET2 contains 4 CROISSANTS and 2 JAMS. We quickly realized these products were similar to previous years. We visualized the difference in price between each basket and it's constituents and plotted it to look for any interesting behaviors. The basket premiums looked like they were mean-reverting, and so we used the hard-coded mean of the bottle data with a short rolling window for standard deviation to calculate rolling z-scores, and would enter into short positions on a basket and long the underlying when the z-score went above 20 and long positions on baskets and short the underlying when the z-score dropped below -20. By hedging our position, we could isolate the basket premium and directly trade it.

![](images/basket_premiums.png)

One key part of this round was position sizing. Position limits on the products would not allow us to go long both baskets at the same time while maintaining a perfect hedge. To make up for this, we decided to trade the difference between the premium in the baskets. Entering into fully hedge directional positions on the difference in premiums left us with a position size of 40 to trade basket 2, but we were limited by our remaining underlying position which only allowed us to fully hedge a position of 32 on basket 2. With our remaining position of 32, we traded the premium on basket 2 using the same exact strategy. This left us with a position size of 8 left on basket 2. Rather than let this position size go to waste not not utilize it, we noticed that there was a consistent spread of ~7 in the orderbook for basket 2, and ~10 for basket 1. We decided to market make using a maximum position size of 8 using this remaining position. While the unhedged market making basket position could potentially lose us some money, over backtests it consistently provided 5k extra seashells per day with minimal swings due to directional moves.

There were a few other things that we tried. Chris, who had done the trading challange the previous year and placed 15th, had a suspicion that round 5 was going to be extremely similar to the previous year. Last year, there were bots that would send trade orders on certain products at exactly the top and bottom of the day, so he hypothesized that somewhere in the orderbook on certain timestamps, there would be a signal indicating that the current price is the highest/lowest of the day. 

![](images/squid_ink_trades.png)

We found that for squid ink and croissants was clear that at the high and low of a given day, there was a trade present. This looked like a true signal, the problem was it also incldued many noisy and false signals. Unfortunately we discovered this very close to the end of the round, and didn't have time to write an algorithm that could effectively determine true signals from false ones, so we ended up not using this, and waiting until round 5 to confirm if this was a true signal or not.

<h3>Manual</h3>

This round’s manual was particularly interesting: we had the choice of selecting up to two out of ten available shipping containers, each with different **multipliers** and **inhabitants**. The key mechanic was that your profit from a container depended not just on the container’s treasure multiplier, but also on how many other players chose the same one:

> **PNL = (10,000 × Multiplier) / (Number of inhabitants + % of total selections that picked this container)**

The first container choice was free, but opening a second cost **50,000 SeaShells**.

We realized fairly early on that this wasn’t just a math problem; it was about simulating player behavior. Containers that were underselected would naturally end up with a higher expected value (EV) than those that looked good initially. At first, we tried writing a basic Monte Carlo simulation where agents simply picked the two containers with the highest immediate EV. This rough model didn’t converge well and ended up giving confusing, unreliable numbers. Looking back, this was the right idea but just poorly executed and didn't have the right goal in mind.

We came up with the idea of estimating the **Nash equilibrium** across the crates, using a similiar but simpler greedy Monte Carlo simulation that aimed to predict the base selection rates for each container. 

# TODO ADD PICTURE OF NASH ON CONTAINERS

When we ran the numbers, we found that the Nash equilibrium values for the containers were consistently **below 50,000 SeaShells**, meaning that opening a second container would almost always be a losing play. From this point on, we decided to only focus on selecting **one container**, believing that hedging across two was too risky given the low payouts.

On top of the Nash equilibrium strategy, we built a set of **priors** based on how we thought players would actually behave, the goal with these assumptions was to try and price in how people might act (beyond just following the nash). These alternative strategies ranged a lot from just random selection to phsycolgoical bias (the number 7 & 3 are well-documented to be more 'likeable' to humans and thus picked more frequently when asked to pick a number from 1-10)  Our hypothesis was that:

- 15% of players would play according to Nash equilibrium,
- 50% would choose randomly,
- 20% would gravitate toward “nice numbers” (multipliers like 73, 17, and 37),
- 10% would misread the prompt and simply pick based on initial EV,
- and 5% would follow the flawed Monte Carlo strategy we had initially come up with.

We re-ran a new Monte Carlo simulation based on these priors and recalculated the EVs of all the containers, aiming to account for both rational and irrational human actors. Ultiamtely we chose to only pick the 80x crate (this was a bad idea).

# TODO ADD PICTURE OF UPDATED MONTE CARLO


<h3>Results and Post-Round Analysis</h3>

Looking back, we definitely **underestimated** how many players would stick close to Nash equilibrium, and **overestimated** the randomness in player behavior. Additionally, our simulation didn’t properly prioritize the impact of the "nice numbers" category, which led us to overweight the chances of truly random selections. Our misjudgments here probably contributed the most to our low overall ranking in the manual component of the tournament. However, it wasn't a total loss — we took the lessons from this round, updated our priors accordingly, and built a much stronger player modeling system for future decision-based rounds.

Once again, these results were quite controversial. Some teams found out that the timestamp in which the bots would trade were exactly the same as the previous year. This meant that teams could predict when buy and sell orders would be filled, and they could take the entire bid/ask of an orderbook out and place their own orders below/above them and have them instnatly be filled, leading to millions in profit per round. This, in our opinion and many others, was unfair and not in the spirit of the challange. While only 2 teams found this (they had millions of seashells at this point), the admins once again decided to disallow this sort of hardcoding, and after reviewing the code of many in the top 25, asked teams who they believed were using this to their advantage to submit versions of their algorithms that did not have this hard coding behavior, ultimately causing them to drop many places on the leaderboard. As for us, we moved up into 7th place with 243,083 seashells, making 102,758 seashells from our algo and 33,087 from the manual.

</details>

<details>
<summary><h2>Round 3</h2></summary>


<h3>Algo</h3>

This round introduced 6 new products: Volcanic Rocks, and 5 different Volcanic Rock vouchers with strike prices of 9500, 9750, 10000, 10250, and 10500. These products very closely resembled european option contracts, and were set to expire in in 7 in-game trading days. Chris did the analysis for this round, and using the hint provided on the website to model the volatility smile by plotting the moneyness $m_t$ agaisnt the implied volatility $v_t$. Moneyness was calculated using the following formula $$m_t = log(K / S_t) / \sqrt(TTE)$$ where $K$ is the voucher strike price, $S_t$ is the price of the underlying at some time $t$, and $TTE$ being the time to expiration in years. 

![](images/volatility_smile.png)

Fitting a quadtratic to this we found parameters $a, b, c$ for the equation $v_t = a \cdot m_t^2 + b \cdot m_t + c$ allowing us to predict a 'fair' implied volatility for any a given $m_t$. After coding this up, we found the best way to take advantages of this was to code an agressive market maker using our fitted implied volatility. We also added in functionality to automatically hedge our positions after every timestamp, ensuring that we are only exposed to the implied volatility of a contract. Our backtesting PNL curve was a straight line on most days, indicating that we found a reasonable strategy that is direction-neutral. From our backtests, we were expecting to make ~80k from all voucher products and ~100k from other products.

A few other things we considered this round for algo: 

- Something we considered as part of our analysis was how much we are losing in our long voucher positions due to theta decay. Chris found that the theta decay of the vouchers had a maximum 800 annualized, meaning that holding a voucher for a year, assuming nothing about the underlying or voucher changes, that the value of the voucher would decrease by 800 seashells over the course of the year. So he estimated that the upper bound on how much we would lose due theta decay on a given day if we were fully long 200 of a given voucher was ~430 seashells. (800 seashells per year /  365 days per year * 1 day * 200 vouchers  = ~430 seashells per day per voucher we are fully long). This amount was negligible compared to the 80k we were making on backtests. 

- Since we could hold up to 400 volcanic rocks, and 200 of any voucher, this meant if we went long 2 different vouchers, in the worst case, we could only completely hedge up to 2 vouchers assuming each had a delta of 1. Since we thought that this could get very complicated very quickly, so decided to cap all vouchers at a position size of 80 so we could guarantee that no matter what we would always be fully hedged. 

<h3>Manual</h3>
In this round, we had to place **two bids** to acquire **Sea Turtles' Flippers**. Each turtle accepted the **lowest bid above their reserve price**, where reserves were **uniformly distributed** between **160–200** and **250–320**.

For the **second bid**, a penalty applied if your offer was **below the average** of all second bids, scaling your profit by:

> $$ p = \left(\frac{320 – \text{average bid}}{320 – \text{your bid}}\right)^3 $$

All acquired Flippers could later be sold for **320 SeaShells** each.

For this manual, we took a more systematic approach from the start. First, we isolated the **one-bid scenario** and ran a Monte Carlo simulation for every possible bid between 160 and 320.  
*(Insert picture here.)*

From this, we found that if we were limited to only one bid, it was clearly optimal to set it at **200** — just at the cutoff before the dead zone of 200–250.

Next, we tackled the **two-bid scenario**, initially **ignoring** the impact of the *p* scaling (i.e., assuming no penalty for being under the average second bid). We ran another Monte Carlo simulation where the **first bid** was fixed at **200**, and the **second bid** varied across the full range from 160 to 320.  
*(Insert picture here.)*

At this point, it became clear that **picking 285 for the second bid** was the Nash Equilibrium: if all players played optimally (GTO), they would pick **200** first and **~285** second, ensuring their second bid was just above the reserve range and staying above the average.

However, we realized that some players might attempt to **undercut** the average slightly — placing their second bids just above 285 to exploit players who bid exactly at Nash, thereby pushing their bids below the average and subjecting them to the *p* scaling penalty.

To account for this, we built a new set of **priors**, this time using **continuous probability distributions** rather than discrete categories (since bids could be any number within the range). Our assumptions were:

- **10%** of players would play perfect Nash,
- **25%** would concentrate around the optimal mid-point (tight Nash cluster),
- **49%** would pick values **slightly higher than the GTO price**,
- **1%** would pick completely randomly,
- **15%** would intentionally grief (e.g., bots setting bids at 160 or 320 to skew the distribution, as discussed in Discord).

*(Insert distribution image here.)*

We then modeled these priors and re-simulated outcomes, finding that the **optimal second bid** was approximately **290** — slightly higher than the GTO point to hedge against players trying to outmaneuver Nash bidders.

<br>

<h3>Results and Post-Round Analyysis</h3>
Ultimately, we were quite happy with how this manual turned out. The **actual average** second bid ended up being around **286**, slightly higher than pure GTO but very much in line with our expectations. Looking at the resulting graphs, it was clear that most players aimed for Nash or slightly above it, confirming that our modeling approach and priors were pretty spot-on.

Overall though, this round was absolutely brutal for us as we fell from 7th to 241st, making us all believe that a comeback was impossible. We only made 75,755 on algo and 53,430 on manual, while many of the top teams made >200k on algo. We knew either something was wrong or we had missed something.

- We first realized Jasper's visualizer, which we were using extensively, was having some issue where it would cause the algorithm on submission to use more than 100mb of memory, causing the instance to reboot. This meant all local variables that the algorithm was using to trade would be wiped and re-initialized. This was a problem for our rolling windows containing short-term price movements important for trade entries and hedges on basket and volcanic rock products, causing our trader to effectively buy and sell these products randomly. In future submissions, we decided to remove Jasper's visualizer on our final submission to avoid this issue rather than debug it. 

- Chris then realized we completely missed an extremely profitable trading strategy on volcanic vouchers. The issue was that our quadratic fit for implied volatility stopped being a good model on the submission day (who would have guessed that past data doesn't imply future data), and our model would either severely under or over estimate the actual IV. This meant our trader effectively would enter into a long / short position on IV for a voucher and stay in that position for the whole day. While the IV on the vouchers did spike, the amount of seashells this IV spike corresponded to was very little, so we pretty much made nothing from volcanic rocks by using our fitted model. In the figure below, Chris plotted the IV for bids and asks on different vouchers across time, along with a short rolling window of the mid IV. Using the mean of this rollowing window instead of our quadtratic fit as a model for the fair IV made our backtester PNL shoot up from 80k to 150k on every single day, including the day of submission.

- Chris then also ran some backtests to figure out how much our hedge cost us. Since trading volcanic rock had a spread of 1, every buy/sell effectively cost us 0.5 seashells. By counting the total trades we took while hedging out position, -Chris found that we paying over 40k in spread just to hedge our position. He then tried to make an upper-bound for how much we could lose due to being unhedged. At one point in the day, volcanic rocks moved by 100 in a single step, which assuming a delta of 1, would correspond to a maximum loss of 40k. We decided that because to us price movement appears random, in expectation this will net to 0 and that we would go unhedged on volcanic vouchers in future rounds. This boosted our backtester PNL on all volcanic rock products to 250 per day.

![](images/rocks.png)


</details>

<details>
<summary><h2>Round 4</h2></summary>
Thoughts going in

<br>
  
<h3>Algo</h3>

BLAH BLAH BLAH
<h3>Manual</h3>

In this round, players could open up to **three suitcases** containing prizes. Opening one suitcase was free, but opening a second or third required paying a fixed cost. 

Each suitcase had a **prize multiplier** (up to 100) and a known number of **inhabitants** already selecting it. Profit was calculated as:

> **Profit = (10,000 × Multiplier) ÷ (Number of inhabitants + % of global suitcase selections)**

Costs for opening additional suitcases applied after this division, making careful suitcase selection critical.

This challenge was nearly identical to Round 2, giving us a shot at redemption. We started strong by immediately calculating the **Nash equilibrium** across all suitcases.  
*(Insert Nash picture here.)*

Since the Nash EV was **greater than 50,000** (the cost of opening a second suitcase), we determined it was profitable to **open two suitcases**.

The real challenge came in **modeling human behavior**. Fortunately, players had shared post-analysis from Round 2 on Discord, showing how actual picks compared to Nash predictions.  
*(Insert selection vs. Nash image here.)*

The findings were surprising:
- **Way more players** picked close to Nash than we had expected.
- There was **massive buy pressure** on "nice numbers" like **17** and **73**, confirming our human psychology prior.
- Minor deviations elsewhere seemed due to random noise.

Based on this, we simplified and updated our priors:
- **50–60%** of players would pick according to Nash distribution.
- **5–15%** would concentrate on the most selected parts of Nash.
- **5–10%** would favor the least selected parts (based on over-correcting from last round’s profitable crates).
- **10–15%** would pick randomly.
- **10–15%** would favor "nice numbers" based on human psychology.

Rather than running another Monte Carlo simulation (since this was a discrete problem), we created a **probability distribution** directly across all suitcases. We multiplied base Nash probabilities by the expected deviations from our priors to estimate suitcase popularity mathematically.  
*(Insert probability distribution picture.)*  
*(Insert predicted density sorted by EV picture.)*

Using this model, we selected **suitcases 83 and 47** as our picks.

<br>

This manual went **extremely well** for us. While we didn’t absolutely maximize profits, our approach paid off — our predicted densities were **very close to the actual results**, leading to strong EV predictions and a solid gain in ranking.  
*(Insert predicted vs actual densities/EVs picture.)*

---

</details>

<details>
<summary><h2>Round 5</h2></summary>
Thoughts going in

<br>
  
<h3>Algo</h3>

BLAH BLAH BLAH
<h3>Manual</h3>

For this round, we had to trade on 9 different products and derive sentiments from the 'goldberg' terminal. Trading was not only influenced by **sentiment**, but also incurred increasing **fees** based on how much of each product was purchased:

> **Fee(x) = 120 × x²**, where *x* is the portfolio allocation fraction.

This made optimizing both **selection** and **sizing** critical to maximize profits.

At first, this round seemed purely **vibe-based**. However, after some thought, we realized it was actually a **portfolio optimization** problem in disguise.

The first step was to generate **priors** for how each product's price might move.  
Luckily, we found data online from previous years, and noticed that the tradeable products were almost **identical** to those offered this year. This allowed us to **map historical returns** onto current products. 

However, the instructions were vague — it was unclear whether price movements were **purely player-driven** or **predetermined**. To be cautious:
- We **adjusted** last year’s return data slightly based on **sentiment from Discord** and our **own intuition**.
- We used historical data mostly to **estimate the range of possible movements** rather than directly copying past results.

Once we had reasonable return estimates, we tackled the portfolio allocation. With **9 products** and the **quadratic fee structure**, it was clear that naive brute-force (e.g., a grid search) would be computationally impossible.

Instead, we used **convex optimization** (`cvxpy`) to solve for the **optimal portfolio allocation**, maximizing expected returns while minimizing fee penalties.
# TODO ADD IMAGE OF THE IPYNB TRACE

We also decided to **tone down** the allocation weights slightly for higher-risk products to **mitigate the chance of getting burned** if our return estimates were wrong.


<br>

Overall, for manual we played this round **a bit too safe**. While our returns were solid, we left potential profits on the table by not being aggressive enough in our allocations. Additionally, it turned out that **player behavior had a major impact** on price movements — some products (like Red Flags) moved far more than historical data suggested, likely due to heavy player sentiment.

While it wasn’t our strongest manual, we stuck to a disciplined strategy and don’t regret the decision to prioritize **risk management** over gambling for bigger wins.

---

</details>

## 🏁 Final Thoughts
Something philosophical
