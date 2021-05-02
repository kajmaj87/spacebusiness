from random import random

import esper

import globals
from components import (
    BuyOrder,
    Details,
    Money,
    Need,
    Needs,
    OrderStatus,
    Producer,
    Resource,
    SellOrder,
    Storage,
    Wallet,
)
from log import log


class Ordering(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        log.debug("\nOrdering Phase started")
        self.create_sell_orders()
        self.create_buy_orders()

    def decide_order_price_for_buy(self, details: Details, need: Need, wallet: Wallet):
        last_price, status = wallet.last_transaction_details_for(need.resource_type())
        if status is None:
            bid_price = wallet.money.multiply(random() * 0.2)
            log.debug(f"{details.name} knows nothing about prices of {need.resource_type()}. Guessing: {bid_price}")
        else:
            if status == OrderStatus.BOUGHT:
                bid_price = last_price.multiply(need.price_change_on_buy)
                log.debug(f"{details.name} bought {need.resource_type()} for {last_price}. Will try to order for {bid_price}")
            elif status == OrderStatus.CANCELLED:
                if globals.stats_history.has_stats_for_day(globals.star_date.yesterday(), need.resource_type()):
                    # yesterday_stats = globals.stats_history.stats_for_day(globals.star_date.yesterday(), need.resource_type())
                    # median = yesterday_stats.sell_stats.median
                    # bid_price = (median + last_price).split()[0] if median is not None else last_price
                    bid_price = max(last_price.multiply(need.price_change_on_failed_buy), last_price + Money(1))
                    log.debug(f"{details.name} failed to buy {need.resource_type()} for {last_price}." f" Will try to order for {bid_price}")
                else:
                    bid_price = last_price
                    log.debug(f"{details.name} has no info about yesterday prices of {need.resource_type()}. Ordering for last price {last_price}")
            else:
                raise Exception(f"Unexpected transaction status: {status}")
        return max(bid_price, Money(1))

    def create_buy_orders(self):
        def decide_to_place_buy_order(owner, resouce: Resource, wallet: Wallet, max_bid_price: Money):
            if resouce == Resource.NOTHING:
                log.debug(f"{details.name} won't buy nothing so not placing an order")
            elif not storage.will_fit_one_of(resouce):
                log.debug(f"{details.name} did not order {resouce} (no storage space left)")
            else:
                if wallet.money < max_bid_price:
                    log.debug(
                        f"{details.name} did not affort {max_bid_price} to order {resouce}. Has only {wallet.money} left. Will bid for this amount instead"
                    )
                bid = min(max_bid_price, wallet.money)
                if wallet.money.creds > 0:
                    wallet.money -= bid
                    buy_order = create_buy_order(owner, resouce, bid)
                    log.debug(f"{details.name} created a {buy_order}")
                else:
                    log.debug(f"{details.name} has no money left to create orders")

        def create_buy_order(owner, resource: Resource, max_bid_price: Money) -> BuyOrder:
            buy_order_ent = self.world.create_entity()
            buy_order = BuyOrder(owner, resource, max_bid_price)
            self.world.add_component(buy_order_ent, buy_order)
            return buy_order

        needers = self.world.get_components(Details, Storage, Needs, Wallet)
        for ent, (details, storage, needs, wallet) in needers:
            for need in needs:
                if not need.is_fullfilled(storage):
                    log.debug(f"{details.name} wants to {need.name}")
                    bid_price = self.decide_order_price_for_buy(details, need, wallet)
                    decide_to_place_buy_order(ent, need.pile.resource_type, wallet, bid_price)

    def decide_order_price_for_sell(self, details, resource_type, wallet: Wallet) -> Money:
        last_price, status = wallet.last_transaction_details_for(resource_type)
        if status is None:
            bid_price = Money(int(random() * 200 + 50))
            log.debug(f"{details.name} knows nothing about prices of {resource_type}. Guessing: {bid_price}")
        else:
            if status == OrderStatus.SOLD:
                # TODO Should be handled more in a way as needs are
                # don't get stuck at small values
                bid_price = max(last_price.multiply(1.1), last_price + Money(1))
                log.debug(f"{details.name} sold {resource_type} for {last_price}. Will try to sell for {bid_price}")
            elif status == OrderStatus.CANCELLED:
                bid_price = last_price.multiply(0.9)
                log.debug(f"{details.name} failed to sell {resource_type} for {last_price}. Will try to sell for {bid_price}")
            else:
                raise Exception(f"Unexpected transaction status: {status}")
        return max(bid_price, Money(1))  # TODO make it more sensible, wallet should take all transactions from last turn into account

    def create_sell_orders(self):
        def create_sell_order(owner, resource: Resource, min_bid_price: Money) -> SellOrder:
            sell_order_ent = self.world.create_entity()
            sell_order = SellOrder(owner, resource, min_bid_price)
            self.world.add_component(sell_order_ent, sell_order)
            return sell_order

        producers = self.world.get_components(Details, Storage, Producer, Wallet)
        for ent, (details, storage, producer, wallet) in producers:
            while storage.has_one_of(producer.created_pile()):
                storage.remove_one_of(producer.created_pile())
                bid_price = self.decide_order_price_for_sell(details, producer.created_pile().resource_type, wallet)
                sell_order = create_sell_order(ent, producer.created_pile().resource_type, bid_price)
                log.debug(f"{details.name} created a {sell_order}")
            log.debug(f"{details.name} won't sell {producer.created_pile().resource_type} as it does not have enough of it")
