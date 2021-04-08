from random import random

import esper
import statistics

from components import Storage, Consumer, Details, Producer, SellOrder, ResourcePile, BuyOrder, Wallet


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        wallets = self.world.get_component(Wallet)
        total_money = sum([w.money for ent, w in wallets])
        print(f"Another turn has passed. Total money: {total_money}cr")


class Consumption(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nConsumption Phase started.")
        consumers = self.world.get_components(Details, Storage, Consumer)
        for ent, (details, storage, consumer) in consumers:
            if storage.has_at_least(consumer.needed_pile()):
                storage.remove(consumer.needed_pile())
                print(f"Removed {consumer.needed_pile()} from {details.name}")
            else:
                print(f"Consumer {details.name} did not have {consumer.needed_pile()}")


class Production(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print(f"\nProduction Phase started")
        producers = self.world.get_components(Details, Storage, Producer)
        for ent, (details, storage, producer) in producers:
            if not storage.has_at_least(producer.needed_pile()):
                print(f"Producer {details.name} did not have {producer.needed_pile()} to start production")
            elif not storage.will_fit(producer.created_pile()):
                print(f"Producer {details.name} did not have place to hold {producer.created_pile()}")
            else:
                storage.remove(producer.needed_pile())
                storage.add(producer.created_pile())
                print(f"Producer {details.name} produced {producer.created_pile()}")


class Ordering(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nOrdering Phase started")
        self.create_sell_orders()
        self.create_buy_orders()

    def create_buy_orders(self):
        def decide_to_place_buy_order(owner, pile: ResourcePile, wallet: Wallet, max_bid_price: float):
            if pile.is_nothing():
                print(f"{details.name} won't buy nothing so not placing an order")
            elif not storage.will_fit(pile):
                print(f"{details.name} did not order {pile} (no storage space left)")
            elif wallet.money < max_bid_price:
                print(
                    f"{details.name} did not affort {max_bid_price}cr to order {pile}. Has only {wallet.money}cr left")
            else:
                wallet.money -= max_bid_price
                buy_order = create_buy_order(owner, pile, max_bid_price)
                print(f"{details.name} created a {buy_order}")

        def create_buy_order(owner, pile: ResourcePile, max_bid_price: float):
            buy_order_ent = self.world.create_entity()
            buy_order = BuyOrder(owner, pile, max_bid_price)
            self.world.add_component(buy_order_ent, buy_order)
            return buy_order

        consumers = self.world.get_components(Details, Storage, Consumer, Wallet)
        for ent, (details, storage, consumer, wallet) in consumers:
            max_bid_price = random() * 10 + 2
            pile_to_buy = ResourcePile(consumer.needed_pile().resource_type, 1)
            decide_to_place_buy_order(ent, pile_to_buy, wallet, max_bid_price)

        producers = self.world.get_components(Details, Storage, Producer, Wallet)
        for ent, (details, storage, producer, wallet) in producers:
            max_bid_price = random() * 10 + 5
            pile_to_buy = ResourcePile(producer.needed_pile().resource_type, 1)
            decide_to_place_buy_order(ent, pile_to_buy, wallet, max_bid_price)

    def create_sell_orders(self):
        def create_sell_order(owner, pile: ResourcePile, min_bid_price: float):
            sell_order_ent = self.world.create_entity()
            sell_order = SellOrder(owner, pile, min_bid_price)
            self.world.add_component(sell_order_ent, sell_order)
            return sell_order

        producers = self.world.get_components(Details, Storage, Producer, Wallet)
        for ent, (details, storage, producer, wallet) in producers:
            if not storage.has_at_least(producer.created_pile()):
                print(f"{details.name} won't sell {producer.created_pile()} as it does not have enough of it")
            else:
                storage.remove(producer.created_pile())
                min_bid_price = random() * 10 + 5
                sell_order = create_sell_order(ent, producer.created_pile(), min_bid_price)
                print(f"{details.name} created a {sell_order}")

class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nExchange Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        eligible_sell, eligible_buy = self.eligible_orders(sell_orders, buy_orders)
        self.report_orders(sell_orders, "sell orders")
        self.report_orders(buy_orders, " buy orders")
        self.report_orders(eligible_sell, "eligible sell orders")
        self.report_orders(eligible_buy, " eligible buy orders")
        if len(eligible_sell) < len(eligible_buy):
            self.report_orders(eligible_sell, "chosen sell")
            self.report_orders(eligible_buy[:-len(eligible_sell)], " chosen buy")
            order_pairs = zip(eligible_buy[:-len(eligible_sell)], eligible_sell)
        else:
            self.report_orders(eligible_sell[:len(eligible_buy)], "chosen sell")
            self.report_orders(eligible_buy, " chosen buy")
            order_pairs = zip(eligible_buy, eligible_sell[:len(eligible_buy)])
        self.process_orders(order_pairs)

    def process_orders(self, order_pairs):
        #print(list(order_pairs))
        for buy, sell in order_pairs:
            buy_ent, buy_order = buy
            sell_ent, sell_order = sell
            gain_resource_pile_from_order(self.world, buy_ent, buy_order, sell_order.owner)
            gain_money_from_order(self.world, sell_ent, sell_order, buy_order)

    def report_orders(self, orders, name):
        if len(orders) > 0:
            mean = statistics.mean([order.price for ent, order in orders])
            prices = ", ".join([f"{p:0.2f}" for p in sorted([order.price for ent, order in orders])])
            print(f"{name}: {prices} (mean: {mean:.2f})")
        else:
            print(f"{name}: None")

    def eligible_orders(self, sell_orders, buy_orders):
        max_buy = max([o.price for ent, o in buy_orders])
        min_sell = min([o.price for ent, o in sell_orders])
        return sorted([(ent, o) for ent, o in sell_orders if o.price <= max_buy], key=lambda x: x[1].price), sorted(
            [(ent, o) for ent, o in buy_orders if o.price >= min_sell], key=lambda x: x[1].price)

def gain_resource_pile_from_order(world, order_ent, order, new_owner):
    owner_name = world.component_for_entity(order.owner, Details).name
    owner_storage = world.component_for_entity(order.owner, Storage)
    owner_storage.add(order.pile)
    world.delete_entity(order_ent)
    if new_owner != order.owner:
        new_owner_name = world.component_for_entity(new_owner, Details).name
        print(f"{new_owner_name} gained {order.pile} from {owner_name}")
    else:
        print(f"{owner_name} gained {order.pile} back as the order for {order.price:.2f}cr was cancelled")

def gain_money_from_order(world, order_ent, order, new_order):
    owner_name = world.component_for_entity(order.owner, Details).name
    world.component_for_entity(order.owner, Wallet).money += order.price
    half_price_diff = (new_order.price - order.price)/2
    # both get half of the price difference, the buyer already payed more in advance so he gets a refund
    world.component_for_entity(order.owner, Wallet).money += half_price_diff
    world.component_for_entity(new_order.owner, Wallet).money += half_price_diff
    world.delete_entity(order_ent)
    if new_order != order:
        new_owner_name = world.component_for_entity(new_order.owner, Details).name
        print(f"{new_owner_name} gained {order.price:.2f}cr + {half_price_diff:.2f}cr  from {owner_name}")
    else:
        print(f"{owner_name} gained {order.price:.2f}cr back as the order for {order.pile} was cancelled")


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
