from random import random, choice, randint
from typing import Tuple, Union, List
from log import log

import esper  # type: ignore
import statistics

import icontract as icontract

from components import Storage, Consumer, Details, Producer, SellOrder, ResourcePile, BuyOrder, Wallet, Resource, \
    Needs, OrderStatus, Need, Money, Hunger, InheritancePool, Terminated
from entities import create_person
from transaction_logger import Ticker
import globals


class Timeflow(esper.Processor):
    def __init__(self):
        super().__init__()
        self.total_money_at_start = None

    def process(self):
        globals.star_date.increase()
        log.info(f"It is now {globals.star_date}. Total money: {total_money_in_wallets(self.world)}")
        if self.total_money_at_start is None:
            self.total_money_at_start = total_money_in_wallets(self.world)
        if self.total_money_at_start.creds != total_money_in_wallets(self.world).creds:
            raise Exception(
                f"Total money changed from {self.total_money_at_start} to {total_money_in_wallets(self.world)}. (diff {self.total_money_at_start.creds - total_money_in_wallets(self.world).creds}cr)")


class Consumption(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        def consume_if_possible(ent, storage: Storage, pile: ResourcePile):
            if storage.has_at_least(pile):
                storage.remove(pile)
                log.debug(f"Removed {pile} from {details.name}")
            else:
                log.debug(f"Consumer {details.name} did not have {pile} and will suffer consequences")
                if pile.resource_type == Resource.FOOD:
                    self.world.add_component(ent, Hunger())

        log.debug("\nConsumption Phase started.")
        consumers = self.world.get_components(Details, Storage, Consumer)
        for ent, (details, storage, consumer) in consumers:
            for need in consumer.needs:
                consume_if_possible(ent, storage, need)


class Production(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        log.debug(f"\nProduction Phase started")
        producers = self.world.get_components(Details, Storage, Producer)
        for ent, (details, storage, producer) in producers:
            while storage.has_at_least(producer.needed_pile()) and storage.will_fit(producer.created_pile()):
                storage.remove(producer.needed_pile())
                storage.add(producer.created_pile())
                log.debug(f"Producer {details.name} produced {producer.created_pile()}")
            if not storage.will_fit(producer.created_pile()):
                log.debug(f"Producer {details.name} did not have place to hold {producer.created_pile()}")
            if not storage.has_at_least(producer.needed_pile()):
                log.debug(f"Producer {details.name} did not have {producer.needed_pile()} to start production")


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
                log.debug(
                    f"{details.name} bought {need.resource_type()} for {last_price}. Will try to order for {bid_price}")
            elif status == OrderStatus.CANCELLED:
                if globals.stats_history.has_stats_for_day(globals.star_date.yesterday(), need.resource_type()):
                    #yesterday_stats = globals.stats_history.stats_for_day(globals.star_date.yesterday(), need.resource_type())
                    #median = yesterday_stats.sell_stats.median
                    #bid_price = (median + last_price).split()[0] if median is not None else last_price
                    bid_price = max(last_price.multiply(need.price_change_on_failed_buy), last_price + Money(1))
                    log.debug( f"{details.name} failed to buy {need.resource_type()} for {last_price}. Will try to order for {bid_price}")
                else:
                    bid_price = last_price
                    log.debug(
                        f"{details.name} has no info about yesterday prices of {need.resource_type()}. Ordering for last price {last_price}")
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
                        f"{details.name} did not affort {max_bid_price} to order {resouce}. Has only {wallet.money} left. Will bid for this amount instead")
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
                log.debug(
                    f"{details.name} sold {resource_type} for {last_price}. Will try to sell for {bid_price}")
            elif status == OrderStatus.CANCELLED:
                bid_price = last_price.multiply(0.9)
                log.debug(
                    f"{details.name} failed to sell {resource_type} for {last_price}. Will try to sell for {bid_price}")
            else:
                raise Exception(f"Unexpected transaction status: {status}")
        return max(bid_price, Money(
            1))  # TODO make it more sensible, wallet should take all transactions from last turn into account

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


class Exchange(esper.Processor):
    def __init__(self):
        super().__init__()

    def create_order_pairs(self, buy_orders, sell_orders):
        if len(sell_orders) < len(buy_orders):
            order_pairs = zip(buy_orders[len(buy_orders) - len(sell_orders):], sell_orders)
        else:
            order_pairs = zip(buy_orders, sell_orders[:len(buy_orders)])
        return order_pairs

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(lambda OLD, self: total_money_locked_in_orders(self.world) + total_money_in_wallets(self.world) == total_money_locked_in_orders(OLD.self.world) + total_money_in_wallets(OLD.self.world))
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
            globals.stats_history.register_day_transactions(globals.star_date, resource_type, all_buy=filtered_buys,
                                                            all_sell=filtered_sells, fulfilled_buy=eligible_buy,
                                                            fulfilled_sell=eligible_sell, transactions=transactions)

    @icontract.require(lambda buy_order, sell_order: buy_order.price >= sell_order.price)
    @icontract.ensure(lambda result, buy_order, sell_order: abs(2*result.creds - (buy_order.price + sell_order.price).creds) <= 1)
    @icontract.ensure(
        lambda buy_order, sell_order: buy_order.status == OrderStatus.BOUGHT and sell_order.status == OrderStatus.SOLD)
    def process_transaction(self, buy_order: BuyOrder, sell_order: SellOrder) -> Money:
        if buy_order.price < sell_order.price:
            raise Exception(f"Attempted to buy at lower price then seller wanted")
        transaction_price, _ = (buy_order.price + sell_order.price).split()
        self.world.component_for_entity(sell_order.owner, Wallet).money += transaction_price
        self.world.component_for_entity(sell_order.owner, Wallet).register_transaction(sell_order.resource,
                                                                                       transaction_price,
                                                                                       OrderStatus.SOLD)
        # buyer gets a refund from what he payed upfront when creating order
        self.world.component_for_entity(buy_order.owner, Wallet).money += buy_order.price - transaction_price
        self.world.component_for_entity(buy_order.owner, Wallet).register_transaction(sell_order.resource,
                                                                                      transaction_price,
                                                                                      OrderStatus.BOUGHT)
        self.world.component_for_entity(buy_order.owner, Storage).add_one_of(sell_order.resource)
        # Orders are deleted in cleanup phase
        sell_order.status = OrderStatus.SOLD
        buy_order.status = OrderStatus.BOUGHT

        log.debug(f"{buy_order} and {sell_order} fulfilled for {transaction_price}. Buyer got a return of {buy_order.price - transaction_price}")

        return transaction_price

    def process_orders(self, buy_orders, sell_orders) -> List[Money]:
        if len(sell_orders) < len(buy_orders):
            self.report_orders(sell_orders, "chosen sell")
            self.report_orders(buy_orders[len(buy_orders) - len(sell_orders):], " chosen buy")
        else:
            self.report_orders(sell_orders[:len(buy_orders)], "chosen sell")
            self.report_orders(buy_orders, " chosen buy")

        transactions = []

        for buy, sell in self.create_order_pairs(buy_orders, sell_orders):
            _, buy_order = buy
            _, sell_order = sell
            transaction_price = self.process_transaction(buy_order, sell_order)
            if transaction_price is not None:
                transactions.append(transaction_price)

        print_total_money(self.world, "After orders where processed")
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
        return sorted(
            [(ent, o) for ent, o in sell_orders if o.price <= max_buy],
            key=lambda x: x[1].price), sorted(
            [(ent, o) for ent, o in buy_orders if o.price >= min_sell],
            key=lambda x: x[1].price)


class OrderCancellation(esper.Processor):
    def __init__(self):
        super().__init__()

    @icontract.require(lambda buy_order: buy_order.status == OrderStatus.UNPROCESSED)
    @icontract.ensure(lambda buy_order: buy_order.status == OrderStatus.CANCELLED)
    def cancel_buy_order(self, buy_order: BuyOrder):
        owner_name = self.world.component_for_entity(buy_order.owner, Details).name
        self.world.component_for_entity(buy_order.owner, Wallet).money += buy_order.price
        buy_order.status = OrderStatus.CANCELLED
        self.world.component_for_entity(buy_order.owner, Wallet).register_order(buy_order)
        #log.debug(f"{owner_name} gained {buy_order.price} back as the order for {buy_order.resource} was cancelled")

    @icontract.require(lambda sell_order: sell_order.status == OrderStatus.UNPROCESSED)
    @icontract.ensure(lambda sell_order: sell_order.status == OrderStatus.CANCELLED)
    def cancel_sell_order(self, sell_order: SellOrder):
        owner_name = self.world.component_for_entity(sell_order.owner, Details).name
        owner_storage = self.world.component_for_entity(sell_order.owner, Storage)
        owner_storage.add_one_of(sell_order.resource)
        sell_order.status = OrderStatus.CANCELLED
        self.world.component_for_entity(sell_order.owner, Wallet).register_order(sell_order)
        #log.debug(f"{owner_name} gained {sell_order.resource} back as the order for {sell_order.price} was cancelled")

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(lambda OLD, self: total_money_locked_in_orders(self.world) + total_money_in_wallets(self.world) == total_money_locked_in_orders(OLD.self.world) + total_money_in_wallets(OLD.self.world))
    def process(self):
        # self.world._clear_dead_entities()
        log.debug("\nOrder Cancellation Phase started.")
        print_total_money(self.world, "Before Cancellation")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        log.debug(f"Locks will be released for {len(sell_orders)} sell and {len(buy_orders)} buy orders still on market")
        for ent, buy_order in filter(lambda o: o[1].status == OrderStatus.UNPROCESSED, buy_orders):
            # we return money back as the order didn't happen
            self.cancel_buy_order(buy_order)

        for ent, sell_order in filter(lambda o: o[1].status == OrderStatus.UNPROCESSED, sell_orders):
            # we return resources back as the order didn't happen
            self.cancel_sell_order(sell_order)

        # mark all orders for deletion
        for ent, order in self.world.get_component(SellOrder):
            self.world.add_component(ent, Terminated())
        for ent, order in self.world.get_component(BuyOrder):
            self.world.add_component(ent, Terminated())

        print_total_money(self.world, "After Cancellation")

class Maturity(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (details, storage) in self.world.get_components(Details, Storage):
            if storage.has_one(Resource.GROWN_HUMAN):
                log.warning(f"{details.name} created a grown human!")
                storage.remove_one_of(ResourcePile(Resource.GROWN_HUMAN))
                # FIXME cloning center should also have bought this water
                # FIXME those values should be constant and same as for other people in the world
                create_person(self.world, f"Clone-{randint(0,10000)}", food_consumption=0.5, food_amount=5, water_amount=5, water_consumption=0.25, money=0)



class Death(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for _, (pool_storage, pool_wallet, _) in self.world.get_components(Storage, Wallet, InheritancePool):
            for ent, (details, storage, wallet, _) in self.world.get_components(Details, Storage, Wallet, Hunger):
                log.warning(f"{details.name} died of hunger")
                storage.add_one_of(Resource.SOUL)
                pool_storage.add_all(storage)
                pool_wallet.money += wallet.money
                self.world.add_component(ent, Terminated())
            log.debug(f"Inheritance pool contents: {pool_wallet.money} and {pool_storage}")

class InheritanceLottery(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for _, (pool_storage, pool_wallet, _) in self.world.get_components(Storage, Wallet, InheritancePool):
            if pool_wallet.money.creds > 0:
                winner, (details, storage, wallet) = choice(self.world.get_components(Details, Storage, Wallet))
                half, _ = pool_wallet.money.split()
                if not self.world.has_component(winner, Terminated):
                    log.debug(f"{details.name} won {half} at the inheritance lottery!")
                    wallet.money += half
                    pool_wallet.money -= half
                else:
                    log.debug(f"{details.name} won {half} at the inheritance lottery but was already dead!")
                log.debug(f"Inheritance pool contents: {pool_wallet.money} and {pool_storage}")

class WealthRedistribution(esper.Processor):
    def __init__(self, tax_rate: float = 0):
        super().__init__()
        self.tax_rate = tax_rate

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(lambda OLD, self: total_money_in_wallets(self.world) == total_money_in_wallets(OLD.self.world))
    def process(self):
        money_before_redistribution = total_money_in_wallets(self.world)
        money_for_redistribution = Money(0)
        total_wallets = len(self.world.get_component(Wallet))
        last_wallet = None
        for ent, wallet in self.world.get_component(Wallet):
            if not self.world.has_component(ent, Terminated):
                tax = wallet.money.multiply(self.tax_rate)
                money_for_redistribution += tax
                wallet.money -= tax
        ubi_value = money_for_redistribution.multiply(1/total_wallets)
        for ent, wallet in self.world.get_component(Wallet):
            if not self.world.has_component(ent, Terminated):
                money_for_redistribution -= ubi_value
                wallet.money += ubi_value
                last_wallet = wallet
        # last one gets whats left
        if last_wallet is not None:
            last_wallet.money += money_for_redistribution
        log.info(f"Ubi this round is: {ubi_value}")
        assert money_before_redistribution == total_money_in_wallets(self.world), f"Redistributing money should not change the amount of it: {money_before_redistribution} changed to {total_money_in_wallets(self.world)}"



class StatisticsUpdate(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        pass


def print_total_money(world, where):
    total_money = total_money_in_wallets(world)
    log.debug(f"Total money: {total_money}. ({where})")


def total_money_in_wallets(world) -> Money:
    wallets = world.get_component(Wallet)
    return Money(sum([w.money.creds for ent, w in wallets]))


def total_money_locked_in_orders(world) -> Money:
    buy_orders = world.get_component(BuyOrder)
    return Money(sum([o.price.creds for ent, o in buy_orders]))


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()
        self.ticker = Ticker()

    def process(self):
        print_total_money(self.world, "Turn end")
        log.info(f"Prices in {globals.star_date}:")
        for resource in Resource:
            if globals.stats_history.has_stats_for_day(globals.star_date, resource):
                log.info(globals.stats_history.stats_for_day(globals.star_date, resource))
            self.ticker.log_transactions(resource)

        log.info("Richest entities:")
        money_in_rich_pockets = Money(0)
        for ent, (details, storage, wallets) in sorted(self.world.get_components(Details, Storage, Wallet),
                                                       key=lambda x: -x[1][2].money.creds)[0:5]:
            log.info(f"{details.name} has {wallets.money} left. Storage: {storage}")
            money_in_rich_pockets += wallets.money
        log.info(f"Richest have {money_in_rich_pockets} accounting for {money_in_rich_pockets.creds/total_money_in_wallets(self.world).creds*100:.2f}% of total money")

class Cleanup(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, terminated in self.world.get_component(Terminated):
            self.world.delete_entity(ent)


