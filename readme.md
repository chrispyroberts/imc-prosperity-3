
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


<h3>Algo</h3>

This round introduced 6 new products: Volcanic Rocks, and 5 different Volcanic Rock vouchers with strike prices of 9500, 9750, 10000, 10250, and 10500. These products very closely resembled european option contracts, and were set to expire in in 7 in-game trading days. Chris did the analysis for this round, and using the hint provided on the website to model the volatility smile by plotting the moneyness $m_t$ agaisnt the implied volatility $v_t$. Moneyness was calculated using the following formula $$m_t = log(K / S_t) / \sqrt(TTE)$$ where $K$ is the voucher strike price, $S_t$ is the price of the underlying at some time $t$, and $TTE$ being the time to expiration in years. 

![](images/volatility_smile.png)

Fitting a quadtratic to this we found parameters $a, b, c$ for the equation $v_t = a \cdot m_t^2 + b \cdot m_t + c$ allowing us to predict a 'fair' implied volatility for any a given $m_t$. After coding this up, we found the best way to take advantages of this was to code an agressive market maker using our fitted implied volatility. We also added in functionality to automatically hedge our positions after every timestamp, ensuring that we are only exposed to the implied volatility of a contract. Our backtesting PNL curve was a straight line on most days, indicating that we found a reasonable strategy that is direction-neutral. From our backtests, we were expecting to make ~80k from all voucher products and ~100k from other products.

A few other things we considered this round for algo: 

- Something we considered as part of our analysis was how much we are losing in our long voucher positions due to theta decay. Chris found that the theta decay of the vouchers had a maximum 800 annualized, meaning that holding a voucher for a year, assuming nothing about the underlying or voucher changes, that the value of the voucher would decrease by 800 seashells over the course of the year. So he estimated that the upper bound on how much we would lose due theta decay on a given day if we were fully long 200 of a given voucher was ~430 seashells. (800 seashells per year /  365 days per year * 1 day * 200 vouchers  = ~430 seashells per day per voucher we are fully long). This amount was negligible compared to the 80k we were making on backtests. 

- Since we could hold up to 400 volcanic rocks, and 200 of any voucher, this meant if we went long 2 different vouchers, in the worst case, we could only completely hedge up to 2 vouchers assuming each had a delta of 1. Since we thought that this could get very complicated very quickly, so decided to cap all vouchers at a position size of 80 so we could guarantee that no matter what we would always be fully hedged. 

<h3>Manual</h3>
BLAH BLAH BLAH

<br>

<h3>Results and Post-Round Analyysis</h3>
This round was absolutely brutal for us as we fell from 7th to 241st, making us all believe that a comeback was impossible. We only made 75,755 on algo and 53,430 on manual, while many of the top teams made >200k on algo. We knew either something was wrong or we had missed something.

- We first realized Jasper's visualizer, which we were using extensively, was having some issue where it would cause the algorithm on submission to use more than 100mb of memory, causing the instance to reboot. This meant all local variables that the algorithm was using to trade would be wiped and re-initialized. This was a problem for our rolling windows containing short-term price movements important for trade entries and hedges on basket and volcanic rock products, causing our trader to effectively buy and sell these products randomly. In future submissions, we decided to remove Jasper's visualizer on our final submission to avoid this issue rather than debug it. 

