import statistics
from typing import List

import esper
import icontract as icontract

import globals
from components import (
    BuyOrder,
    Money,
    OrderStatus,
    Resource,
    SellOrder,
    Storage,
    Wallet,
)
from log import log

from .pure import total_money_in_wallets, total_money_locked_in_orders


class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def create_order_pairs(self, buy_orders, sell_orders):
        if len(sell_orders) < len(buy_orders):
            order_pairs = zip(buy_orders[len(buy_orders) - len(sell_orders) :], sell_orders)
        else:
            order_pairs = zip(buy_orders, sell_orders[: len(buy_orders)])
        return order_pairs

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(
        lambda OLD, self: total_money_locked_in_orders(self.world) + total_money_in_wallets(self.world)
        == total_money_locked_in_orders(OLD.self.world) + total_money_in_wallets(OLD.self.world)
    )
    def process(self):
        def order_pairs_are_valid(buy_orders, sell_orders):
            for buy, sell in self.create_order_pairs(buy_orders, sell_orders):
                _, buy_order = buy
                _, sell_order = sell
                if buy_order.price < sell_order.price:
                    log.debug(f"Order Pair: {buy_order} / {sell_order} is invalid.")
                    return False
            return True

        def fix_orders(buy, sell):
            log.debug("Fixing orders")
            return buy[1:], sell

        log.debug("\nExchange Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        self.report_orders(sell_orders, "sell orders")
        self.report_orders(buy_orders, " buy orders")
        for resource_type in Resource:
            filtered_sells = [(ent, o) for ent, o in sell_orders if o.resource == resource_type]
            filtered_buys = [(ent, o) for ent, o in buy_orders if o.resource == resource_type]
            if len(filtered_buys) == 0 and len(filtered_sells) == 0:
                continue
            log.debug(f"Processing orders for {resource_type}")
            self.report_orders(filtered_sells, "sell orders")
            self.report_orders(filtered_buys, " buy orders")
            eligible_sell, eligible_buy = self.eligible_orders(filtered_sells, filtered_buys)
            while not order_pairs_are_valid(eligible_buy, eligible_sell):
                eligible_buy, eligible_sell = fix_orders(eligible_buy, eligible_sell)

            transactions = self.process_orders(eligible_buy, eligible_sell)
            globals.stats_history.register_day_transactions(
                globals.star_date,
                resource_type,
                all_buy=filtered_buys,
                all_sell=filtered_sells,
                fulfilled_buy=eligible_buy,
                fulfilled_sell=eligible_sell,
                transactions=transactions,
            )

    @icontract.require(lambda buy_order, sell_order: buy_order.price >= sell_order.price)
    @icontract.ensure(lambda result, buy_order, sell_order: abs(2 * result.creds - (buy_order.price + sell_order.price).creds) <= 1)
    @icontract.ensure(lambda buy_order, sell_order: buy_order.status == OrderStatus.BOUGHT and sell_order.status == OrderStatus.SOLD)
    def process_transaction(self, buy_order: BuyOrder, sell_order: SellOrder) -> Money:
        if buy_order.price < sell_order.price:
            raise Exception("Attempted to buy at lower price then seller wanted")
        transaction_price, _ = (buy_order.price + sell_order.price).split()
        self.world.component_for_entity(sell_order.owner, Wallet).money += transaction_price
        self.world.component_for_entity(sell_order.owner, Wallet).register_transaction(sell_order.resource, transaction_price, OrderStatus.SOLD)
        # buyer gets a refund from what he payed upfront when creating order
        self.world.component_for_entity(buy_order.owner, Wallet).money += buy_order.price - transaction_price
        self.world.component_for_entity(buy_order.owner, Wallet).register_transaction(sell_order.resource, transaction_price, OrderStatus.BOUGHT)
        self.world.component_for_entity(buy_order.owner, Storage).add_one_of(sell_order.resource)
        # Orders are deleted in cleanup phase
        sell_order.status = OrderStatus.SOLD
        buy_order.status = OrderStatus.BOUGHT

        log.debug(f"{buy_order} and {sell_order} fulfilled for {transaction_price}. Buyer got a return of {buy_order.price - transaction_price}")

        return transaction_price

    def process_orders(self, buy_orders, sell_orders) -> List[Money]:
        if len(sell_orders) < len(buy_orders):
            self.report_orders(sell_orders, "chosen sell")
            self.report_orders(buy_orders[len(buy_orders) - len(sell_orders) :], " chosen buy")
        else:
            self.report_orders(sell_orders[: len(buy_orders)], "chosen sell")
            self.report_orders(buy_orders, " chosen buy")

        transactions = []

        for buy, sell in self.create_order_pairs(buy_orders, sell_orders):
            _, buy_order = buy
            _, sell_order = sell
            transaction_price = self.process_transaction(buy_order, sell_order)
            if transaction_price is not None:
                transactions.append(transaction_price)

        return transactions

    def report_orders(self, orders, name):
        if len(orders) > 0:
            mean = statistics.mean([order.price.creds for ent, order in orders])
            prices = ", ".join([f"{p}" for p in sorted([order.price for ent, order in orders])])
            log.debug(f"{name}: {prices} (mean: {mean:.2f})")
        else:
            log.debug(f"{name}: None")

    def eligible_orders(self, sell_orders, buy_orders):
        if len(buy_orders) == 0 or len(sell_orders) == 0:
            return [], []
        max_buy = max(buy_orders, key=lambda x: x[1].price)[1].price
        min_sell = min(sell_orders, key=lambda x: x[1].price)[1].price
        return sorted([(ent, o) for ent, o in sell_orders if o.price <= max_buy], key=lambda x: x[1].price), sorted(
            [(ent, o) for ent, o in buy_orders if o.price >= min_sell], key=lambda x: x[1].price
        )
