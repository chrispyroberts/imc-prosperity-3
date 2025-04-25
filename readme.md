
# CMU Physics 🐚🐚🐚 
This repo documents our research, strategy development and tools for **Prosperity 3 (2025)**, with ~12,000 teams we finished 7th Globally & 1st USA.

<br>

## 📜 What is Prosperity?

Prosperity is a 15-day long trading competition where players earn "seashells" to grow their "archipelago" in 5 rounds (each 3 days long). Each round new products are introduced that each have their own unique properties resembling real world tradable assets; you can always trade products from previous rounds so it's a game of finding alpha and optimizing previous strategies. To trade these products we researched the products (using provided sample data) then wrote and submitted a python file that performed systematic trades. Every round also had a manual trading aspect to it these challenges were typically centered around game theory decisions and had us playing around other participants' choices. 

At the end of each round, the algorithmic trading scripts and manual trading challenges were evaluated and added to our islands' PNL.

[Prosperity 3 Wiki](https://imc-prosperity.notion.site/Prosperity-3-Wiki-19ee8453a09380529731c4e6fb697ea4)

<br>

## 👥 The Team
| Christopher Berman | [@chrispyroberts](https://github.com/chrispyroberts) |

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

TODO: WRITE THIS

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

BLAH BLAH BLAH

<h3>Results and Post-Round Analysis</h3>


Once again, these results were quite controversial. Some teams found out that the timestamp in which the bots would trade were exactly the same as the previous year. This meant that teams could predict when buy and sell orders would be filled, and they could take the entire bid/ask of an orderbook out and place their own orders below/above them and have them instnatly be filled, leading to millions in profit per round. This, in our opinion and many others, was unfair and not in the spirit of the challange. While only 2 teams found this (they had millions of seashells at this point), the admins once again decided to disallow this sort of hardcoding, and after reviewing the code of many in the top 25, asked teams who they believed were using this to their advantage to submit versions of their algorithms that did not have this hard coding behavior, ultimately causing them to drop many places on the leaderboard. As for us, we moved up into 7th place with 243,083 seashells, making 102,758 seashells from our algo and 33,087 from the manual.

</details>

<details>
<summary><h2>Round 3</h2></summary>
This round introduced 6 new products: Volcanic Rocks, and 5 different Volcanic Rock vouchers with strike prices of 9500, 9750, 10000, 10250, and 10500. These products very closely resembled european option contracts, and were set to expire in in 7 in-game trading days. Chris did the analysis for this round, and using the hint provided on the website to model the volatility smile by plotting the moneyness $m_t$ agaisnt the implied volatility $v_t$. Moneyness was calculated using the following formula $$m_t = log(K / S_t) / \sqrt(TTE)$$ where $K$ is the voucher strike price, $S_t$ is the price of the underlying at some time $t$, and $TTE$ being the time to expiration in years. 

![](images/volatility_smile.png)

Fitting a quadtratic to this we found parameters $a, b, c$ for the equation $v_t = a \cdot m_t^2 + b \cdot m_t + c$ allowing us to predict a 'fair' implied volatility for any a given $m_t$. After coding this up, we found the best way to take advantages of this was to code an agressive market maker using our fitted implied volatility. We also added in functionality to automatically hedge our positions after every timestamp, ensuring that we are only exposed to the implied volatility of a contract. Our backtesting PNL curve was a straight line on most days, indicating that we found a reasonable strategy that is direction-neutral. 

A few other things we considered this round for algo: 
\begin{itemize}
\item Something we considered as part of our analysis was how much we are losing in our long voucher positions due to theta decay. Chris found that the theta decay of the vouchers had a maximum 800 annualized, meaning that holding a voucher for a year, assuming nothing about the underlying or voucher changes, that the value of the voucher would decrease by 800 seashells over the course of the year. So he estimated that the upper bound on how much we would lose due theta decay on a given day if we were fully long 200 of a given voucher was ~430 seashells. (800 seashells per year /  365 days per year * 1 day * 200 vouchers  = ~430 seashells per day per voucher we are fully long). This amount was negligible compared to the 80k we were making on backtests. 
\item Since we could hold up to 400 volcanic rocks, and 200 of any voucher, this meant if we went long 2 different vouchers, in the worst case, we could only completely hedge up to 2 vouchers assuming each had a delta of 1. Since we thought that this could get very complicated very quickly, so decided to cap all vouchers at a position size of 80 so we could guarantee that no matter what we would always be fully hedged. 
\end{itemize}

<br>
  
<h3>Algo</h3>

BLAH BLAH BLAH
<h3>Manual</h3>

BLAH BLAH BLAH

<br>

Results

---

</details>

<details>
<summary><h2>Round 4</h2></summary>
Thoughts going in

<br>
  
<h3>Algo</h3>

BLAH BLAH BLAH
<h3>Manual</h3>

BLAH BLAH BLAH

<br>

Results

---

</details>

<details>
<summary><h2>Round 5</h2></summary>
Thoughts going in

<br>
  
<h3>Algo</h3>

BLAH BLAH BLAH
<h3>Manual</h3>

BLAH BLAH BLAH

<br>

Results

---

</details>

## 🏁 Final Thoughts
Something philosophical
