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

class Logger:
    def __init__(self) -> None:
        self.logs = ""
        self.max_log_length = 3750

    def print(self, *objects: Any, sep: str = " ", end: str = "\n") -> None:
        self.logs += sep.join(map(str, objects)) + end

    def flush(self, state: TradingState, orders: dict[Symbol, list[Order]], conversions: int, trader_data: str) -> None:
        base_length = len(
            self.to_json(
                [
                    self.compress_state(state, ""),
                    self.compress_orders(orders),
                    conversions,
                    "",
                    "",
                ]
            )
        )

        # We truncate state.traderData, trader_data, and self.logs to the same max. length to fit the log limit
        max_item_length = (self.max_log_length - base_length) // 3

        print(
            self.to_json(
                [
                    self.compress_state(state, self.truncate(state.traderData, max_item_length)),
                    self.compress_orders(orders),
                    conversions,
                    self.truncate(trader_data, max_item_length),
                    self.truncate(self.logs, max_item_length),
                ]
            )
        )

        self.logs = ""

    def compress_state(self, state: TradingState, trader_data: str) -> list[Any]:
        return [
            state.timestamp,
            trader_data,
            self.compress_listings(state.listings),
            self.compress_order_depths(state.order_depths),
            self.compress_trades(state.own_trades),
            self.compress_trades(state.market_trades),
            state.position,
            self.compress_observations(state.observations),
        ]

    def compress_listings(self, listings: dict[Symbol, Listing]) -> list[list[Any]]:
        compressed = []
        for listing in listings.values():
            compressed.append([listing.symbol, listing.product, listing.denomination])

        return compressed

    def compress_order_depths(self, order_depths: dict[Symbol, OrderDepth]) -> dict[Symbol, list[Any]]:
        compressed = {}
        for symbol, order_depth in order_depths.items():
            compressed[symbol] = [order_depth.buy_orders, order_depth.sell_orders]

        return compressed

    def compress_trades(self, trades: dict[Symbol, list[Trade]]) -> list[list[Any]]:
        compressed = []
        for arr in trades.values():
            for trade in arr:
                compressed.append(
                    [
                        trade.symbol,
                        trade.price,
                        trade.quantity,
                        trade.buyer,
                        trade.seller,
                        trade.timestamp,
                    ]
                )

        return compressed

    def compress_observations(self, observations: Observation) -> list[Any]:
        conversion_observations = {}
        for product, observation in observations.conversionObservations.items():
            conversion_observations[product] = [
                observation.bidPrice,
                observation.askPrice,
                observation.transportFees,
                observation.exportTariff,
                observation.importTariff,
                observation.sugarPrice,
                observation.sunlightIndex,
            ]

        return [observations.plainValueObservations, conversion_observations]

    def compress_orders(self, orders: dict[Symbol, list[Order]]) -> list[list[Any]]:
        compressed = []
        for arr in orders.values():
            for order in arr:
                compressed.append([order.symbol, order.price, order.quantity])

        return compressed

    def to_json(self, value: Any) -> str:
        return json.dumps(value, cls=ProsperityEncoder, separators=(",", ":"))

    def truncate(self, value: str, max_length: int) -> str:
        lo, hi = 0, min(len(value), max_length)
        out = ""

        while lo <= hi:
            mid = (lo + hi) // 2

            candidate = value[:mid]
            if len(candidate) < len(value):
                candidate += "..."

            encoded_candidate = json.dumps(candidate)

            if len(encoded_candidate) <= max_length:
                out = candidate
                lo = mid + 1
            else:
                hi = mid - 1

        return out

logger = Logger()