- Chris then realized we completely missed an extremely profitable trading strategy on volcanic vouchers. The issue was that our quadratic fit for implied volatility stopped being a good model on the submission day (who would have guessed that past data doesn't imply future data), and our model would either severely under or over estimate the actual IV. This meant our trader effectively would enter into a long / short position on IV for a voucher and stay in that position for the whole day. While the IV on the vouchers did spike, the amount of seashells this IV spike corresponded to was very little, so we pretty much made nothing from volcanic rocks by using our fitted model. In the figure below, Chris plotted the IV for bids and asks on different vouchers across time, along with a short rolling window of the mid IV. Using the mean of this rollowing window instead of our quadtratic fit as a model for the fair IV made our backtester PNL shoot up from 80k to 150k on every single day, including the day of submission.

- Chris then also ran some backtests to figure out how much our hedge cost us. Since trading volcanic rock had a spread of 1, every buy/sell effectively cost us 0.5 seashells. By counting the total trades we took while hedging out position, -Chris found that we paying over 40k in spread just to hedge our position. He then tried to make an upper-bound for how much we could lose due to being unhedged. At one point in the day, volcanic rocks moved by 100 in a single step, which assuming a delta of 1, would correspond to a maximum loss of 40k. We decided that because to us price movement appears random, in expectation this will net to 0 and that we would go unhedged on volcanic vouchers in future rounds. This boosted our backtester PNL on all volcanic rock products to 250 per day.

![](images/rocks.png)


</details>

<details>
<summary><h2>Round 4</h2></summary>
<br>

After the dissapointing algo results in round 3, we felt defeated and were honestly ready to give up. Breaking into the top 25, let alone the top 10, seemed impossible from this position. In Chris' opinion, this round was incredibly easy, as it was very similar to round 2 last year, and his trading algo last year landed him in 3rd place that round, so he was confident that re-implementing his strategy from last year would net good results. 
  
<h3>Algo</h3>
This round introduced a new product called Magnificent Macrons. Magnificent Macrons can be bought or sold on the local island and then converted on the Pristine Island (thinking buying BTC from one crypto exchange then selling it on another, same exact concept). However, when converting your position, you pay fees, which include a transport cost, an export tariff, which is paid if you convert a long position (think exporting from main island) or an import tariff (think importing to main island). In addition to this, you pay a storage fee of 0.1 seashells per timestamp per Macron you hold, heavily encouraging you to never hold long positions. While the price movements of Macron are strongly correlated with sugarPrice and sunlightIndex, we decided to completely ignore this, as simply arbitraging across islands was far more profitable than predicting the movements Macron's using some model. 

- Because import tariffs were negative, we were paid to sell on the local island and convert on the Pristine island. To calculate the price needed to sell a Macron for to break even after converting, we used the following formula: sell_local_break_even_price = conversion_ask + import_tariff + transport_fee.

- We also noticed that there was a bot agressively taking orders on our local island around the mid price of the Pristine island. We used this to our advantage by placing sell orders near this mid price if it was above our break even price, and immediately converting them after they were filled. We would pocket the difference between how much we sold it for and our break even price, multiplied by 10 because we could convert 10 at a time.

- In backtests, Chris estimated a potential profit of up to 100k on Macrons over the course of the day depending on how negative import tariffs were. We were happy with this so submitted and went to bed. 

BLAH BLAH BLAH
<h3>Manual</h3>

BLAH BLAH BLAH

<br>

<h3>Results and Post-Round Analysis</h3>

![](images/round_4_res.png)

We woke up to a very pleasant suprise. We were back in 8th! Out of all teams this round, we had the highest PNL, making a whopping 447,251 from our algo and manual! We realized that had we not messed up round 3, we would be in second, and we also realized we had a better algo than #1, making 20k on them while having a very straight PNL curve. We also found that in backtests on the submission for round 3, our algo PNL was slightly better than #1, pretty much confirming that we had the same strategies but potentially slightly better. We had a real stop of making the top 2, or maybe even top 1, and were incredibly motivated.

After our emotions settled, Chris ran some backtests on Macron arbing and confirmed that around 100k of our PNL came from Macrons. He also found out that out of the 10,000 steps in the submission, we only traded 56,000 macrons. Because we only sent orders in sizes of 10, we estiamted that we were only trading about half the time. Because the import tariffs were very negative, we were making ~3 seashells per Macron we arbed, and so by not trading on 4,400 timesteps, we effectively left 44,000 macrons on the table, which would been an upper bound on the PNL we didn't capture was 132k. Chris reasoned that sometimes the aggressive buyer of Macrons would sometimes not be there, and so we would want to have a small stockpile of Macrons that we are always short for timesteps where we don't get to sell. By simply ensuring that we always sold up to 30 instead 10, we traded 95,000 macrons. This however would lead to a net short position the entire day, which we estiamted could potentially cost us 30 * 400 = 12,000, with the 400 coming from the largest price movement we observed in the data. We decided this risk was worth taking, given that we were almost doubling the amount of Macrons we were arbing. 

---

</details>

<details>
<summary><h2>Round 5</h2></summary>

![](images/Hr_Tnb.gif)

<br>
  
<h3>Algo</h3>
This round no new products were introduced. Instead, we were told the counterparties that we were trading agaisnt. Specifically, there were 11 other bots trading the same products we were. We started by first visualizing all trading activity for all the bots, by plotting products prices and overlaying a scatter plot with the prices bots would trade at. We did this for all bots and all products, and quickly found that one bot, 'Olivia', would buy/sell and the low/high of the day on 3 different products.

![](images/olivia_signal.png)

Chris had correctly guessed that the trades present in round 2 data did indeed have a true signal. Using this information, we planned to update our algorithms to copy Olivia's trades.
- After running some quick tests, we found that we were making more just market making and taking on kelp than using Olivia's signal, so we left our Kelp trading alone.

- For Squid Ink, we decided to market make and take with maximum position sizing until Olivia's signal, and then just follow it for the rest of the day.

- Croissants was slightly more complicated because we were using it as a hedge in our basket trades. We estimated that we were making ~30k per day by doing statistical arbitrage on the basket premiums. Because we had a true signal on croissants, Chris reasoned that we shouldn't take trades on baskets in the opposite direction of Olivia's signal, as the price of Croissants accounted for ~50% of the price of the basket.

  
- Building off this, we decided to YOLO into Croissants. Our maximum position size for Croissants was 250, but if we went long on both baskets, we could effectively be long 1050 Croissants. We estimated that on a bad trading day for this signal, the difference between the high and low on Croissants is 40 seashells, so a lower bound on our croissants PNL was 40 * our position size. Going long an extra 800 Croissants on this bad day will give us an extra 32k Seashells.


- Our statistical basket arbitrage was hitting 40k on it's best days, while YOLOing croissaints on Olivia's signal was getting up to 120k on a good day (difference of about ~120 between the high and low). We decided this was the best idea, and it was also very simple to implement.


- We hedged the baskets by going opposite on Jams and Djembes, as the movement of the basket was still about 50% correlated with these products. Our final position ended up being exposed to 30 Jams due to position limits. By taking on the extra 30 jams, we were able to go long another 60 croissants. We found that Jams would move around 50 on their most volatile day, so the upside of the 60 Croissants was higher than the potential downside on Jams leading us to believe that this was a risk worth taking.


- We also realized we were exposed to the premium of the basket, and that in a near worst-case scenario, we could lose up to 300 seashells per basket we were holding if we bought at the top of premium then sold at the bottom or vice versa, meaning a total potential loss of up to 45,000 seashells due to premium movement agaisnt us while in our trade. We could not think of a way to reduce this risk. Chris found that with 90% confidence the difference in basket 2 premiums from one timestep to the next was stationary, and with 95% confidence for basket 1, so we reasoned that its a coinflip that premium will move agaisnt us, and the probability of us buying right as the series is mean reverting is incredibly low (assuming Olivia's signal is not correlated with the top/bottom of premiums). Because of this, we reasoned that our potential loss is most likely not 45,000 and more realistically 20,000 at most, and that in expectation our loss is 0. Based on this line of reasoning, we ultimately decided that this risk was worth taking. 

- One final optimization Chris made was that while waiting for Olivia's signal, we would market make and take on both picnic baskets since they both had large spreads. This made us an 10k seashells per day depending on how long before Olivia's signal. 


<h3>Manual</h3>

BLAH BLAH BLAH

<br>

<h3>Results & Post-Round Analysis</h3>
We finished 7th! and 1st in the US! We we really happy with this result. Our algo made 244,740 seashells and we made 138,274 on manual. Frankfurt, who we knew with high probability had a very similar strategy to us, made a similar amount. Heisenberg, the #1 team, made more than 800k on algo this round! We still have no idea how he did this, but Kudos to them for figuring out something that no other team could! 

Chris, after talking with Jasper about his algo on the last round, realized that z-score based strategies on Volcanic rocks performed really well across all days in backtests. Using Jasper's volcanic rock z-score trading logic, and using the same hyperparameters, we were able to make an extra 150k per day by trading volcanic rocks, a product we decided not to trade at all. However, we were still unsure if this was truly an edge-generating strategy or just very lucky, because small tweaks to the hyperparameters or implementation would lead to wildly different backtesting results, some often being very negative in PNL. 

---

</details>

## 🏁 Final Thoughts

Safe to say we spent many long nights together on discord, often staying up until 6am discussing the mechanics of squid ink, the volatility smile of the volcanic rock options chain, making guesses on what the critical sunlight level is and it's correlation to sugar prices, and praising Olivia for providing us with true alpha on Croissants.

While we didn't win any money, making the top 10 after having our rank change more than squid ink would in a day is something that we are proud of. We did make a few small mistakes which ended up costing us what we believe would have been a top 5 global ranking. Regardless, we learned a lot about game theory, options trading and statistical modelling
and are incredibly thankful to IMC for hosting the challange, the discord moderaters for being very pleasant and providing useful hints, and Jasper for his open source visualization, backtester, and leaderboard. 

