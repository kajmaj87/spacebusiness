import statistics
from collections import defaultdict, namedtuple
from random import random
from typing import Dict, Tuple, List, Union

import icontract
from sortedcontainers import SortedList  # type: ignore
from enum import Enum


class OrderType(Enum):
    BUY = 0
    SELL = 1
    TRANSACTION = 2

    def __str__(self):
        return f"{self.name}"


class Resource(Enum):
    NOTHING = -1
    MAN_DAY = 0
    FOOD = 1
    LUXURY = 2
    WATER = 3
    SOUL = 4
    EMBRYO = 5
    GROWN_HUMAN = 6

    def __str__(self):
        return f"{self.name}"


class OrderStatus(Enum):
    UNPROCESSED = -2
    BOUGHT = -1
    SOLD = 0
    CANCELLED = 1

    def __str__(self):
        return f"{self.name}"


class ResourcePile:
    def __init__(self, resource_type: Resource, amount_needed: float = 1):
        self.resource_type = resource_type
        self.amount = amount_needed

    def __str__(self):
        return f"{self.amount} {self.resource_type}"

    def is_nothing(self):
        return self.amount == 0 or self.resource_type == Resource.NOTHING


class Details:
    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f"{self.name}"

    def __repr__(self):
        return f"Details:{self.name}"


class Storage:
    def __init__(self):
        self.stored_resources = defaultdict(int)
        self.limit = dict()

    def __str__(self):
        contents = []
        for type, amount in self.stored_resources.items():
            if amount > 0:
                limit = f"/{self.limit[type]:.2f}" if type in self.limit else ""
                contents.append(f"{type}: {amount:.2f}{limit}")
        if len(contents) > 0:
            return f"Storage: {', '.join(contents)}"
        else:
            return "Storage: EMPTY"

    def amount(self, resource_type):
        return self.stored_resources[resource_type]

    def add(self, pile: ResourcePile):
        if self.will_fit(pile):
            self.stored_resources[pile.resource_type] += pile.amount
        else:
            raise Exception(f"Attempted to overfill storage with {pile}")

    def add_one_of(self, resource: Resource):
        if self.will_fit_one_of(resource):
            self.stored_resources[resource] += 1
        else:
            raise Exception(f"Attempted to overfill storage with {resource}")

    def add_all(self, storage: "Storage"):
        for resource in storage.stored_resources:
            self.add(ResourcePile(resource, storage.stored_resources[resource]))

    def set_limit(self, pile: ResourcePile):
        self.limit[pile.resource_type] = pile.amount

    def will_fit(self, pile: ResourcePile):
        type = pile.resource_type
        return type not in self.limit or self.amount(type) + pile.amount <= self.limit[type]

    def will_fit_one_of(self, resource: Resource):
        return resource not in self.limit or self.amount(resource) + 1 <= self.limit[resource]

    def remove(self, pile: ResourcePile):
        if self.has_at_least(pile):
            self.stored_resources[pile.resource_type] -= pile.amount
        else:
            raise Exception(f"Attempted to remove more resources then there were available for {pile})")

    def remove_one_of(self, pile: ResourcePile):
        if self.has_one_of(pile):
            self.stored_resources[pile.resource_type] -= 1
        else:
            raise Exception(f"Attempted to remove more resources then there were available for {pile})")

    def has_at_least(self, pile: ResourcePile):
        return self.amount(pile.resource_type) >= pile.amount

    def has_one_of(self, pile: ResourcePile):
        return self.amount(pile.resource_type) >= 1

    def has_one(self, resource: Resource):
        return self.amount(resource) >= 1


