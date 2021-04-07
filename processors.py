from random import random

import esper

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
        print(f"Consumption starting.")
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
        print(f"Production starting")
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
        self.create_sell_orders()
        self.create_buy_orders()

    def create_buy_orders(self):
        def create_buy_order(owner, pile: ResourcePile, min_bid_price: float):
            buy_order_ent = self.world.create_entity()
            buy_order = BuyOrder(owner, pile, min_bid_price)
            self.world.add_component(buy_order_ent, buy_order)
            return buy_order

        producers = self.world.get_components(Details, Storage, Producer, Wallet)
        for ent, (details, storage, producer, wallet) in producers:
            min_bid_price = random()*10
            if producer.needed_pile().is_nothing():
                print(f"Producer {details.name} won't buy nothing so not placing an order")
            elif not storage.will_fit(producer.needed_pile()):
                print(f"Producer {details.name} did not order {producer.needed_pile()} (no storage space left)")
            elif wallet.money < min_bid_price:
                print(f"Producer {details.name} did not affort {min_bid_price}cr to order {producer.needed_pile()}. Has only {wallet.money}cr left")
            else:
                wallet.money -= min_bid_price
                buy_order = create_buy_order(ent, producer.needed_pile(), min_bid_price)
                print(f"Producer {details.name} created a {buy_order}")


    def create_sell_orders(self):
        pass


class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        pass
