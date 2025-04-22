from typing import List
import string
import numpy as np
import json
from typing import Any
import math

import json
from typing import Any
from datamodel import *
from datamodel import Listing, Observation, Order, OrderDepth, ProsperityEncoder, Symbol, Trade, TradingState



from math import log, sqrt, exp
from statistics import NormalDist


# logger = Logger()


class BlackScholes:
    @staticmethod
    def black_scholes_call(spot, strike, time_to_expiry, volatility):
        d1 = (
            log(spot) - log(strike) + (0.5 * volatility * volatility) * time_to_expiry
        ) / (volatility * sqrt(time_to_expiry))
        d2 = d1 - volatility * sqrt(time_to_expiry)
        call_price = spot * NormalDist().cdf(d1) - strike * NormalDist().cdf(d2)
        return call_price

    @staticmethod
    def black_scholes_put(spot, strike, time_to_expiry, volatility):
        d1 = (log(spot / strike) + (0.5 * volatility * volatility) * time_to_expiry) / (
            volatility * sqrt(time_to_expiry)
        )
        d2 = d1 - volatility * sqrt(time_to_expiry)
        put_price = strike * NormalDist().cdf(-d2) - spot * NormalDist().cdf(-d1)
        return put_price

    @staticmethod
    def delta(spot, strike, time_to_expiry, volatility):
        d1 = (
            log(spot) - log(strike) + (0.5 * volatility * volatility) * time_to_expiry
        ) / (volatility * sqrt(time_to_expiry))
        return NormalDist().cdf(d1)

    @staticmethod
    def gamma(spot, strike, time_to_expiry, volatility):
        d1 = (
            log(spot) - log(strike) + (0.5 * volatility * volatility) * time_to_expiry
        ) / (volatility * sqrt(time_to_expiry))
        return NormalDist().pdf(d1) / (spot * volatility * sqrt(time_to_expiry))

    @staticmethod
    def vega(spot, strike, time_to_expiry, volatility):
        d1 = (
            log(spot) - log(strike) + (0.5 * volatility * volatility) * time_to_expiry
        ) / (volatility * sqrt(time_to_expiry))
        # print(f"d1: {d1}")
        # print(f"vol: {volatility}")
        # print(f"spot: {spot}")
        # print(f"strike: {strike}")
        # print(f"time: {time_to_expiry}")
        return NormalDist().pdf(d1) * (spot * sqrt(time_to_expiry)) / 100

    @staticmethod
    def implied_volatility(
        call_price, spot, strike, time_to_expiry, max_iterations=200, tolerance=1e-10
    ):
        low_vol = 0.001
        high_vol = 1.0
        volatility = (low_vol + high_vol) / 2.0  # Initial guess as the midpoint
        for _ in range(max_iterations):
            estimated_price = BlackScholes.black_scholes_call(
                spot, strike, time_to_expiry, volatility
            )
            diff = estimated_price - call_price
            if abs(diff) < tolerance:
                break
            elif diff > 0:
                high_vol = volatility
            else:
                low_vol = volatility
            volatility = (low_vol + high_vol) / 2.0
        return volatility