@icontract.invariant(lambda self: self.creds >= 0, "Money cannot become negative")
class Money:
    def __init__(self, creds: int):
        if not isinstance(creds, int):
            raise TypeError(f"Expected {int} but got {type(creds)}")

        self.creds = creds

    def __str__(self):
        return f"{self.creds}cr"

    def __repr__(self):
        return f"{self.creds}"

    def __lt__(self, other):
        return self.creds < other.creds

    def __le__(self, other):
        return self.creds <= other.creds

    def __gt__(self, other):
        return self.creds > other.creds

    def __eq__(self, other):
        return self.creds == other.creds

    def __int__(self):
        return self.creds

    def __add__(self, other: "Money") -> "Money":
        return Money(self.creds + other.creds)

    def __sub__(self, other: "Money") -> "Money":
        return Money(self.creds - other.creds)

    def multiply(self, multiplier: float) -> "Money":
        return Money(int(self.creds * multiplier))

    def split(self) -> Tuple["Money", "Money"]:
        result = (Money(self.creds // 2 + self.creds % 2), Money(self.creds // 2))
        assert result[0].creds + result[1].creds == self.creds
        # give last penny out randomly
        if random() < 0.5:
            return result
        else:
            return result[1], result[0]

    def remove(self, money: "Money") -> "Money":
        if not isinstance(money, Money):
            raise TypeError(f"Expected {Money} but got {type(money)}")
        else:
            return Money(self.creds - money.creds)


class Wallet:
    def __init__(self, money: Money):
        if not isinstance(money, Money):
            raise TypeError(f"Expected {Money} but got {type(money)}")
        self.money = money
        self.last_transaction: Dict[Resource, Tuple[Money, OrderStatus]] = dict()

    @icontract.require(lambda status: status != OrderStatus.UNPROCESSED)
    def register_transaction(self, resource_type: Resource, price: Money, status: OrderStatus):
        if not isinstance(price, Money):
            raise TypeError(f"Expected {Money} but got {type(price)}")
        self.last_transaction[resource_type] = (price, status)

    @icontract.require(lambda order: order.status != OrderStatus.UNPROCESSED)
    def register_order(self, order: Union["BuyOrder", "SellOrder"]):
        self.last_transaction[order.resource] = (order.price, order.status)

    def last_transaction_details_for(self, resource_type: Resource):
        return self.last_transaction[resource_type] if resource_type in self.last_transaction else (None, None)


class Consumer:
    def __init__(self, pile: ResourcePile = None):
        self.needs = []
        if pile is not None:
            self.needs.append(pile)

    def add_need(self, need: ResourcePile):
        self.needs.append(need)


# marker interfaces
class Hunger:
    pass


class Terminated:
    pass


class InheritancePool:
    pass


class Producer:
    def __init__(self, needs: ResourcePile, gives: ResourcePile):
        self.needs = needs
        self.gives = gives

    def needed_pile(self):
        return self.needs

    def created_pile(self):
        return self.gives


class Need:
    def __init__(self, name, priority, pile: ResourcePile, price_change_on_buy, price_change_on_failed_buy):
        self.name = name
        self.priority = priority
        self.pile = pile
        self.price_change_on_buy = price_change_on_buy
        self.price_change_on_failed_buy = price_change_on_failed_buy

    def is_fullfilled(self, storage):
        return storage.has_at_least(self.pile)

    def resource_type(self):
        return self.pile.resource_type


class Needs:
    def __init__(self):
        self.needs = SortedList(key=lambda x: x.priority)

    def add(self, need: Need):
        self.needs.add(need)

    def __iter__(self):
        return self.needs.__iter__()


class SellOrder:
    def __init__(self, owner, resource: Resource, price: Money, status: OrderStatus = OrderStatus.UNPROCESSED):
        if not isinstance(price, Money):
            raise TypeError(f"Expected {Money} but got {type(price)}")
        self.owner = owner
        self.resource = resource
        self.price = price
        self.status = status

    def __str__(self):
        return f"SellOrder: {self.resource} for at least {self.price}"

    def __repr__(self):
        return f"Sell: {self.resource} for {self.price}"


class BuyOrder:
    def __init__(self, owner, resource: Resource, price: Money, status: OrderStatus = OrderStatus.UNPROCESSED):
        if not isinstance(price, Money):
            raise TypeError(f"Expected {Money} but got {type(price)}")
        self.owner = owner
        self.resource = resource
        self.price = price
        self.status = status

    def __str__(self):
        return f"BuyOrder: {self.resource} for {self.price} at maximum"

    def __repr__(self):
        return f"Buy: {self.resource} for {self.price}"


Stat = namedtuple("Stat", ["resource", "order_type", "length", "min", "median", "max"])


class StarDate:
    START_YEAR = 2200
    TURNS_IN_YEAR = 50

    def __init__(self, time=0):
        self.time = time

    def increase(self):
        self.time += 1

    def yesterday(self):
        return StarDate(self.time - 1)

    def __str__(self):
        return f"SD {self.START_YEAR + self.time // self.TURNS_IN_YEAR}.{self.time % self.TURNS_IN_YEAR}"


class StatsHistory:
    def __init__(self):
        self.history = {}

    def register_day_transactions(
        self,
        date: StarDate,
        resource: Resource,
        all_buy,
        all_sell,
        fulfilled_buy,
        fulfilled_sell,
        transactions: List[Money],
    ):
        self.history[(date.time, resource)] = StatsForDay(date, resource, all_buy, all_sell, fulfilled_buy, fulfilled_sell, transactions)

    def stats_for_day(self, date: StarDate, resource: Resource):
        return self.history[(date.time, resource)]

    def has_stats_for_day(self, date: StarDate, resource: Resource):
        return (date.time, resource) in self.history


class StatsForDay:
    def __init__(
        self,
        date: StarDate,
        resource: Resource,
        all_buy,
        all_sell,
        fulfilled_buy,
        fulfilled_sell,
        transactions: List[Money],
    ):
        self.fulfilled_sell = self.calculate_base_stats(resource, OrderType.SELL, fulfilled_sell)
        self.fulfilled_buy = self.calculate_base_stats(resource, OrderType.BUY, fulfilled_buy)
        self.transactions = self.calculate_stats_for_prices(resource, OrderType.TRANSACTION, transactions)
        self.date = date

        self.sell_stats = self.calculate_base_stats(resource, OrderType.SELL, all_sell)
        self.buy_stats = self.calculate_base_stats(resource, OrderType.BUY, all_buy)
        self.resource = resource
        self.total = self.buy_stats.length + self.sell_stats.length

    def __str__(self):
        buy, sell, transactions = "", "", ""
        if self.transactions.length > 0:
            transactions = f"T:{self.transactions.min}/{self.transactions.median}/{self.transactions.max}"
        if self.buy_stats.length > 0:
            buy = f"B:{self.buy_stats.min}/{self.buy_stats.max}"
        if self.sell_stats.length > 0:
            sell = f"S:{self.sell_stats.min}/{self.sell_stats.max}"
        return f"{self.resource} #B {self.buy_stats.length} #S {self.sell_stats.length} #T {self.transactions.length} {buy} {transactions} {sell}"

    def as_csv(self):
        if self.transactions.length > 0:
            transactions = f"{self.transactions.min!r},{self.transactions.median!r},{self.transactions.max!r}"
        else:
            transactions = ",,"
        return f"{self.date},{self.resource},{self.buy_stats.length},{self.sell_stats.length},{self.transactions.length},{transactions}"

    def calculate_stats_for_prices(self, resource: Resource, order_type: OrderType, prices: List[Money]) -> Stat:
        if len(prices) > 0:
            median = Money(statistics.median_low([p.creds for p in prices]))
            return Stat(
                resource=resource,
                order_type=order_type,
                length=len(prices),
                min=min(prices),
                median=median,
                max=max(prices),
            )
        else:
            return Stat(resource=resource, order_type=order_type, length=len(prices), min=None, median=None, max=None)

    def calculate_base_stats(self, resource: Resource, order_type: OrderType, orders):
        prices = [o.price for ent, o in orders]
        return self.calculate_stats_for_prices(resource, order_type, prices)
