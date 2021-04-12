import statistics
from collections import defaultdict, namedtuple
from sortedcontainers import SortedList
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

    def __str__(self):
        return f"{self.name}"

class OrderStatus(Enum):
    BOUGHT = -1
    SOLD = 0
    FAILED = 1

    def __str__(self):
        return f"{self.name}"


class ResourcePile:
    def __init__(self, resource_type: Resource, amount_needed: float = 0):
        self.resource_type = resource_type
        self.amount = amount_needed

    def __str__(self):
        return f"{self.amount} {self.resource_type}"

    def is_nothing(self):
        return self.amount == 0 or self.resource_type == Resource.NOTHING


class Details:
    def __init__(self, name):
        self.name = name


class Storage:
    def __init__(self):
        self.stored_resources = defaultdict(float)
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


class Wallet:
    def __init__(self, money):
        self.money = money
        self.last_transaction = dict()

    def register_transaction(self, resource_type: Resource, price, status: OrderStatus):
        self.last_transaction[resource_type] = (price, status)

    def last_transaction_details_for(self, resource_type: Resource):
        return self.last_transaction[resource_type] if resource_type in self.last_transaction else (None, None)


class Consumer:
    def __init__(self, pile: ResourcePile = None):
        self.needs = []
        if pile is not None:
            self.needs.append(pile)

    def add_need(self, need: ResourcePile):
        self.needs.append(need)


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
    def __init__(self, owner, resource: Resource, price: float):
        self.owner = owner
        self.resource = resource
        self.price = price

    def __str__(self):
        return f"SellOrder: {self.resource} for at least {self.price:.2f}cr"

    def __repr__(self):
        return f"Sell: {self.resource} for {self.price:.2f}cr"


class BuyOrder:
    def __init__(self, owner, resource: Resource, price: float):
        self.owner = owner
        self.resource = resource
        self.price = price

    def __str__(self):
        return f"BuyOrder: {self.resource} for {self.price:.2f}cr at maximum"

    def __repr__(self):
        return f"Buy: {self.resource} for {self.price:.2f}cr"


Stat = namedtuple('Stat', ['resource', 'order_type', 'length', 'min', 'median', 'max'])


class StarDate:

    START_YEAR = 2200
    TURNS_IN_YEAR = 50

    def __init__(self):
        self.time = 0

    def increase(self):
        self.time += 1

    def __str__(self):
        return f"SD {self.START_YEAR + self.time//self.TURNS_IN_YEAR}.{self.time % self.TURNS_IN_YEAR}"


class StatsHistory:
    def __init__(self):
        self.history = {}

    def register_day_transactions(self, date: StarDate, resource: Resource, all_buy, all_sell, fulfilled_buy, fulfilled_sell, transactions):
        self.history[(date, resource)] = StatsForDay(resource, all_buy, all_sell, fulfilled_buy, fulfilled_sell, transactions)

    def stats_for_day(self, date: StarDate, resource: Resource):
        return self.history[(date, resource)]

    def has_stats_for_day(self, date: StarDate, resource: Resource):
        return (date, resource) in self.history


class StatsForDay:
    def __init__(self, resource: Resource, all_buy, all_sell, fulfilled_buy, fulfilled_sell, transactions):
        self.fulfilled_sell = self.calculate_base_stats(resource, OrderType.SELL, fulfilled_sell)
        self.fulfilled_buy = self.calculate_base_stats(resource, OrderType.BUY, fulfilled_buy)
        self.transactions = self.calculate_stats_for_prices(resource, OrderType.TRANSACTION, transactions)

        self.sell_stats = self.calculate_base_stats(resource, OrderType.SELL, all_sell)
        self.buy_stats = self.calculate_base_stats(resource, OrderType.BUY, all_buy)
        self.resource = resource
        self.total = self.buy_stats.length + self.sell_stats.length

    def __str__(self):
        buy, sell, transactions= "", "", ""
        if self.transactions.length > 0:
           transactions = f"T:{self.transactions.min:.2f}/{self.transactions.median:.2f}/{self.transactions.max:.2f}"
        if self.buy_stats.length > 0:
            buy = f"B:{self.buy_stats.min:.2f}/{self.buy_stats.max:.2f}"
        if self.sell_stats.length > 0:
            sell = f"S:{self.sell_stats.min:.2f}/{self.sell_stats.max:.2f}"
        return f"{self.resource} #B {self.buy_stats.length} #S {self.sell_stats.length} #T {self.transactions.length} {buy} {transactions} {sell}"

    def calculate_stats_for_prices(self, resource: Resource, order_type: OrderType, prices):
        if len(prices) > 0:
            median = statistics.median(prices)
            return Stat(resource=resource, order_type=order_type, length=len(prices), min=min(prices), median=median, max=max(prices))
        else:
            return Stat(resource=resource, order_type=order_type, length=len(prices), min=None, median=None, max=None)

    def calculate_base_stats(self, resource: Resource, order_type: OrderType, orders):
        prices = [o.price for ent, o in orders]
        return self.calculate_stats_for_prices(resource, order_type, prices)
