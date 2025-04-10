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

        # ROUND 2
        # basket1
        self.basket1_premiums = []
        self.basket1_pos = 0
        self.basket2_pos = 0 # track independently

        # basket2
        self.basket2_premiums = []

    # define easier sell and buy order functions
    def send_sell_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        if msg is not None:
            logger.print(msg)

    def send_buy_order(self, product, price, amount, msg=None):
        self.orders[product].append(Order(product, price, amount))

        if msg is not None:
            logger.print(msg)

    def printStuff(self, state):
        logger.print("traderData: " + state.traderData)
        logger.print("Observations: " + str(state.observations))        

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
                self.send_buy_order('KELP', buy_price, max_buy, msg=f"KELP: MARKET MADE Buy {max_buy} @ {buy_price}")
            
            # if we are in short, and our best sell price IS the fair price, don't sell more
            if not(pos < 0 and float(sell_price) == decimal_fair_price):
                self.send_sell_order('KELP', sell_price, -max_sell, msg=f"KELP: MARKET MADE Sell {max_sell} @ {sell_price}")

    def trade_squid_ink(self, state):
        # this is the same logic as kelp!
        # position limits
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

            logger.print(f"SQUID_INK FAIR PRICE: {decimal_fair_price}")
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
                
                sell_price = ask - 1
                buy_price = bid + 1

            max_buy =  50 - self.squid_ink_position - self.squid_ink_buy_orders # MAXIMUM SIZE OF MARKET ON BUY SIDE
            max_sell = self.squid_ink_position + 50 - self.squid_ink_sell_orders # MAXIMUM SIZE OF MARKET ON SELL SIDE

            self.send_buy_order('SQUID_INK', buy_price, max_buy, msg=f"SQUID_INK: MARKET MADE Buy {max_buy} @ {buy_price}")
            self.send_sell_order('SQUID_INK', sell_price, -max_sell, msg=f"SQUID_INK: MARKET MADE Sell {max_sell} @ {sell_price}")

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
        basket1_volume_available = product_data['PICNIC_BASKET1']['bid_volume'] # buy this
        basket2_volume_available = product_data['PICNIC_BASKET2']['ask_volume'] # sell this

        # Take the minimum of them
        possible_buys = min(basket2_volume_available, basket1_volume_available, 
                          djembe_volume_available, jam_volume_available,
                          crossaint_volume_available // 2)
        
        # calculate how many we can sell before we hit our position limit   
        self.get_product_pos(state, 'PICNIC_BASKET1')
        buy_limit = 60 - self.get_product_pos(state, 'PICNIC_BASKET1')
        basket1_pos = min(buy_limit, possible_buys)

        
        self.basket1_pos = basket1_pos # record this

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # sell CROISSANTS
        price = product_data['CROISSANTS']['bid']
        size = -basket1_pos * 2
        self.send_sell_order('CROISSANTS', price, size,  
                             msg=F'LONG-BASKET-1: SELL {abs(size)} CROISSANTS @ {price}')
        
        # sell djembe
        price = product_data['DJEMBES']['bid']
        size = -basket1_pos
        self.send_sell_order('DJEMBES', price, size,  
                             msg=F'LONG-BASKET-1: SELL {abs(size)} DJEMBES @ {price}')

        # sell jam
        price = product_data['JAMS']['bid']
        size = -basket1_pos
        self.send_sell_order('JAMS', price, size,  
                             msg=F'LONG-BASKET-1: SELL {abs(size)} JAMS @ {price}')  
        
       # buy basket 1
        price = product_data['PICNIC_BASKET1']['ask']
        size = basket1_pos
        self.send_buy_order('PICNIC_BASKET1', price, size,
                             msg=F'LONG-BASKET-1: BUY {abs(size)} PICNIC_BASKET1 @ {price}')     

        # sell basket2
        price = product_data['PICNIC_BASKET2']['bid']
        size = -basket1_pos
        self.send_sell_order('PICNIC_BASKET2', price, size,  
                             msg=F'LONG-BASKET-1: SELL {abs(size)} PICNIC_BASKET2 @ {price}')     

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

        # buy CROISSANTS
        price = product_data['CROISSANTS']['ask']
        size = basket1_pos * 2
        self.send_buy_order('CROISSANTS', price, size,  
                             msg=F'SHORT-BASKET-1: BUY {abs(size)} CROISSANTS @ {price}')
        
        # buy djembe
        price = product_data['DJEMBES']['ask']
        size = basket1_pos
        self.send_buy_order('DJEMBES', price, size,  
                             msg=F'SHORT-BASKET-1: BUY {abs(size)} DJEMBES @ {price}')

        # buy jam
        price = product_data['JAMS']['ask']
        size = basket1_pos
        self.send_buy_order('JAMS', price, size,  
                             msg=F'SHORT-BASKET-1: BUY {abs(size)} JAMS @ {price}')        
                
        # sell basket1
        price = product_data['PICNIC_BASKET1']['bid']
        size = -basket1_pos
        self.send_sell_order('PICNIC_BASKET1', price, size,  
                             msg=F'SHORT-BASKET-1: SELL {abs(size)} PICNIC_BASKET1 @ {price}')          

        # buy basket2
        price = product_data['PICNIC_BASKET2']['ask']
        size = basket1_pos
        self.send_buy_order('PICNIC_BASKET2', price, size,  
                             msg=F'SHORT-BASKET-1: BUY {abs(size)} PICNIC_BASKET2 @ {price}')          

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

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # sell CROISSANTS
        price = product_data['CROISSANTS']['bid']
        size = -basket2_pos * 4
        self.send_sell_order('CROISSANTS', price, size,  
                             msg=F'LONG-BASKET-2: SELL {abs(size)} CROISSANTS @ {price}')

        # sell jam
        price = product_data['JAMS']['bid']
        size = -basket2_pos * 2
        self.send_sell_order('JAMS', price, size,  
                             msg=F'LONG-BASKET-2: SELL {abs(size)} JAMS @ {price}') 
        
        # buy basket2
        price = product_data['PICNIC_BASKET2']['ask']
        size = basket2_pos
        self.send_buy_order('PICNIC_BASKET2', price, size,  
                             msg=F'LONG-BASKET-2: BUY {abs(size)} PICNIC_BASKET2 @ {price}')    

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
        buy_limit = 32 + self.basket2_pos 
        basket2_pos = min(buy_limit, possible_sells)

        # Send out orders! Doing this ensures we never have to check if we are hedged, because we only
        # ever send our orders to b uy everything in a manner that would ensure we are hedged, simplifying any logic

        # buy CROISSANTS
        price = product_data['CROISSANTS']['ask']
        size = basket2_pos * 4
        self.send_buy_order('CROISSANTS', price, size,  
                             msg=F'SHORT-BASKET-2: BUY {abs(size)} CROISSANTS @ {price}')

        # buy jam
        price = product_data['JAMS']['ask']
        size = basket2_pos * 2
        self.send_buy_order('JAMS', price, size,  
                             msg=F'SHORT-BASKET-2: BUY {abs(size)} JAMS @ {price}') 
        
        # sell basket2
        price = product_data['PICNIC_BASKET2']['bid']
        size = -basket2_pos
        self.send_sell_order('PICNIC_BASKET2', price, size,  
                             msg=F'SHORT-BASKET-2: SELL {abs(size)} PICNIC_BASKET2 @ {price}')    

        self.basket2_pos += basket2_pos # update our basket2 position

    def trade_baskets(self, state):
        # get the midprice of all items
        
        products = ['PICNIC_BASKET1', 'PICNIC_BASKET2', 'JAMS', 'CROISSANTS', 'DJEMBES']
        product_data = {}

        for p in products:
            product_data[p] = self.get_market_data(state, p)

        basket1_premium, basket2_premium = self.get_basket_premiums(state, product_data)

        self.basket1_premiums.append(basket1_premium)
        self.basket2_premiums.append(basket2_premium)

        premium_diff = basket1_premium - basket2_premium

        # TODO: EXPERIMENT WITH ROLLING WINDOWS, FOR NOW HARDCODE THE PREMIUM DIFFS
        logger.print(f"Basket 1 Premium {basket1_premium}")
        logger.print(f"Basket 2 Premium {basket2_premium}")
        logger.print(f"Basket Premium Diff {premium_diff}")

        # Toggles for whether to arb both baskets.
        arb_baskets = True
        arb_basket2 = True

        # Basket stat arbing
        if premium_diff > 100 and arb_baskets: # mean + 1std 
            logger.print("Go short on basket 1 and long on basket 2")
            # Go short on basket 1 and long on basket 2, and automatically hedge
            self.short_basket_1(state, product_data)

        elif premium_diff < -50 and arb_baskets: # mean - 1std
            logger.print("Go long on basket 1 and short on basket 2")
            # Go long on basket 1 and short on basket 2, and automatically hedge
            self.long_basket_1(state, product_data)

        # Check if we aren't trading baskets on this turn so we can do arb on basket 2
        # I don't want to implement the logic to track everything dynamically, and I don't think
        # it's worth doing, so this is a good enough solution IMO, can discuss it later.
        if self.basket1_pos != 0:
            return 
        
        # continuing if we aren't trading so we can arb basket 2
        if basket2_premium > 90 and arb_basket2: # mean + 1std
            self.short_basket_2(state, product_data) # short basket 2 and hedge accordingly
        
        elif basket2_premium < -30 and arb_basket2:
            self.long_basket_2(state, product_data) # long basket 2 and hedge accordingly

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

        for product in state.order_depths:
            self.orders[product] = []

    def run(self, state: TradingState):        
        self.reset_orders(state)

        # self.trade_resin(state)
        # self.trade_kelp(state)
        # self.trade_squid_ink(state)
        self.trade_baskets(state)

        logger.flush(state, self.orders, self.conversions, self.traderData)
        return self.orders, self.conversions, self.traderData
