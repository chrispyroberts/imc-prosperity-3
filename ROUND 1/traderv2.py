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
        if len(value) <= max_length:
            return value

        return value[: max_length - 3] + "..."

logger = Logger()

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
        self.squid_ink_prices = []
        self.squid_ink_ema_short = None
        self.squid_ink_ema_long = None
        self.squid_ink_short_window = 600
        self.squid_ink_long_window = 1400 


    # define easier sell and buy order functions
    def send_sell_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        if msg is not None:
            logger.print(msg)

    def send_buy_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, int(price), amount))

        if msg is not None:
            logger.print(msg)

    def printStuff(self, state):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))        

    # TODO: UPDATE WHENEVER YOU ADD A NEW PRODUCT
    def get_product_pos(self, state, product):
        if product == 'RAINFOREST_RESIN':
            pos = state.position.get('RAINFOREST_RESIN', 0)
        elif product == 'KELP':
            pos = state.position.get('KELP', 0)
        elif product == 'SQUID_INK':
            pos = state.position.get('SQUID_INK', 0)
        else:
            raise ValueError(f"Unknown product: {product}")

        return pos
                
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
                        self.send_buy_order(product, ask, size, msg=f"TRADE BUY {str(size)} x @ {ask}")

                    elif product == 'KELP':
                        size = min(50-self.kelp_position-self.kelp_buy_orders, -amount)
                        self.kelp_buy_orders += size 
                        self.send_buy_order(product, ask, size, msg=f"TRADE BUY {str(size)} x @ {ask}")
                    
                    elif product == 'SQUID_INK':
                        size = min(50-self.squid_ink_position-self.squid_ink_buy_orders, -amount)
                        self.squid_ink_buy_orders += size 
                        self.send_buy_order(product, ask, size, msg=f"TRADE BUY {str(size)} x @ {ask}")
                    
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
                        self.send_sell_order(product, bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")

                    elif product == 'KELP':
                        size = min(self.kelp_position + 50 - self.kelp_sell_orders, amount)
                        self.kelp_sell_orders += size
                        self.send_sell_order(product, bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")
                    
                    elif product == 'SQUID_INK':
                        size = min(self.squid_ink_position + 50 - self.squid_ink_sell_orders, amount)
                        self.squid_ink_sell_orders += size
                        self.send_sell_order(product, bid, -size, msg=f"TRADE SELL {str(-size)} x @ {bid}")

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

    def get_second_bid(self, state, product):
        order_depth = state.order_depths[product]
        if len(order_depth.buy_orders) != 0:
            orders = list(order_depth.buy_orders.items())
            if len(orders) < 2:
                return None
            else:
                bid, _ = orders[1]
                return bid
            
        return None
    
    def get_second_ask(self, state, product):
        order_depth = state.order_depths[product]
        if len(order_depth.sell_orders) != 0:
            orders = list(order_depth.sell_orders.items())
            if len(orders) < 2:
                return None
            else:
                ask, _ = orders[1]
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
        buy_price = 9996
        sell_price = 10004  

        # update market if someone else is better than us
        if best_ask is not None and best_bid is not None:
            ask = best_ask
            bid = best_bid
            
            sell_price = ask - 1
            buy_price = bid + 1
    
        max_buy =  50 - self.resin_position - self.resin_buy_orders 
        max_sell = self.resin_position + 50 - self.resin_sell_orders

        self.send_sell_order('RAINFOREST_RESIN', sell_price, -max_sell, msg=f"RAINFOREST_RESIN: MARKET MADE Sell {max_sell} @ {sell_price}")
        self.send_buy_order('RAINFOREST_RESIN', buy_price, max_buy, msg=f"RAINFOREST_RESIN: MARKET MADE Buy {max_buy} @ {buy_price}")

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

            logger.print(f"KELP FAIR PRICE: {decimal_fair_price}")
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
                
                sell_price = ask - 1
                buy_price = bid + 1

            max_buy =  50 - self.kelp_position - self.kelp_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = self.kelp_position + 50 - self.kelp_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            self.send_buy_order('KELP', buy_price, max_buy, msg=f"KELP: MARKET MADE Buy {max_buy} @ {buy_price}")
            self.send_sell_order('KELP', sell_price, -max_sell, msg=f"KELP: MARKET MADE Sell {max_sell} @ {sell_price}")

    def trade_squid_ink(self, state):
        order_book = state.order_depths['SQUID_INK']
        position = state.position.get("SQUID_INK", 0)
        
        if len(order_book.sell_orders) != 0 and len(order_book.buy_orders) != 0:
            best_ask = min(order_book.sell_orders.keys())
            best_bid = max(order_book.buy_orders.keys())
            mid_price = (best_ask + best_bid) / 2
            spread = best_ask - best_bid
            
            self.squid_ink_prices.append(mid_price)
            
            # window stuff
            max_history = max(self.squid_ink_short_window, self.squid_ink_long_window) * 3
            if len(self.squid_ink_prices) > max_history:
                self.squid_ink_prices = self.squid_ink_prices[-max_history:]
            
            # EMA
            if len(self.squid_ink_prices) >= self.squid_ink_long_window:
                if self.squid_ink_ema_short is None:
                    self.squid_ink_ema_short = sum(self.squid_ink_prices[-self.squid_ink_short_window:]) / self.squid_ink_short_window
                    self.squid_ink_ema_long = sum(self.squid_ink_prices[-self.squid_ink_long_window:]) / self.squid_ink_long_window
                else:
                    alpha_short = 2 / (self.squid_ink_short_window + 1)
                    alpha_long = 2 / (self.squid_ink_long_window + 1)
                    self.squid_ink_ema_short = (mid_price * alpha_short) + (self.squid_ink_ema_short * (1 - alpha_short))
                    self.squid_ink_ema_long = (mid_price * alpha_long) + (self.squid_ink_ema_long * (1 - alpha_long))
                
                # momemtum(formulas are vibe coded)
                trend_strength = self.squid_ink_ema_short - self.squid_ink_ema_long
                
                recent_prices = self.squid_ink_prices[-10:]
                # volatility = max(recent_prices) - min(recent_prices) if len(recent_prices) > 1 else spread
                volatility = np.std(np.diff(np.log(recent_prices))) if len(recent_prices) > 1 else spread
                

                logger.print(f"SQUID_INK - Mid: {mid_price:.2f}")
                logger.print(f"EMA5: {self.squid_ink_ema_short:.2f}")
                logger.print(f"EMA15: {self.squid_ink_ema_long:.2f}")
                logger.print(f"Trend: {trend_strength:.2f}")
                logger.print(f"Vol: {volatility:.2f}")
                
                
                max_position = 50  # Position limit
                trend_confidence = min(abs(trend_strength) / (volatility/2), 1.0) if volatility > 0 else 0.5
                
                # trend following(some what vibe coded)
                if trend_strength > 0:  
                    target_pos = int(max_position * trend_confidence)
                else:  
                    target_pos = int(-max_position * trend_confidence)
                
                self.search_buys(state, 'SQUID_INK', self.squid_ink_ema_short * 0.995, depth=1)
                self.search_sells(state, 'SQUID_INK', self.squid_ink_ema_short * 1.005, depth=1)
                
                position_delta = target_pos - position
                
                # aggressive or passive trades
                if trend_strength > 0:  
                    buy_price = best_bid
                    sell_price = max(best_ask, self.squid_ink_ema_short * 1.01)
                else:  
                    buy_price = min(best_bid, self.squid_ink_ema_short * 0.99)
                    sell_price = best_ask
                
                # Execute trades 
                if position_delta > 0: 
                    remaining_buy = min(position_delta, max_position - position - self.squid_ink_buy_orders)
                    if remaining_buy > 0:
                        self.squid_ink_buy_orders += remaining_buy
                        self.send_buy_order('SQUID_INK', int(buy_price), remaining_buy, 
                                        msg=f"SQUID_INK: TREND BUY {remaining_buy} @ {buy_price}")
                
                elif position_delta < 0:  
                    remaining_sell = min(abs(position_delta), position + max_position - self.squid_ink_sell_orders)
                    if remaining_sell > 0:
                        self.squid_ink_sell_orders += remaining_sell
                        self.send_sell_order('SQUID_INK', int(sell_price), -remaining_sell, 
                                        msg=f"SQUID_INK: TREND SELL {remaining_sell} @ {sell_price}")
                
                # Rreduce extreme positions if trend weakens
                if abs(trend_strength) < volatility * 0.2:  
                    if position > 20 and self.squid_ink_sell_orders < 10:
                        # Reduce long position
                        risk_reduce = min(position - 20, position + max_position - self.squid_ink_sell_orders)
                        if risk_reduce > 0:
                            self.squid_ink_sell_orders += risk_reduce
                            self.send_sell_order('SQUID_INK', int(best_bid), -risk_reduce, 
                                            msg=f"SQUID_INK: RISK-REDUCE SELL {risk_reduce} @ {best_bid}")
                    
                    elif position < -20 and self.squid_ink_buy_orders < 10:
                        # Reduce short position
                        risk_reduce = min(abs(position) - 20, max_position - position - self.squid_ink_buy_orders)
                        if risk_reduce > 0:
                            self.squid_ink_buy_orders += risk_reduce
                            self.send_buy_order('SQUID_INK', int(best_ask), risk_reduce, 
                                            msg=f"SQUID_INK: RISK-REDUCE BUY {risk_reduce} @ {best_ask}")
                
                # finally market make
                remaining_buy = max_position - position - self.squid_ink_buy_orders
                remaining_sell = position + max_position - self.squid_ink_sell_orders
                
                passive_buy_price = max(best_bid - spread, self.squid_ink_ema_long * 0.98)
                self.send_buy_order('SQUID_INK', int(passive_buy_price), remaining_buy, 
                                msg=f"SQUID_INK: PASSIVE BUY {remaining_buy} @ {passive_buy_price}")
            
                passive_sell_price = min(best_ask + spread, self.squid_ink_ema_long * 1.02)
                self.send_sell_order('SQUID_INK', int(passive_sell_price), -remaining_sell, 
                                msg=f"SQUID_INK: PASSIVE SELL {remaining_sell} @ {passive_sell_price}")
            
            else:
                # only market make
                logger.print(f"SQUID_INK: Building price history ({len(self.squid_ink_prices)}/{self.squid_ink_long_window})")
                fair_price = mid_price
                buy_price = fair_price - spread
                sell_price = fair_price + spread
                
                max_buy = 50 - position - self.squid_ink_buy_orders
                max_sell = position + 50 - self.squid_ink_sell_orders
                
                self.send_buy_order('SQUID_INK', int(buy_price), max_buy, 
                                msg=f"SQUID_INK: INIT BUY {max_buy} @ {buy_price}")
                self.send_sell_order('SQUID_INK', int(sell_price), -max_sell, 
                                msg=f"SQUID_INK: INIT SELL {max_sell} @ {sell_price}")
        else:
            logger.print("SQUID_INK: Insufficient market data")
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

        for product in state.order_depths:
            self.orders[product] = []

    def run(self, state: TradingState):        
        self.reset_orders(state)

        self.trade_resin(state)
        self.trade_kelp(state)
        self.trade_squid_ink(state)

        logger.flush(state, self.orders, self.conversions, self.traderData)
        return self.orders, self.conversions, self.traderData