class Trader:
    # definite init state
    def __init__(self):

        self.limits = {
            'RAINFOREST_RESIN' : 50,
            'SQUID_INK' : 50,
            'KELP' : 50,
        }

        self.orders = {}
        self.conversions = 0
        self.traderData = "SAMPLE"

        # ROUND 1

        # Resin
        self.resin_buy_orders = 0
        self.resin_sell_orders = 0
        self.resin_position = 0

        # Kelp
        self.kelp_position = 0
        self.kelp_buy_orders = 0
        self.kelp_sell_orders = 0

        # squid
        self.squid_ink_position = 0
        self.squid_ink_buy_orders = 0
        self.squid_ink_sell_orders = 0
        self.prev_squid_price = None

        # windows
        self.squid_ink_short_window_prices = []
        self.squid_ink_long_window_prices = []
        self.volatility_window_price_diffs = []
        self.volatility_window = 50 # no need to change, unused
        self.squid_ink_prices = []


        #==================================
        # SQUID INK HYPERPARAMS 
        self.squid_ink_long_window = 1000   # long window size for squid ink

        # market making
        self.max_squid_market = 50          # determines max position size for market making

        # spike trading
        self.price_diff_threshold = 10      # threshold for detecting huge price spikes
        self.threshold = 1                  # default threshold for squid ink spike trading
        #==================================

        # ROUND 2
        # basket1
        self.basket1_premiums = []
        self.basket1_pos = 0
        self.basket2_pos = 0 # track independently
        self.basket2_premiums = []
        self.premium_difference = []
        # basket2 mm
        self.trade_on_turn = False
        self.basket2_market_make_pos = 0
        self.basket2_buy_orders = 0
        self.basket2_sell_orders = 0
        self.basket1_buy_orders = 0
        self.basket1_sell_orders = 0

        # self.basket_2_premium_mean = 48.82898734599846 
        # self.premium_diff_mean = 18.625755400487463

        # HYPERPARAMS FOR BASKET WEAVING
        #==================================
        self.basket_2_premium_mean = 31.424069485119272     # basket2 mean
        self.premium_diff_mean = 29.38458361492829          # basket1 prem - basket2 prem mean
        # self.premium_diff_window = 30                       # z-score window length
        # self.z_score_threshold_basket_2 = 14                # entry and exit for basket 2 premium
        # self.z_score_threshold = 17                        # entry and exit for premium difference
        self.premium_diff_window = 1000                       # z-score window length
        self.z_score_threshold_basket_2 = 1.5
        self.z_score_threshold = 1.5
        #==================================

        self.initialize_round_3()

        self.total_fills = 0

   # =======================================
    # ROUND 3 TRADING LOGIC BELOW
    # =======================================

    def initialize_round_3(self):
        # init call but for round 3

        self.options_model = BlackScholes()

        self.timestamps_per_year = 365e6
        self.days_left = 4 # day 2: 6, day 3 (submission) : 5

        # fit params genrated by fit between -0.35 and 0.35 moneyness
        self.ask_params = {
                          'a': 0.2386154106662951,
                          'b': -0.001961415956883628,  
                          'c': 0.15164395927568022
                          }
        
        self.bid_params = {
                          'a': 0.1436195242784995,
                          'b': -0.0015495217059325098,
                          'c': 0.15037740474609734
                          }
        

        self.vouchers =  ['VOLCANIC_ROCK_VOUCHER_9500', 'VOLCANIC_ROCK_VOUCHER_9750',
                          'VOLCANIC_ROCK_VOUCHER_10000', 'VOLCANIC_ROCK_VOUCHER_10250',
                          'VOLCANIC_ROCK_VOUCHER_10500']

        # self.vouchers = ['VOLCANIC_ROCK_VOUCHER_10000']

        # windows n shit
        self.underlying_price_history = []
        self.underlying_spread = 0
        self.underlying_price_window = 5

        self.window_size = 20
        self.total_trades = 0
        self.total_takes = 0
        self.total_hedges = 0
        self.total_exits = 0
    
        self.voucher_implied_vols = {
            'VOLCANIC_ROCK_VOUCHER_9500' :  [],
            'VOLCANIC_ROCK_VOUCHER_9750' :  [],
            'VOLCANIC_ROCK_VOUCHER_10000' : [],
            'VOLCANIC_ROCK_VOUCHER_10250' : [],
            'VOLCANIC_ROCK_VOUCHER_10500' : []
        }

        self.voucher_deltas = {
            'VOLCANIC_ROCK_VOUCHER_9500' :  [],
            'VOLCANIC_ROCK_VOUCHER_9750' :  [],
            'VOLCANIC_ROCK_VOUCHER_10000' : [],
            'VOLCANIC_ROCK_VOUCHER_10250' : [],
            'VOLCANIC_ROCK_VOUCHER_10500' : []   
        }


    def update_round_4_products(self, state):
        # vouchers = [self.trading_voucher]
        underlying = 'VOLCANIC_ROCK'

        order_book = state.order_depths[underlying]
        if len(order_book.sell_orders) != 0 and len(order_book.buy_orders) != 0:
            ask, _ = list(order_book.sell_orders.items())[0] 
            bid, _ = list(order_book.buy_orders.items())[0]         

            underlying_price = (ask + bid) / 2
            self.underlying_spread = (bid-ask)
            self.underlying_price_history.append(underlying_price)
            self.underlying_price_history = self.underlying_price_history[-self.squid_ink_long_window:]

        for voucher in self.vouchers:
            order_book = state.order_depths[voucher]
            if len(order_book.sell_orders) == 0 or len(order_book.buy_orders) == 0 or len(self.underlying_price_history) == 0:
                continue

            ask, _ = list(order_book.sell_orders.items())[0]
            bid, _ = list(order_book.buy_orders.items())[0]
               
            mid_price = (ask + bid) / 2
            underlying_price = self.underlying_price_history[-1]
            strike = int(voucher.split('_')[-1])
            tte = (self.days_left / 365)  - state.timestamp / self.timestamps_per_year

            voucher_iv = self.options_model.implied_volatility(mid_price, underlying_price, strike, tte)
            # logger.print(f"{strike} - {mid_price} - {underlying_price} - {tte} => {voucher_iv}")
            voucher_delta = self.options_model.delta(underlying_price, strike, tte, voucher_iv)

            # append vol
            self.voucher_implied_vols[voucher].append(voucher_iv)
            self.voucher_implied_vols[voucher] = self.voucher_implied_vols[voucher][-self.window_size:]

            # append deltas
            self.voucher_deltas[voucher].append(voucher_delta)
            self.voucher_deltas[voucher] = self.voucher_deltas[voucher][-self.window_size:]

    def buy_voucher(self, state, voucher):

        pos_size = self.get_product_pos(state, voucher)
        
        if pos_size >= 0:
            return

        voucher_avg_vol = np.mean(self.voucher_implied_vols[voucher])
        strike = int(voucher.split('_')[-1])
        underlying_price = self.underlying_price_history[-1]
        tte = (self.days_left / 365)  - state.timestamp / self.timestamps_per_year        

        fair_value = self.options_model.black_scholes_call(underlying_price, strike, tte, voucher_avg_vol)
        
        # since we are buying, round mid_price up
        price = int(math.ceil(fair_value))
        self.entry_price = price
        size = abs(pos_size)
        self.send_buy_order(voucher, price, size)

    def sell_voucher(self, state, voucher):
        pos_size = self.get_product_pos(state, voucher)
        
        if pos_size <= 0:
            return 
        
        voucher_avg_vol = np.mean(self.voucher_implied_vols[voucher])
        strike = int(voucher.split('_')[-1])
        underlying_price = self.underlying_price_history[-1]
        tte = (self.days_left / 365)  - state.timestamp / self.timestamps_per_year        

        fair_value = self.options_model.black_scholes_call(underlying_price, strike, tte, voucher_avg_vol)
        
        price = int(math.floor(fair_value))
        size = abs(pos_size)
        self.send_sell_order(voucher, price, -size)

    def mm_on_IV(self, state): 
        for voucher in self.vouchers:  
            voucher_avg_vol = np.mean(self.voucher_implied_vols[voucher])
            voucher_std_vol = np.std(self.voucher_implied_vols[voucher])
        
            strike = int(voucher.split('_')[-1])
            underlying_price = self.underlying_price_history[-1]
            tte = (self.days_left / 365)  - state.timestamp / self.timestamps_per_year

            high_value = self.options_model.black_scholes_call(underlying_price, strike, tte, voucher_avg_vol + voucher_std_vol)
            fair_value = self.options_model.black_scholes_call(underlying_price, strike, tte, voucher_avg_vol)
            low_value = self.options_model.black_scholes_call(underlying_price, strike, tte, voucher_avg_vol - voucher_std_vol)
            
            # dont trade it if it's not volatile enough
            if (high_value - low_value) < 1.0:
                self.buy_voucher(state, voucher)
                self.sell_voucher(state, voucher)
                continue

            eps = 0.1
            bid = int(math.floor(fair_value+eps))
            ask = int(math.ceil(fair_value-eps))
  
            # =========== MM Approach ==========
            max_size = 200
            bid_size = max_size - self.get_product_pos(state, voucher)
            ask_size = self.get_product_pos(state, voucher) + max_size

            # check for other person's market
            order_depth = state.order_depths[voucher]
            
            best_ask = None
            best_ask_amount = None

            best_bid = None
            best_bid_amount = None

            if len(order_depth.sell_orders) != 0:
                best_ask, _ = list(order_depth.sell_orders.items())[-1]
            
            if len(order_depth.buy_orders) != 0:
                best_bid, _ = list(order_depth.buy_orders.items())[-1]

            sent_buys = 0
            sent_sells = 0

            fair_value = int(fair_value)
            max_spread = math.floor(fair_value * 0.03)

            # check if we are crossing markets with best_ask
            for market_ask, market_amount in order_depth.sell_orders.items():
                if bid > market_ask:
                    # eat their market then take it over
                    eat_order_size = abs(min(bid_size, abs(market_amount)))
                    self.send_buy_order(voucher, market_ask, eat_order_size) # take their ask
                    sent_buys += eat_order_size
                        
                    # place bid above best bid
                    if best_bid is not None:
                        bid = best_bid + 1
                    else:
                        bid = int(math.floor(fair_value - max_spread))

                    # place ask at maximum dist from fair value
                    ask = int(math.ceil(max(fair_value + max_spread, ask)))
                                    
            # check if we are crossing with best_bid
            for market_bid, market_amount in order_depth.buy_orders.items():
                if ask < market_bid:
                    # eat their market then take it over
                    eat_order_size = abs(min(ask_size, abs(market_amount)))
                    sent_sells += eat_order_size
                    self.send_sell_order(voucher, best_bid, -eat_order_size)
                    
                    # place ask below best ask
                    if best_ask is not None: 
                        ask = best_ask - 1
                    else:
                        ask = int(math.ceil(ask + max_spread))
                    
                    # place bid at maximum dist from fair value
                    bid = int(math.floor(max(fair_value - max_spread, bid)))


            # logger.print(f"strike {strike} price: {fair_value:.1f} market: ({bid}|{ask}) taken: ({sent_buys}|{sent_sells})")

            # recalculate max sizings
            bid_size = max(max_size - self.get_product_pos(state, voucher) - sent_buys, 0)
            ask_size = max(self.get_product_pos(state, voucher) + max_size - sent_sells, 0)

            if sent_buys > 0:
                bought_delta = np.mean(self.voucher_deltas[voucher]) * sent_buys
                self.trade_underlying(state, -int(bought_delta))
            
            if sent_sells > 0:
                sold_delta = np.mean(self.voucher_deltas[voucher]) * sent_sells
                self.trade_underlying(state, int(sold_delta))

            if bid == ask:
                if bid_size > ask_size:
                    self.send_buy_order(voucher, bid, bid_size)
                elif ask_size < bid_size:
                    self.send_sell_order(voucher, ask, -ask_size)   
            else:
                self.send_buy_order(voucher, bid, bid_size)      
                self.send_sell_order(voucher, ask, -ask_size)   

    def trade_underlying(self, state, size, dont_hedge=True):
        
        if dont_hedge:
            return
        
        if self.underlying_spread > 1:
            return
                 
        if size < 0:
            # need to buy
            mid_price = self.underlying_price_history[-1]
            price = int(math.ceil(mid_price))
            size = abs(size)
            cur_pos = self.get_product_pos(state, 'VOLCANIC_ROCK')
            size = min(400-cur_pos-self.volcanic_rock_buy_orders, size)
            self.volcanic_rock_buy_orders += size
            self.send_buy_order('VOLCANIC_ROCK', price, size)
            
        elif size > 0:
            # need to sell
            mid_price = self.underlying_price_history[-1]
            price = int(math.floor(mid_price))
            size = abs(size)
            cur_pos = self.get_product_pos(state, 'VOLCANIC_ROCK')
            size = min(cur_pos + 400 - self.volcanic_rock_sell_orders, size)
            self.volcanic_rock_sell_orders += size
            self.send_buy_order('VOLCANIC_ROCK', price, -size)

    def delta_hedge(self, state):
        # need to calcualte total delta
        total_delta = 0
        for voucher in self.vouchers:
            
            if len(self.voucher_deltas[voucher]) == 0:
                continue
            
            delta = np.mean(self.voucher_deltas[voucher]) # take last delta

            position_size = self.get_product_pos(state, voucher) # get position size 
            total_delta += delta * position_size
        
        # logger.print(f"Total Delta: {total_delta:.2f}, Volcanic Rock: {self.get_product_pos(state, 'VOLCANIC_ROCK'):.2f}")
        size = int(self.get_product_pos(state, 'VOLCANIC_ROCK') + self.volcanic_rock_buy_orders - self.volcanic_rock_sell_orders + total_delta)

        self.trade_underlying(state, size)   

    def trade_vouchers(self, state):

        self.update_round_4_products(state)

        self.mm_on_IV(state)

        # hedge after trading
        self.delta_hedge(state)

    # =======================================
    # ROUND 1 TRADING LOGIC BELOW
    # ======================================= 
    
    # define easier sell and buy order functions
    def send_sell_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        # if msg is not None:
            # logger.print(msg)

    def send_buy_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        # if msg is not None:
        #     logger.print(msg)

    def get_product_pos(self, state, product):
        return state.position.get(product, 0)
        
    def search_buys(self, state, product, acceptable_price, depth=1):
        # Buys things if there are asks below or equal acceptable price
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            for ask, amount in orders[0:max(len(orders), depth)]: 

                pos = self.get_product_pos(state, product)                    
                if int(ask) < acceptable_price or (abs(ask - acceptable_price) < 1 and (pos < 0 and abs(pos - amount) < abs(pos))):
                    if product == 'RAINFOREST_RESIN':
                        size = min(50-self.resin_position-self.resin_buy_orders, -amount)

                        self.resin_buy_orders += size 
                        self.send_buy_order(product, ask, size)

                    elif product == 'KELP':
                        size = min(50-self.kelp_position-self.kelp_buy_orders, -amount)
                        self.kelp_buy_orders += size 
                        self.send_buy_order(product, ask, size)
                    
                    elif product == 'SQUID_INK':

                        if self.max_squid_market:
                            size = min(self.max_squid_market-self.squid_ink_position-self.squid_ink_buy_orders, -amount)
                        else:
                            size = min(50-self.squid_ink_position-self.squid_ink_buy_orders, -amount)

                        self.squid_ink_buy_orders += size 
                        self.send_buy_order(product, ask, size)  

                    elif product == 'PICNIC_BASKET1':
                        size = min(60-self.get_product_pos(state, product)-self.basket1_buy_orders, -amount)
                        self.basket1_buy_orders += size
                        self.send_buy_order(product, ask, size)
                    
                    # ARB VERSION
                    elif product == 'PICNIC_BASKET2':
                        size = min(8-self.basket2_market_make_pos-self.basket2_buy_orders, -amount)
                        self.basket2_buy_orders += size
                        self.send_buy_order(product, ask, size)  

    def search_sells(self, state, product, acceptable_price, depth=1):   
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            for bid, amount in orders[0:max(len(orders), depth)]: 
                
                pos = self.get_product_pos(state, product)   
                if int(bid) > acceptable_price or (abs(bid-acceptable_price) < 1 and (pos > 0 and abs(pos - amount) < abs(pos))):
                    if product == 'RAINFOREST_RESIN':
                        size = min(self.resin_position + 50 - self.resin_sell_orders, amount)
                        self.resin_sell_orders += size
                        self.send_sell_order(product, bid, -size)

                    elif product == 'KELP':
                        size = min(self.kelp_position + 50 - self.kelp_sell_orders, amount)
                        self.kelp_sell_orders += size
                        self.send_sell_order(product, bid, -size)
                    
                    elif product == 'SQUID_INK':
                        if self.max_squid_market:
                            size = min(self.squid_ink_position + self.max_squid_market - self.squid_ink_sell_orders, amount)
                        else:
                            size = min(self.squid_ink_position + 50 - self.squid_ink_sell_orders, amount)

                        self.squid_ink_sell_orders += size
                        self.send_sell_order(product, bid, -size)

                    elif product == 'PICNIC_BASKET1':
                        size = min(self.get_product_pos(state, product) + 60 - self.basket1_sell_orders, amount)
                        self.basket1_sell_orders += size
                        self.send_sell_order(product, bid, -size)

                    # ARB VERSION
                    elif product == 'PICNIC_BASKET2':
                        size = min(self.basket2_market_make_pos + 8 - self.basket2_sell_orders, amount)
                        self.basket2_sell_orders += size
                        self.send_sell_order(product, bid, -size)
                
    def get_bid(self, state, product, price):        
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            for bid, _ in orders: 
                if bid < price: # DONT COPY SHIT MARKETS
                    return bid
        
        return None

    def get_ask(self, state, product, price):      
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            for ask, _ in orders: 
                if ask > price: # DONT COPY A SHITY MARKET
                    return ask
        
        return None

    def trade_resin(self, state):
        # Buy anything at a good price
        self.search_buys(state, 'RAINFOREST_RESIN', 10000, depth=3)
        self.search_sells(state, 'RAINFOREST_RESIN', 10000, depth=3)

        # Check if there's another market maker
        best_ask = self.get_ask(state, 'RAINFOREST_RESIN', 10000)
        best_bid =  self.get_bid(state, 'RAINFOREST_RESIN', 10000)

        # our ordinary market
        buy_price = 9993
        sell_price = 10007  

        # update market if someone else is better than us
        if best_ask is not None and best_bid is not None:
            ask = best_ask
            bid = best_bid
            
            sell_price = ask - 1
            buy_price = bid + 1
    
        max_buy =  50 - self.resin_position - self.resin_buy_orders 
        max_sell = self.resin_position + 50 - self.resin_sell_orders

        self.send_sell_order('RAINFOREST_RESIN', sell_price, -max_sell)
        self.send_buy_order('RAINFOREST_RESIN', buy_price, max_buy)

    def trade_kelp(self, state):
        # position limits
        low = -50
        high = 50

        position = state.position.get("KELP", 0)

        max_buy = high - position
        max_sell = position - low

        order_book = state.order_depths['KELP']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            
            fair_price = int(math.ceil((ask + bid) / 2))  # try changing this to floor maybe

            decimal_fair_price = (ask + bid) / 2

            # logger.print(f"KELP FAIR PRICE: {decimal_fair_price}")
            self.search_buys(state, 'KELP', decimal_fair_price, depth=3)
            self.search_sells(state, 'KELP', decimal_fair_price, depth=3)

            # Check if there's another market maker
            best_ask = self.get_ask(state, 'KELP', fair_price)
            best_bid =  self.get_bid(state, 'KELP', fair_price)

            # our ordinary market
            buy_price = math.floor(decimal_fair_price) - 2
            sell_price = math.ceil(decimal_fair_price) + 2
        
            # update market if someone else is better than us
            if best_ask is not None and best_bid is not None:
                ask = best_ask
                bid = best_bid
                
                # check if we move our market if the price is still good
                if ask - 1 > decimal_fair_price:
                    sell_price = ask - 1
                
                if bid + 1 < decimal_fair_price:
                    buy_price = bid + 1 
            
            max_buy =  50 - self.kelp_position - self.kelp_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = self.kelp_position + 50 - self.kelp_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            pos = self.get_product_pos(state, 'KELP')

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('KELP', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('KELP', sell_price, -max_sell)

    def make_squid_market(self, state):
        low = -50
        high = 50

        position = state.position.get("SQUID_INK", 0)

        max_buy = high - position
        max_sell = position - low

        order_book = state.order_depths['SQUID_INK']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            
            fair_price = int(math.ceil((ask + bid) / 2))  # try changing this to floor maybe

            decimal_fair_price = (ask + bid) / 2

            
            self.search_buys(state, 'SQUID_INK', decimal_fair_price, depth=3)
            self.search_sells(state, 'SQUID_INK', decimal_fair_price, depth=3)

            # Check if there's another market maker
            best_ask = self.get_ask(state, 'SQUID_INK', fair_price)
            best_bid =  self.get_bid(state, 'SQUID_INK', fair_price)

            # our ordinary market
            buy_price = math.floor(decimal_fair_price) - 2
            sell_price = math.ceil(decimal_fair_price) + 2
        
            # update market if someone else is better than us
            if best_ask is not None and best_bid is not None:
                ask = best_ask
                bid = best_bid
                
                if ask - 1 > decimal_fair_price:
                    sell_price = ask - 1
                if bid + 1 < decimal_fair_price:
                    buy_price = bid + 1
    
            if self.max_squid_market:
                maximum_sizing = self.max_squid_market
            else:
                maximum_sizing = 50

            max_buy =  maximum_sizing - state.position.get("SQUID_INK", 0) - self.squid_ink_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = state.position.get("SQUID_INK", 0) + maximum_sizing - self.squid_ink_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            # logger.print("SQUID_INK MAX MARKET BUY: ", max_buy)
            # logger.print("SQUID_INK MAX MARKET SELL: ", max_sell)

            max_buy = max(0, max_buy)
            max_sell = max(0, max_sell)

            self.send_buy_order('SQUID_INK', buy_price, max_buy)
            self.send_sell_order('SQUID_INK', sell_price, -max_sell)
        
    def squid_ink_spike_trade(self, state, decimal_fair_price, long_mean, std, threshold):
        if decimal_fair_price > long_mean + threshold*std:
            # logger.print(f"SQUID INK HIT LONG THRESHOLD: {decimal_fair_price} > {long_mean + threshold*std}")
            # logger.print(f"FULL SELL MODE")
            self.sell_squid_at_market(state)

        elif decimal_fair_price < long_mean - threshold*std:
            # logger.print(f"SQUID INK HIT SHORT THRESHOLD: {decimal_fair_price} < {long_mean - threshold*std}")
            # logger.print(f"FULL BUY MODE")
            self.buy_squid_at_market(state)

        else:                    
            # logger.print(f"SQUID_INK FAIR PRICE: {decimal_fair_price}")
            # logger.print(f"SQUID_INK LONG THRESHOLD: {long_mean + threshold*std}")
            # logger.print(f"SQUID_INK SHORT THRESHOLD: {long_mean - threshold*std}")
            self.make_squid_market(state) 

    def buy_squid_at_market(self, state):
        pos = self.get_product_pos(state, 'SQUID_INK')   
        order_depth = state.order_depths['SQUID_INK']
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            # buy the whole book
            for ask, amount in orders:
                size = min(50 - pos - self.squid_ink_buy_orders, -amount)
                self.squid_ink_buy_orders += size
                self.send_buy_order('SQUID_INK', ask, size)

    def sell_squid_at_market(self, state):
        pos = self.get_product_pos(state, 'SQUID_INK')   
        order_depth = state.order_depths['SQUID_INK']
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            # sell the whole book
            for bid, amount in orders:
                size = min(pos + 50 - self.squid_ink_sell_orders, amount)
                self.squid_ink_sell_orders += size
                self.send_sell_order('SQUID_INK', bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")

    def trade_squid(self, state):
        # position limits
        order_book = state.order_depths['SQUID_INK']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders

        self.squid_ink_sell_volume = 0
        self.squid_ink_buy_volume = 0

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            decimal_fair_price = (ask + bid) / 2

            # Append to windows
            self.squid_ink_prices.append(decimal_fair_price)
            self.squid_ink_prices = self.squid_ink_prices[-self.squid_ink_long_window:]

            # check if we have enough data
            if len(self.squid_ink_prices) < self.squid_ink_long_window:
                self.make_squid_market(state)
            else:
                spike_trading = False
                if self.prev_squid_price is not None:
                    # price diff
                    price_diff = abs(self.prev_squid_price - decimal_fair_price)
                    # logger.print("SQUID INK PRICE DIFF: ", price_diff)
                    if price_diff > self.price_diff_threshold:
                        # logger.print("SQUID INK SPIKE DETECTED")
                        spike_trading = True

                if spike_trading:
                    threshold = self.threshold
                    long_mean = np.mean(self.squid_ink_prices)
                    std = np.std(self.squid_ink_prices)
                    self.squid_ink_spike_trade(state, decimal_fair_price, long_mean, std, threshold)                  
                else:
                    self.make_squid_market(state)
            
            self.prev_squid_price = decimal_fair_price

    # =======================================
    # ROUND 2 TRADING LOGIC BELOW
    # =======================================

    def get_market_data(self, state, product):
        # returns total volume and the worst bid
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) == 0:
            raise ValueError('No orders')
        
        last_bid = None
        total_bid_volume = 0
        buy_orders = list(order_depth.buy_orders.items())
        for bid, volume in buy_orders:
            last_bid = bid
            total_bid_volume += abs(volume)

        last_ask = None
        total_ask_volume = 0
        sell_orders = list(order_depth.sell_orders.items())
        for bid, volume in sell_orders:
            last_ask = bid
            total_ask_volume += abs(volume)  

        data = {
            'bid' : last_bid, 'bid_volume' : total_bid_volume, 
            'ask': last_ask, 'ask_volume' : total_ask_volume,
            'mid_price': (last_ask + last_bid)/2}
        
        return data

    def get_basket_premiums(self, state, product_data):
        jam_price = product_data['JAMS']['mid_price']
        crossaint_price = product_data['CROISSANTS']['mid_price']
        djembe_price = product_data['DJEMBES']['mid_price']

        basket1_theo_price =  6 * crossaint_price + 3 * jam_price + djembe_price
        basket2_theo_price = 4 * crossaint_price + 2 * jam_price

        basket1_premium = product_data['PICNIC_BASKET1']['mid_price'] - basket1_theo_price
        basket2_premium = product_data['PICNIC_BASKET2']['mid_price'] - basket2_theo_price

        return basket1_premium, basket2_premium

    def long_basket_1(self, state, product_data):
        # need to long basket1, to do this we need to calculate how many baskets we can short
        # For every basket1 we buy, 
        # -> sell   basket2
        # -> sell 1 djembe
        # -> sell 2 CROISSANTS
        # -> sell 1 jam
        crossaint_volume_available = product_data['CROISSANTS']['bid_volume'] # sell this
        jam_volume_available = product_data['JAMS']['bid_volume'] # sell this
        djembe_volume_available = product_data['DJEMBES']['bid_volume'] # sell this
        basket1_volume_available = product_data['PICNIC_BASKET1']['ask_volume'] # buy this
        basket2_volume_available = product_data['PICNIC_BASKET2']['bid_volume'] # sell this

        # Take the minimum of them
        possible_buys = min(basket2_volume_available, basket1_volume_available, 
                          djembe_volume_available, jam_volume_available,
                          crossaint_volume_available // 2)
        
        # calculate how many we can sell before we hit our position limit   
        self.get_product_pos(state, 'PICNIC_BASKET1')
        buy_limit = 60 - self.get_product_pos(state, 'PICNIC_BASKET1')
        basket1_pos = min(buy_limit, possible_buys)

        self.basket1_pos = basket1_pos # record this

        if self.basket1_pos == 0:
            return

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # sell CROISSANTS
        price = product_data['CROISSANTS']['bid']
        size = -basket1_pos * 2
        self.send_sell_order('CROISSANTS', price, size,  
                             )
        
        # sell djembe
        price = product_data['DJEMBES']['bid']
        size = -basket1_pos
        self.send_sell_order('DJEMBES', price, size,  
                            )

        # sell jam
        price = product_data['JAMS']['bid']
        size = -basket1_pos
        self.send_sell_order('JAMS', price, size,  
                             )  
        
       # buy basket 1
        price = product_data['PICNIC_BASKET1']['ask']
        size = basket1_pos
        self.send_buy_order('PICNIC_BASKET1', price, size,
                            )     

        # sell basket2
        price = product_data['PICNIC_BASKET2']['bid']
        size = -basket1_pos
        self.send_sell_order('PICNIC_BASKET2', price, size,  
                             )     
    
    def short_basket_1(self, state, product_data):
        # need to short basket1, to do this we need to calculate how many baskets we can short
        # based off available volume of individual products

        # For every basket1 we sell, 
        # -> buy  1 basket2
        # -> buy 1 djembe
        # -> buy 2 CROISSANTS
        # -> buy 1 jam
        
        crossaint_volume_available = product_data['CROISSANTS']['ask_volume'] # buy this
        jam_volume_available = product_data['JAMS']['ask_volume'] # buy this
        djembe_volume_available = product_data['DJEMBES']['ask_volume'] # buy this
        basket1_volume_available = product_data['PICNIC_BASKET1']['bid_volume'] # short this
        basket2_volume_available = product_data['PICNIC_BASKET2']['ask_volume'] # buy this

        # Take the minimum of them
        possible_sells = min(basket2_volume_available, basket1_volume_available, 
                          djembe_volume_available, jam_volume_available,
                          crossaint_volume_available // 2)
        
        # calculate how many we can sell before we hit our position limit   
        self.get_product_pos(state, 'PICNIC_BASKET1')
        sell_limit = 60 + self.get_product_pos(state, 'PICNIC_BASKET1')
        basket1_pos = min(sell_limit, possible_sells)        
        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        self.basket1_pos = basket1_pos # record this
        if self.basket1_pos == 0:
            return

        # buy CROISSANTS
        price = product_data['CROISSANTS']['ask']
        size = basket1_pos * 2
        self.send_buy_order('CROISSANTS', price, size,  
                             )
        
        # buy djembe
        price = product_data['DJEMBES']['ask']
        size = basket1_pos
        self.send_buy_order('DJEMBES', price, size,  
                           )

        # buy jam
        price = product_data['JAMS']['ask']
        size = basket1_pos
        self.send_buy_order('JAMS', price, size,  
                         )        
                
        # sell basket1
        price = product_data['PICNIC_BASKET1']['bid']
        size = -basket1_pos
        self.send_sell_order('PICNIC_BASKET1', price, size,  
                            )          

        # buy basket2
        price = product_data['PICNIC_BASKET2']['ask']
        size = basket1_pos
        self.send_buy_order('PICNIC_BASKET2', price, size,  
                             )          

    def long_basket_2(self, state, product_data):
        # For every basket2 we buy, 
        # -> sell 4 CROISSANTS
        # -> sell 2 jam
        crossaint_volume_available = product_data['CROISSANTS']['bid_volume'] # sell this
        jam_volume_available = product_data['JAMS']['bid_volume'] # sell this
        basket2_volume_available = product_data['PICNIC_BASKET2']['ask_volume'] # buy this

        # Take the minimum of them
        possible_buys = min(basket2_volume_available, 
                            jam_volume_available//2, 
                            crossaint_volume_available//4)
                
        # calculate how many we can buy before we hit our position limit   
        self.get_product_pos(state, 'PICNIC_BASKET2')

        # limit is 32 in either direction (long or short, limited by amount of crossaints we can hold)
        buy_limit = 32 - self.basket2_pos 
        basket2_pos = min(buy_limit, possible_buys)
        # logger.print("Basket 2 Pos: ", self.basket2_pos)

        if abs(basket2_pos) > 0:
            self.trade_on_turn = True # we are trading this turn
        else:
            return

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # sell CROISSANTS
        price = product_data['CROISSANTS']['bid']
        size = -basket2_pos * 4
        self.send_sell_order('CROISSANTS', price, size,  
                             )

        # sell jam
        price = product_data['JAMS']['bid']
        size = -basket2_pos * 2
        self.send_sell_order('JAMS', price, size,  
                             ) 
        
        # buy basket2
        price = product_data['PICNIC_BASKET2']['ask']
        size = basket2_pos
        self.send_buy_order('PICNIC_BASKET2', price, size,  
                            )    

        self.basket2_pos += basket2_pos # update our basket2 position

    def short_basket_2(self, state, product_data):
        # For every basket2 we sell, 
        # -> buy 4 CROISSANTS
        # -> buy 2 jam
        crossaint_volume_available = product_data['CROISSANTS']['ask_volume'] # sell this
        jam_volume_available = product_data['JAMS']['ask_volume'] # sell this
        basket2_volume_available = product_data['PICNIC_BASKET2']['bid_volume'] # buy this

        # Take the minimum of them
        possible_sells = min(basket2_volume_available, 
                            jam_volume_available//2, 
                            crossaint_volume_available//4)
                
        # calculate how many we can buy before we hit our position limit   
        self.get_product_pos(state, 'PICNIC_BASKET2')

        # limit is 32 in either direction (long or short, limited by amount of crossaints we can hold)
        max_sell = 32 + self.basket2_pos 
        # logger.print("Basket 2 Pos: ", self.basket2_pos)
        basket2_pos = min(max_sell, possible_sells)

        if abs(basket2_pos) > 0:
            self.trade_on_turn = True
        else:
            return

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # buy CROISSANTS
        price = product_data['CROISSANTS']['ask']
        size = basket2_pos * 4
        self.send_buy_order('CROISSANTS', price, size,  
                            )

        # buy jam
        price = product_data['JAMS']['ask']
        size = basket2_pos * 2
        self.send_buy_order('JAMS', price, size,  
                             ) 
        
        # sell basket2
        price = product_data['PICNIC_BASKET2']['bid']
        size = -basket2_pos
        self.send_sell_order('PICNIC_BASKET2', price, size,  
                            )    

        self.basket2_pos -= basket2_pos # update our basket2 position

    def trade_baskets(self, state):
        # get the midprice of all items

        self.update_basket2_pos(state)
        products = ['PICNIC_BASKET1', 'PICNIC_BASKET2', 'JAMS', 'CROISSANTS', 'DJEMBES']
        product_data = {}

        for p in products:
            product_data[p] = self.get_market_data(state, p)

        basket1_premium, basket2_premium = self.get_basket_premiums(state, product_data)

        self.basket1_premiums.append(basket1_premium)
        self.basket2_premiums.append(basket2_premium)

        self.basket2_premiums = self.basket2_premiums[-self.premium_diff_window:] # keep the last 10 values
        self.basket1_premiums = self.basket1_premiums[-self.premium_diff_window:] # keep the last 10 values
        
        premium_diff = basket1_premium - basket2_premium

        # TODO: EXPERIMENT WITH ROLLING WINDOWS, FOR NOW HARDCODE THE PREMIUM DIFFS
        # logger.print(f"Basket 1 Premium {basket1_premium}")
        # logger.print(f"Basket 2 Premium {bassket2_premium}")
        # logger.print(f"Basket Premium Diff {premium_diff}")

        # Toggles for whether to arb both baskets.
        arb_baskets = True
        arb_basket2 = True
        mm = True

        # Use rolling z-score to enter and exit on baskets
        self.premium_difference.append(premium_diff)
        self.premium_difference = self.premium_difference[-self.premium_diff_window:] # keep the last 10 values

        # logger.print(f"{len(self.premium_difference)} {self.premium_difference}")        

        if len(self.premium_difference) < self.premium_diff_window:
            # logger.print("Not enough data to calculate z-score")
            if mm:
                self.market_make_basket2(state)
            return
        
        premium_difference = np.std(self.premium_difference)

        rolling = True
        if rolling:
            prem_diff_mean = np.mean(np.array(self.basket1_premiums) - np.array(self.basket2_premiums))
        else:
            prem_diff_mean = self.premium_diff_mean

        # logger.print(f"Premium Difference STD {premium_difference}")
        premium_difference_z_score = (premium_diff - prem_diff_mean) / premium_difference

        basket2_premium_std = np.std(self.basket2_premiums)
        if rolling:
            basket2_premium_mean = np.mean(self.basket2_premiums)
        else:
            basket2_premium_mean = self.basket_2_premium_mean

        # logger.print(f"Basket 2 STD {basket2_premium_std}")

        basket2_z_score = (basket2_premium - basket2_premium_mean) / basket2_premium_std

        # logger.print(f"Premium Z-Scores: {basket2_z_score:.1f}, {premium_difference_z_score:.1f}")

        # Basket stat arbing
        if premium_difference_z_score > self.z_score_threshold and arb_baskets: # mean + 1std 
            # Go short on basket 1 and long on basket 2, and automatically hedge
            self.short_basket_1(state, product_data)

        elif premium_difference_z_score < -self.z_score_threshold and arb_baskets: # mean - 1std
            # Go long on basket 1 and short on basket 2, and automatically hedge
            self.long_basket_1(state, product_data)

        # Check if we aren't trading baskets on this turn so we can do arb on basket 2
        # I don't want to implement the logic to track everything dynamically, and I don't think
        # it's worth doing, so this is a good enough solution IMO, can discuss it later.
        if self.basket1_pos != 0:
            self.trade_on_turn = True
            return 
        

        # continuing if we aren't trading so we can arb basket 2
        if basket2_z_score > self.z_score_threshold_basket_2  and arb_basket2: # mean + 1std
            self.short_basket_2(state, product_data) # short basket 2 and hedge accordingly

        elif basket2_z_score < -self.z_score_threshold_basket_2 and arb_basket2:
            self.long_basket_2(state, product_data) # long basket 2 and hedge accordingly

        if self.trade_on_turn:
            # dont market make on baskets, lets not complicate shit
            return
        
        # final ly, do mm on basket2
        if mm:
            self.market_make_basket2(state)

    def update_basket2_pos(self, state):
        # update basket 2 position
        # look through trades we made on picnic basket 2 and update our position accordingly

        # logger.print("Traded on last turn?", self.trade_on_turn)
        if self.trade_on_turn:
            self.trade_on_turn = False
            return 

        # logger.print("Old Basket 2 Market Making Position: ", self.basket2_market_make_pos)
        for trade in state.own_trades.get('PICNIC_BASKET2', []):
            if trade.timestamp == state.timestamp - 100:
                if trade.buyer == 'SUBMISSION':
                    self.basket2_market_make_pos += abs(trade.quantity)

                elif trade.seller == 'SUBMISSION':
                    self.basket2_market_make_pos -= abs(trade.quantity)
                    
        # logger.print("Basket 2 Market Making Position: ", self.basket2_market_make_pos)
        self.trade_on_turn = False

    def market_make_basket2(self, state):
        # position limits
        low = -50
        high = 50

        position = state.position.get("PICNIC_BASKET2", 0)

        max_buy = high - position
        max_sell = position - low

        order_book = state.order_depths['PICNIC_BASKET2']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders
        basket2_pos = self.basket2_market_make_pos

        # logger.print("Basket 2 position for market making: ", basket2_pos)

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            
            fair_price = int(math.ceil((ask + bid) / 2))  # try changing this to floor maybe

            decimal_fair_price = (ask + bid) / 2

            self.search_buys(state, 'PICNIC_BASKET2', decimal_fair_price, depth=3)
            self.search_sells(state, 'PICNIC_BASKET2', decimal_fair_price, depth=3)

            # Check if there's another market maker
            best_ask = self.get_ask(state, 'PICNIC_BASKET2', fair_price)
            best_bid =  self.get_bid(state, 'PICNIC_BASKET2', fair_price)

            # our ordinary market
            buy_price = math.floor(decimal_fair_price) - 2
            sell_price = math.ceil(decimal_fair_price) + 2
        
            # update market if someone else is better than us
            if best_ask is not None and best_bid is not None:
                ask = best_ask
                bid = best_bid
                
                # check if we move our market if the price is still good
                if ask - 1 > decimal_fair_price:
                    sell_price = ask - 1
                
                if bid + 1 < decimal_fair_price:
                    buy_price = bid + 1 
            
            max_buy =  8 - basket2_pos - self.basket2_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = basket2_pos + 8 - self.basket2_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(basket2_pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('PICNIC_BASKET2', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(basket2_pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('PICNIC_BASKET2', sell_price, -max_sell)

    def market_make_basket1_new(self, state):
        # position limits
        low = -50
        high = 50

        position = state.position.get("PICNIC_BASKET1", 0)

        max_buy = high - position
        max_sell = position - low

        order_book = state.order_depths['PICNIC_BASKET1']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders
        basket1_pos = self.get_product_pos(state, 'PICNIC_BASKET1')

        # logger.print("Basket 2 position for market making: ", basket1_pos)

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            
            fair_price = int(math.ceil((ask + bid) / 2))  # try changing this to floor maybe

            decimal_fair_price = (ask + bid) / 2

            self.search_buys(state, 'PICNIC_BASKET1', decimal_fair_price, depth=3)
            self.search_sells(state, 'PICNIC_BASKET1', decimal_fair_price, depth=3)

            # Check if there's another market maker
            best_ask = self.get_ask(state, 'PICNIC_BASKET1', fair_price)
            best_bid =  self.get_bid(state, 'PICNIC_BASKET1', fair_price)

            # our ordinary market
            buy_price = math.floor(decimal_fair_price) - 2
            sell_price = math.ceil(decimal_fair_price) + 2
        
            # update market if someone else is better than us
            if best_ask is not None and best_bid is not None:
                ask = best_ask
                bid = best_bid
                
                # check if we move our market if the price is still good
                if ask - 1 > decimal_fair_price:
                    sell_price = ask - 1
                
                if bid + 1 < decimal_fair_price:
                    buy_price = bid + 1 
            
            max_buy =  600 - basket1_pos - self.basket1_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = basket1_pos + 600 - self.basket1_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(basket1_pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('PICNIC_BASKET1', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(basket1_pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('PICNIC_BASKET1', sell_price, -max_sell)

    def market_make_basket2_new(self, state):
        # position limits
        low = -50
        high = 50

        position = state.position.get("PICNIC_BASKET2", 0)

        max_buy = high - position
        max_sell = position - low

        order_book = state.order_depths['PICNIC_BASKET2']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders
        basket2_pos = self.get_product_pos(state, 'PICNIC_BASKET2')

        # logger.print("Basket 2 position for market making: ", basket2_pos)

        if len(sell_orders) != 0 and len(buy_orders) != 0:
            ask, _ = list(sell_orders.items())[-1] # worst ask
            bid, _ = list(buy_orders.items())[-1]  # worst bid
            
            fair_price = int(math.ceil((ask + bid) / 2))  # try changing this to floor maybe

            decimal_fair_price = (ask + bid) / 2

            self.search_buys(state, 'PICNIC_BASKET2', decimal_fair_price, depth=3)
            self.search_sells(state, 'PICNIC_BASKET2', decimal_fair_price, depth=3)

            # Check if there's another market maker
            best_ask = self.get_ask(state, 'PICNIC_BASKET2', fair_price)
            best_bid =  self.get_bid(state, 'PICNIC_BASKET2', fair_price)

            # our ordinary market
            buy_price = math.floor(decimal_fair_price) - 2
            sell_price = math.ceil(decimal_fair_price) + 2
        
            # update market if someone else is better than us
            if best_ask is not None and best_bid is not None:
                ask = best_ask
                bid = best_bid
                
                # check if we move our market if the price is still good
                if ask - 1 > decimal_fair_price:
                    sell_price = ask - 1
                
                if bid + 1 < decimal_fair_price:
                    buy_price = bid + 1 
            
            max_buy =  100 - basket2_pos - self.basket2_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = basket2_pos + 100 - self.basket2_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(basket2_pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('PICNIC_BASKET2', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(basket2_pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('PICNIC_BASKET2', sell_price, -max_sell)

    # TODO: UPDATE WHENEVER YOU ADD A NEW PRODUCT
    def reset_orders(self, state):
        self.orders = {}
        self.conversions = 0

        # reset order counts and positions
        self.resin_position = self.get_product_pos(state, 'RAINFOREST_RESIN')
        self.resin_buy_orders = 0
        self.resin_sell_orders = 0

        self.kelp_position = self.get_product_pos(state, 'KELP')
        self.kelp_buy_orders = 0
        self.kelp_sell_orders = 0

        self.squid_ink_position = self.get_product_pos(state, 'SQUID_INK')
        self.squid_ink_buy_orders = 0
        self.squid_ink_sell_orders = 0

        self.basket1_pos = 0 # We aren't trading basket 1 rn

        self.basket2_sell_orders = 0
        self.basket2_buy_orders = 0

        self.volcanic_rock_buy_orders = 0
        self.volcanic_rock_sell_orders = 0

        for product in state.order_depths:
            self.orders[product] = []

    def check_orders(self, state):  
        for trade in state.own_trades.get('MAGNIFICENT_MACARONS', []):
            if trade.timestamp == state.timestamp - 100:
                self.total_trades += abs(trade.quantity)
        
        # logger.print("Total Trades: ", self.total_trades)

    # ------------------ NEW ORCHIDS -----------------------

    def trade_macaroni(self, state):
        position = self.get_product_pos(state, "MAGNIFICENT_MACARONS")

        # if we have a position, convert it
        if position < 0:
            # logger.print(f"Buying {min(abs(position), 10)} macaronis From South Arch.")
            self.conversions += min(abs(position), 10) # can only do 10 at a time
            self.total_fills += 1

        elif position > 0:
            # logger.print(f"Selling {min(abs(position), 10)} macaronis to South Arch.")
            self.conversions += min(abs(position), 10)
            self.total_fills += 1

        obs = state.observations.conversionObservations.get('MAGNIFICENT_MACARONS', None)

        if obs is None:
            return
            # bids 

        conversion_ask = obs.askPrice
        conversion_bid = obs.bidPrice

        # fees
        export_tariff = obs.exportTariff
        import_tariff = obs.importTariff
        transport_fee = obs.transportFees

        sell_local_break_even_price = conversion_ask + import_tariff + transport_fee        # buy from the island and sell local
        buy_local_break_even_price = conversion_bid - export_tariff - transport_fee - 0.1   # sell from the island and buy local

        # logger.print(f"Local Break Even on Sell: {sell_local_break_even_price}")
        # logger.print(f"Local Break Even on Buy : {buy_local_break_even_price}")
        
        # WE BREAK EVEN / MAKE A LITTLE AT THESE SELL & BUY PRICES
        # sell_price = math.ceil(sell_local_break_even_price+0.5) # apparently remove this and we get to 109k 
        # order_depth = state.order_depths['MAGNIFICENT_MACARONS']

        island_mid = (conversion_ask + conversion_bid) / 2

        sell_price = math.ceil(sell_local_break_even_price)
        sell_price = max(math.floor(island_mid), sell_price)  # 5848 in 1k steps

        buy_price = math.floor(buy_local_break_even_price)
        buy_price = min(math.ceil(island_mid), buy_price)  # 5848 in 1k steps


        # sell_price = max(sell_price, math.floor(sell_local_break_even_price))
        max_sell = self.get_product_pos(state, 'MAGNIFICENT_MACARONS') + 20
        # max_buy = self.get_product_pos(state, 'MAGNIFICENT_MACARONS') - 20

        self.send_sell_order('MAGNIFICENT_MACARONS', sell_price, -max_sell, msg=f'MAGNIFICENT_MACARONS: Sell {max_sell} @ {sell_price}')   
        # self.send_buy_order('MAGNIFICENT_MACARONS', buy_price,  max_buy,  msg=f'MAGNIFICENT_MACARONS: Buy {max_buy} @ {buy_price}') 

    def run(self, state: TradingState):        
        self.reset_orders(state)
        self.check_orders(state)

        self.trade_resin(state)
        self.trade_kelp(state)
        self.trade_squid(state)
        self.trade_baskets(state)
        self.trade_vouchers(state)
        # self.trade_macaroni(state)

        # logger.flush(state, self.orders, self.conversions, self.traderData)
        return self.orders, self.conversions, self.traderData