BASKET1_LIMIT = 10 # max of 60
BASKET2_LIMIT = 10 # max of 100
SQUID_LIMIT = 15

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

        self.basket1_total_buys = 0
        self.basket1_total_sells = 0
        self.basket2_total_buys = 0
        self.basket2_total_sells = 0
        
        
        # HYPERPARAMS FOR BASKET WEAVING
        #==================================

        #==================================

        self.initialize_round_3()

        self.total_fills = 0

        # round 5 trading logic
        #==================================
        self.croissants_signal = None
        self.squid_signal = None
        self.kelp_signal = None

        # basket2 mm
        self.basket1_buy_orders = 0
        self.basket1_sell_orders = 0
        self.basket1_market_make_pos = 0
        self.trade_on_turn = False

        self.basket1_premiums = []
        self.basket2_premiums = []

   # =======================================
    # ROUND 5 TRADING LOGIC BELOW
    # =======================================

    def check_olivia_trades(self, state):
        # Check if Olivia has made a trade
        products = ['SQUID_INK', 'KELP', 'CROISSANTS']
        for product in products:
            # check our own trades
            for trade in state.own_trades.get(product, []):
                # filter for occuring on this turn or before
                if abs(trade.timestamp - state.timestamp) <= 100:
                    if trade.buyer == 'Olivia':
                        logger.print(f"Olivia BUY {product}")
                        if product == 'SQUID_INK':
                            self.squid_signal = 'BUY'
                        elif product == 'KELP':
                            self.kelp_signal = 'BUY'
                        elif product == 'CROISSANTS':
                            self.croissants_signal = 'BUY'
                
                    elif trade.seller == 'Olivia':
                        logger.print(f"Olivia SELL {product}")
                        if product == 'SQUID_INK':
                            self.squid_signal = 'SELL'
                        elif product == 'KELP':
                            self.kelp_signal = 'SELL'
                        elif product == 'CROISSANTS':
                            self.croissants_signal = 'SELL'

            # check market trades
            for trade in state.market_trades.get(product, []):
                if abs(trade.timestamp - state.timestamp) <= 100:                    
                    if trade.buyer == 'Olivia':
                        logger.print(f"OLIVIA BUY {product}")
                        if product == 'SQUID_INK':
                            self.squid_signal = 'BUY'
                        elif product == 'KELP':
                            self.kelp_signal = 'BUY'
                        elif product == 'CROISSANTS':
                            self.croissants_signal = 'BUY'
                
                    elif trade.seller == 'Olivia':
                        logger.print(f"OLIVIA SELL {product}")
                        if product == 'SQUID_INK':
                            self.squid_signal = 'SELL'
                        elif product == 'KELP':
                            self.kelp_signal = 'SELL'
                        elif product == 'CROISSANTS':
                            self.croissants_signal = 'SELL'

    def olivia_long_croissants(self, state):
        # go long on croissants
        price = self.get_ask(state, 'CROISSANTS')
        if price is not None:
            size = 250 - self.get_product_pos(state, 'CROISSANTS')
            self.send_buy_order('CROISSANTS', price, size)

        price = self.get_ask(state, 'PICNIC_BASKET1')
        if price is not None:
            size = 60 - self.get_product_pos(state, 'PICNIC_BASKET1') + self.basket1_market_make_pos

            if abs(size) > 0:
                self.trade_on_turn = True

            self.send_buy_order('PICNIC_BASKET1', price, size)

        price = self.get_ask(state, 'PICNIC_BASKET2')
        if price is not None:
            size = 100 - self.get_product_pos(state, 'PICNIC_BASKET2')
            self.send_buy_order('PICNIC_BASKET2', price, size)

        # selling djembes
        price = self.get_bid(state, 'DJEMBES')
        if price is not None:
            size = self.get_product_pos(state, 'DJEMBES') + 60
            self.send_sell_order('DJEMBES', price, -size)
        
        # selling jams
        price = self.get_bid(state, 'JAMS')
        if price is not None:
            size = self.get_product_pos(state, 'JAMS') + 350
            self.send_sell_order('JAMS', price, -size)

    def olivia_short_croissants(self, state):
        # go short on croissants
        price = self.get_bid(state, 'CROISSANTS')
        if price is not None:
            size = self.get_product_pos(state, 'CROISSANTS') + 250
            self.send_sell_order('CROISSANTS', price, -size)
        
        # sell 50 basket1 -> buy 50 djembe, buy 150 jam
        price = self.get_bid(state, 'PICNIC_BASKET1')
        if price is not None:
            size = self.get_product_pos(state, 'PICNIC_BASKET1') + 60  - self.basket1_market_make_pos

            if abs(size) > 0:
                self.trade_on_turn = True
                
            self.send_sell_order('PICNIC_BASKET1', price, -size)
        
        # sell 100 basket 2 -> buy 200 jam
        price = self.get_bid(state, 'PICNIC_BASKET2')
        if price is not None:
            size = self.get_product_pos(state, 'PICNIC_BASKET2') + 100
            self.send_sell_order('PICNIC_BASKET2', price, -size)

        # buying djembes
        price = self.get_ask(state, 'DJEMBES')
        if price is not None:
            size = 60 - self.get_product_pos(state, 'DJEMBES')
            self.send_buy_order('DJEMBES', price, size)
        
        # buying jams
        price = self.get_ask(state, 'JAMS')
        if price is not None:
            size = 350 - self.get_product_pos(state, 'JAMS')
            self.send_buy_order('JAMS', price, size)

    def olivia_trading(self, state):
        if self.croissants_signal:
            if self.croissants_signal == 'BUY':   
                logger.print("OLIVIA LONG ON CROISSANTS")             
                self.olivia_long_croissants(state)

            elif self.croissants_signal == 'SELL':
                logger.print("OLIVIA SHORT ON CROISSANTS")
                self.olivia_short_croissants(state)
    
        if self.squid_signal:
            if self.squid_signal == 'BUY':
                price = self.get_ask(state, 'SQUID_INK')
                if price is not None:
                    size = 50 - self.get_product_pos(state, 'SQUID_INK')
                    self.send_buy_order('SQUID_INK', price, size, "OLIVIA BUY SQUID INK")

            elif self.squid_signal == 'SELL':
                price = self.get_bid(state, 'SQUID_INK')
                if price is not None:
                    size = self.get_product_pos(state, 'SQUID_INK') + 50
                    self.send_sell_order('SQUID_INK', price, -size, "OLIVIA SELL SQUID INK")
            
    # =======================================
    # ROUND 3 TRADING LOGIC BELOW
    # =======================================

    def initialize_round_3(self):
        # init call but for round 3

        self.options_model = BlackScholes()

        self.timestamps_per_year = 365e6
        self.days_left = 7 # day 1: 7, day 2: 6, day 3: 5, day 4: 4, day 5: 3

        self.vouchers =  ['VOLCANIC_ROCK_VOUCHER_9500', 'VOLCANIC_ROCK_VOUCHER_9750',
                          'VOLCANIC_ROCK_VOUCHER_10000', 'VOLCANIC_ROCK_VOUCHER_10250',
                          'VOLCANIC_ROCK_VOUCHER_10500']

        # self.vouchers = ['VOLCANIC_ROCK_VOUCHER_10000']

        # windows n shit
        self.underlying_price_history = []
        self.underlying_spread = 0
        self.underlying_price_window = 5

        self.window_size = 10

        self.voucher_trading_threshold = 0.8

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

        self.voucher_ask_ivs = {
            'VOLCANIC_ROCK_VOUCHER_9500' :  [],
            'VOLCANIC_ROCK_VOUCHER_9750' :  [],
            'VOLCANIC_ROCK_VOUCHER_10000' : [],
            'VOLCANIC_ROCK_VOUCHER_10250' : [],
            'VOLCANIC_ROCK_VOUCHER_10500' : []
        }

        self.voucher_bid_ivs = {
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
            if (high_value - low_value) < self.voucher_trading_threshold:
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
                            size = min(SQUID_LIMIT-self.squid_ink_position-self.squid_ink_buy_orders, -amount)

                        self.squid_ink_buy_orders += size 
                        self.send_buy_order(product, ask, size)  

                    elif product == 'PICNIC_BASKET1':
                        size = min(BASKET1_LIMIT-pos-self.basket1_buy_orders, -amount)
                        self.basket1_buy_orders += size
                        self.send_buy_order(product, ask, size)

                    elif product == 'PICNIC_BASKET2':
                        size = min(BASKET2_LIMIT-pos-self.basket2_buy_orders, -amount)
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
                            size = min(self.squid_ink_position + SQUID_LIMIT - self.squid_ink_sell_orders, amount)
                        else:
                            size = min(self.squid_ink_position + SQUID_LIMIT - self.squid_ink_sell_orders, amount)

                        self.squid_ink_sell_orders += size
                        self.send_sell_order(product, bid, -size)

                    elif product == 'PICNIC_BASKET1':
                        size = min(pos + BASKET1_LIMIT - self.basket1_sell_orders, amount)
                        self.basket1_sell_orders += size
                        self.send_sell_order(product, bid, -size)

                    elif product == 'PICNIC_BASKET2':
                        size = min(pos + BASKET2_LIMIT - self.basket2_sell_orders, amount)
                        self.basket2_sell_orders += size
                        self.send_sell_order(product, bid, -size)

    def get_bid(self, state, product, price=None):        
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            for bid, _ in orders:
                if price:
                    if bid < price: # DONT COPY SHIT MARKETS
                        return bid
                else:
                    return bid
        
        return None

    def get_ask(self, state, product, price=None):      
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            for ask, _ in orders: 
                if price:
                    if ask > price: # DONT COPY A SHITY MARKET
                        return ask
                else:
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

    def basket2_mm(self, state):

        if self.trade_on_turn:
            return

        order_book = state.order_depths['PICNIC_BASKET2']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders

        # logger.print("Basket 2 position for market making: ", basket1_pos)

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

            basket2_pos = self.get_product_pos(state, 'PICNIC_BASKET2')       
            max_buy =  BASKET1_LIMIT - basket2_pos - self.basket2_buy_orders 
            max_sell = basket2_pos + BASKET1_LIMIT - self.basket2_sell_orders

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(basket2_pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('PICNIC_BASKET2', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(basket2_pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('PICNIC_BASKET2', sell_price, -max_sell)
   
    def basket1_mm(self, state):

        if self.trade_on_turn:
            return

        order_book = state.order_depths['PICNIC_BASKET1']
        sell_orders = order_book.sell_orders
        buy_orders = order_book.buy_orders

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
            
            basket1_pos = self.get_product_pos(state, 'PICNIC_BASKET1')
            max_buy =  BASKET1_LIMIT - basket1_pos - self.basket1_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = basket1_pos + BASKET1_LIMIT - self.basket1_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            # if we are in long, and our best buy price IS the fair price, don't buy more 
            if not(basket1_pos > 0 and float(buy_price) == decimal_fair_price):
                self.send_buy_order('PICNIC_BASKET1', buy_price, max_buy)
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(basket1_pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('PICNIC_BASKET1', sell_price, -max_sell)
            
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

        self.basket1_buy_orders = 0
        self.basket1_sell_orders =0
        self.basket2_sell_orders = 0
        self.basket2_buy_orders = 0

        self.volcanic_rock_buy_orders = 0
        self.volcanic_rock_sell_orders = 0

        for product in state.order_depths:
            self.orders[product] = []

    def check_orders(self, state):  
        # Macron order checking
        for trade in state.own_trades.get('MAGNIFICENT_MACARONS', []):
            if trade.timestamp == state.timestamp - 100:
                self.total_trades += abs(trade.quantity)      

        logger.print(f"Total trades: {self.total_trades}")

        if self.croissants_signal is None:
            for trade in state.own_trades.get("PICNIC_BASKET1", []):
                if trade.timestamp == state.timestamp - 100:
                    if trade.buyer == 'SUBMISSION':
                        self.basket1_total_buys += abs(trade.quantity)
                    else:
                        self.basket1_total_sells += abs(trade.quantity)

            
            for trade in state.own_trades.get("PICNIC_BASKET2", []):
                if trade.timestamp == state.timestamp - 100:
                    if trade.buyer == 'SUBMISSION':
                        self.basket2_total_buys += abs(trade.quantity)
                    else:
                        self.basket2_total_sells += abs(trade.quantity)

            logger.print(f"Basket 1 Total Buys / Sells : {self.basket1_total_buys} / {self.basket1_total_sells}")
            logger.print(f"Basket 2 Total Buys / Sells : {self.basket2_total_buys} / {self.basket2_total_sells}")

    def trade_macaroni(self, state):
        position = self.get_product_pos(state, "MAGNIFICENT_MACARONS")

        # if we have a position, convert it
        if position < 0:
            # logger.print(f"Buying {min(abs(position), 10)} macaronis From South Arch.")
            self.conversions += min(abs(position), 10) # can only do 10 at a time
            self.total_fills += self.conversions

        logger.print(f"Total Fills: {self.total_fills}")

        obs = state.observations.conversionObservations.get('MAGNIFICENT_MACARONS', None)

        if obs is None:
            return
            # bids 

        conversion_ask = obs.askPrice
        conversion_bid = obs.bidPrice

        # fees
        import_tariff = obs.importTariff
        transport_fee = obs.transportFees

        sell_local_break_even_price = conversion_ask + import_tariff + transport_fee        # buy from the island and sell local

        logger.print(f"Local Break Even on Sell: {sell_local_break_even_price}")

        # island_mid = (conversion_ask + conversion_bid) / 2 use floor of this

        sell_price = math.ceil(sell_local_break_even_price)
        sell_price = max(math.floor(conversion_bid), sell_price)

        max_sell = self.get_product_pos(state, 'MAGNIFICENT_MACARONS') + 20 + self.conversions 

        self.send_sell_order('MAGNIFICENT_MACARONS', sell_price, -max_sell, msg=f'MAGNIFICENT_MACARONS: Sell {max_sell} @ {sell_price}')   

    def run(self, state: TradingState):        
        self.reset_orders(state)
        self.check_orders(state)
        
        # self.check_olivia_trades(state)
        # self.olivia_trading(state)
        # if self.croissants_signal is None:
        #     self.basket2_mm(state)
        #     self.basket1_mm(state)
        # if self.squid_signal is None:
        #     self.trade_squid(state)
        # self.trade_resin(state)
        # self.trade_kelp(state)
        self.trade_vouchers(state)

        logger.flush(state, self.orders, self.conversions, self.traderData)
        return self.orders, self.conversions, self.traderData
    