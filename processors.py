from random import random

import esper
import statistics

from components import Storage, Consumer, Details, Producer, SellOrder, ResourcePile, BuyOrder, Wallet


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("Another turn has passed.")


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
            min_bid_price = random() * 10
            if not storage.has_at_least(producer.created_pile()):
                print(f"{details.name} won't sell {producer.created_pile()} as it does not have enough of it")
            else:
                storage.remove(producer.created_pile())
                sell_order = create_sell_order(ent, producer.created_pile(), min_bid_price)
                print(f"{details.name} created a {sell_order}")


class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nExchange Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        print(
            f"There are {len(sell_orders)} sell orders on market (mean price: {statistics.mean([order.price for ent, order in sell_orders])})")
        print(
            f"There are {len(buy_orders)} buy orders on market (mean price: {statistics.mean([order.price for ent, order in buy_orders])})")


class OrderCancellation(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("\nOrder Cancellation Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        print(
            f"Locks will be released for {len(sell_orders)} sell orders still on market (mean price: {statistics.mean([order.price for ent, order in sell_orders])})")
        print(
            f"Locks will be released for {len(buy_orders)} buy orders still on market (mean price: {statistics.mean([order.price for ent, order in buy_orders])})")
        for ent, buy_order in buy_orders:
            owner_name = self.world.component_for_entity(buy_order.owner, Details).name
            self.world.component_for_entity(buy_order.owner, Wallet).money += buy_order.price
            self.world.delete_entity(ent)
            print(f"Removed buy order for {owner_name}")

        for ent, sell_order in sell_orders:
            owner_name = self.world.component_for_entity(sell_order.owner, Details).name
            owner_storage = self.world.component_for_entity(sell_order.owner, Storage)
            owner_storage.add(sell_order.pile)
            self.world.delete_entity(ent)
            print(f"Removed sell order for {owner_name}")
