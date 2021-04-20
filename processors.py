from random import random

import esper
import statistics

from components import Storage, Consumer, Details, Producer, SellOrder, ResourcePile, BuyOrder, Wallet, Resource, \
    Needs, OrderStatus, Need
from transaction_logger import Ticker
import globals


class Timeflow(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        globals.star_date.increase()
        print(f"It is now {globals.star_date}")


class Consumption(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        def consume_if_possible(storage: Storage, pile: ResourcePile):
            if storage.has_at_least(pile):
                storage.remove(pile)
                print(f"Removed {pile} from {details.name}")
            else:
                print(f"Consumer {details.name} did not have {pile}")

        print("\nConsumption Phase started.")
        consumers = self.world.get_components(Details, Storage, Consumer)
        for ent, (details, storage, consumer) in consumers:
            for need in consumer.needs:
                consume_if_possible(storage, need)


class Production(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print(f"\nProduction Phase started")
        producers = self.world.get_components(Details, Storage, Producer)
        for ent, (details, storage, producer) in producers:
            while storage.has_at_least(producer.needed_pile()) and storage.will_fit(producer.created_pile()):
                storage.remove(producer.needed_pile())
                storage.add(producer.created_pile())
                print(f"Producer {details.name} produced {producer.created_pile()}")
            if not storage.will_fit(producer.created_pile()):
                print(f"Producer {details.name} did not have place to hold {producer.created_pile()}")
            if not storage.has_at_least(producer.needed_pile()):
                print(f"Producer {details.name} did not have {producer.needed_pile()} to start production")


class Ordering(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nOrdering Phase started")
        self.create_sell_orders()
        self.create_buy_orders()

    def decide_order_price_for_needs(self, details: Details, need: Need, wallet: Wallet):
        last_price, status = wallet.last_transaction_details_for(need.resource_type())
        if status is None:
            bid_price = random() * 0.2 * wallet.money
            print(f"{details.name} knows nothing about prices of {need.resource_type()}. Guessing: {bid_price:.2f}cr")
        else:
            if status == OrderStatus.BOUGHT:
                bid_price = last_price * need.price_change_on_buy
                print(
                    f"{details.name} bought {need.resource_type()} for {last_price:.2f}cr. Will try to order for {bid_price:.2f}cr")
            elif status == OrderStatus.FAILED:
                if globals.stats_history.has_stats_for_day(globals.star_date.yesterday(), need.resource_type()):
                    yesterday_stats = globals.stats_history.stats_for_day(globals.star_date.yesterday(), need.resource_type())
                    median = yesterday_stats.sell_stats.median
                    bid_price = last_price + (median - last_price)/2 if median is not None else last_price

                print(
                    f"{details.name} failed to buy {need.resource_type()} for {last_price:.2f}cr. Will try to order for {bid_price:.2f}cr")
            else:
                raise Exception(f"Unexpected transaction status: {status}")
        return bid_price

    def create_buy_orders(self):
        def decide_to_place_buy_order(owner, resouce: Resource, wallet: Wallet, max_bid_price: float):
            if resouce == Resource.NOTHING:
                print(f"{details.name} won't buy nothing so not placing an order")
            elif not storage.will_fit_one_of(resouce):
                print(f"{details.name} did not order {resouce} (no storage space left)")
            else:
                if 0 < wallet.money < max_bid_price:
                    print(
                        f"{details.name} did not affort {max_bid_price:.2f}cr to order {resouce}. Has only {wallet.money:.2f}cr left. Will bid for this amount instead")
                bid = min(max_bid_price, wallet.money)
                if wallet.money > 0:
                    wallet.money -= bid
                    buy_order = create_buy_order(owner, resouce, bid)
                    print(f"{details.name} created a {buy_order}")
                else:
                    print(f"{details.name} has no money left to create orders")

        def create_buy_order(owner, resource: Resource, max_bid_price: float):
            buy_order_ent = self.world.create_entity()
            buy_order = BuyOrder(owner, resource, max_bid_price)
            self.world.add_component(buy_order_ent, buy_order)
            return buy_order

        needers = self.world.get_components(Details, Storage, Needs, Wallet)
        for ent, (details, storage, needs, wallet) in needers:
            for need in needs:
                if not need.is_fullfilled(storage):
                    print(f"{details.name} wants to {need.name}")
                    bid_price = self.decide_order_price_for_needs(details, need, wallet)
                    decide_to_place_buy_order(ent, need.pile.resource_type, wallet, bid_price)

    def decide_order_price_for_sell(self, details, resource_type, wallet):
        last_price, status = wallet.last_transaction_details_for(resource_type)
        if status is None:
            bid_price = random() * 2 + 0.5
            print(f"{details.name} knows nothing about prices of {resource_type}. Guessing: {bid_price:.2f}cr")
        else:
            if status == OrderStatus.SOLD:
                # TODO Should be handled more in a way as needs are
                bid_price = last_price * 1.1
                print(
                    f"{details.name} sold {resource_type} for {last_price:.2f}cr. Will try to sell for {bid_price:.2f}cr")
            elif status == OrderStatus.FAILED:
                bid_price = last_price * 0.9
                print(
                    f"{details.name} failed to sell {resource_type} for {last_price:.2f}cr. Will try to sell for {bid_price:.2f}cr")
            else:
                raise Exception(f"Unexpected transaction status: {status}")
        return max(bid_price,
                   0.01)  # TODO make it more sensible, wallet should take all transactions from last turn into account

    def create_sell_orders(self):
        def create_sell_order(owner, resource: Resource, min_bid_price: float):
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
                print(f"{details.name} created a {sell_order}")
            print(f"{details.name} won't sell {producer.created_pile().resource_type} as it does not have enough of it")


class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def create_order_pairs(self, buy_orders, sell_orders):
        if len(sell_orders) < len(buy_orders):
            order_pairs = zip(buy_orders[len(buy_orders) - len(sell_orders):], sell_orders)
        else:
            order_pairs = zip(buy_orders, sell_orders[:len(buy_orders)])
        return order_pairs

    def process(self):
        def order_pairs_are_valid(buy_orders, sell_orders):
            for buy, sell in self.create_order_pairs(buy_orders, sell_orders):
                _, buy_order = buy
                _, sell_order = sell
                if buy_order.price < sell_order.price:
                    print(f"Order Pair: {buy_order} / {sell_order} is invalid.")
                    return False
            return True

        def fix_orders(buy, sell):
            print("Fixing orders")
            return buy[1:], sell

        print("\nExchange Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        self.report_orders(sell_orders, "sell orders")
        self.report_orders(buy_orders, " buy orders")
        for resource_type in Resource:
            filtered_sells = [(ent, o) for ent, o in sell_orders if o.resource == resource_type]
            filtered_buys = [(ent, o) for ent, o in buy_orders if o.resource == resource_type]
            if len(filtered_buys) == 0 and len(filtered_sells) == 0:
                continue
            print(f"Processing orders for {resource_type}")
            self.report_orders(filtered_sells, "sell orders")
            self.report_orders(filtered_buys, " buy orders")
            eligible_sell, eligible_buy = self.eligible_orders(filtered_sells, filtered_buys)
            while not order_pairs_are_valid(eligible_buy, eligible_sell):
                eligible_buy, eligible_sell = fix_orders(eligible_buy, eligible_sell)

            transactions = self.process_orders(eligible_buy, eligible_sell)
            globals.stats_history.register_day_transactions(globals.star_date, resource_type, all_buy=filtered_buys,
                                                            all_sell=filtered_sells, fulfilled_buy=eligible_buy,
                                                            fulfilled_sell=eligible_sell, transactions=transactions)

    def process_orders(self, buy_orders, sell_orders):
        if len(sell_orders) < len(buy_orders):
            self.report_orders(sell_orders, "chosen sell")
            self.report_orders(buy_orders[len(buy_orders) - len(sell_orders):], " chosen buy")
        else:
            self.report_orders(sell_orders[:len(buy_orders)], "chosen sell")
            self.report_orders(buy_orders, " chosen buy")

        transactions = []

        for buy, sell in self.create_order_pairs(buy_orders, sell_orders):
            buy_ent, buy_order = buy
            sell_ent, sell_order = sell
            if buy_order.price < sell_order.price:
                raise Exception(f"Attempted to buy at lower price then seller wanted")
            gain_resource_pile_from_order(self.world, buy_ent, buy_order, sell_order)
            transaction_price = gain_money_from_order(self.world, sell_ent, sell_order, buy_order)
            if transaction_price is not None:
                transactions.append(transaction_price)

        return transactions

    def report_orders(self, orders, name):
        if len(orders) > 0:
            mean = statistics.mean([order.price for ent, order in orders])
            prices = ", ".join([f"{p:0.2f}" for p in sorted([order.price for ent, order in orders])])
            print(f"{name}: {prices} (mean: {mean:.2f})")
        else:
            print(f"{name}: None")

    def eligible_orders(self, sell_orders, buy_orders):
        if len(buy_orders) == 0 or len(sell_orders) == 0:
            return [], []
        max_buy = max(buy_orders, key=lambda x: x[1].price)[1].price
        min_sell = min(sell_orders, key=lambda x: x[1].price)[1].price
        return sorted(
            [(ent, o) for ent, o in sell_orders if o.price <= max_buy],
            key=lambda x: x[1].price), sorted(
            [(ent, o) for ent, o in buy_orders if o.price >= min_sell],
            key=lambda x: x[1].price)


def register_transaction(world, order, status: OrderStatus, transaction_price = None):
    wallet = world.component_for_entity(order.owner, Wallet)
    if transaction_price is not None:
        wallet.register_transaction(order.resource, transaction_price, status)
    else:
        wallet.register_transaction(order.resource, order.price, status)


def gain_resource_pile_from_order(world, order_ent, order, new_order):
    owner_name = world.component_for_entity(order.owner, Details).name
    owner_storage = world.component_for_entity(order.owner, Storage)
    owner_storage.add_one_of(order.resource)
    world.delete_entity(order_ent)
    if new_order != order.owner:
        new_owner_name = world.component_for_entity(new_order.owner, Details).name
        #print(f"{owner_name} gained {order.resource} from {new_owner_name}")
        half_price_diff = (new_order.price - order.price) / 2
        register_transaction(world, new_order, OrderStatus.BOUGHT, order.price + half_price_diff)
    else:
        #print(f"{owner_name} gained {order.resource} back as the order for {order.price:.2f}cr was cancelled")
        register_transaction(world, order, OrderStatus.FAILED)


def gain_money_from_order(world, order_ent, order, new_order):
    owner_name = world.component_for_entity(order.owner, Details).name
    world.component_for_entity(order.owner, Wallet).money += order.price
    half_price_diff = (new_order.price - order.price) / 2
    # both get half of the price difference, the buyer already payed more in advance so he gets a refund
    world.component_for_entity(order.owner, Wallet).money += half_price_diff
    world.component_for_entity(new_order.owner, Wallet).money += half_price_diff
    world.delete_entity(order_ent)
    if new_order != order:
        new_owner_name = world.component_for_entity(new_order.owner, Details).name
        #print(f"{owner_name} gained {order.price:.2f}cr + {half_price_diff:.2f}cr from {new_owner_name}")
        register_transaction(world, order, OrderStatus.SOLD, order.price + half_price_diff)
        return order.price + half_price_diff
    else:
        #print(f"{owner_name} gained {order.price:.2f}cr back as the order for {order.resource} was cancelled")
        register_transaction(world, order, OrderStatus.FAILED)
        return None


class OrderCancellation(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        self.world._clear_dead_entities()
        print("\nOrder Cancellation Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        print(f"Locks will be released for {len(sell_orders)} sell and {len(buy_orders)} buy orders still on market")
        for ent, buy_order in buy_orders:
            # we return money back as the order didn't happen
            gain_money_from_order(self.world, ent, buy_order, buy_order)

        for ent, sell_order in sell_orders:
            # we return resources back as the order didn't happen
            gain_resource_pile_from_order(self.world, ent, sell_order, sell_order.owner)


class StatisticsUpdate(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        pass


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.ticker = Ticker()

    def process(self):
        wallets = self.world.get_components(Details, Storage, Wallet)
        total_money = sum([w.money for ent, (d, s, w) in wallets])
        for ent, (details, storage, wallets) in wallets:
            # print(f"{details.name} has {wallets.money:.2f}cr left. Storage: {storage}")
            pass

        print(f"\n\nTotal money: {total_money:.2f}cr.")
        print(f"Prices in {globals.star_date}:")
        for resource in Resource:
            if globals.stats_history.has_stats_for_day(globals.star_date, resource):
                print(globals.stats_history.stats_for_day(globals.star_date, resource))
            self.ticker.log_transactions(resource)

        print("Richest entities:")
        for ent, (details, storage, wallets) in sorted(self.world.get_components(Details, Storage, Wallet), key=lambda x: -x[1][2].money)[0:5]:
            print(f"{details.name} has {wallets.money:.2f}cr left. Storage: {storage}")

