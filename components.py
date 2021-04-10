from collections import defaultdict
from sortedcontainers import SortedList
from enum import Enum


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

    def set_limit(self, pile: ResourcePile):
        self.limit[pile.resource_type] = pile.amount

    def will_fit(self, pile: ResourcePile):
        type = pile.resource_type
        return type not in self.limit or self.amount(type) + pile.amount <= self.limit[type]

    def remove(self, pile: ResourcePile):
        if self.has_at_least(pile):
            self.stored_resources[pile.resource_type] -= pile.amount
        else:
            raise Exception(f"Attempted to remove more resources then there were available for {pile})")

    def has_at_least(self, pile: ResourcePile):
        return self.amount(pile.resource_type) >= pile.amount


class Wallet:
    def __init__(self, money):
        self.money = money
        self.last_transaction = dict()

    def register_transaction(self, resource_type: Resource, price, status: OrderStatus):
        self.last_transaction[resource_type] = (price, status)

    def last_transaction_details_for(self, resource_type: Resource):
        return self.last_transaction[resource_type] if resource_type in self.last_transaction else (None, None)


class Consumer:
    def __init__(self, needs: ResourcePile):
        self.needs = needs

    def needed_pile(self):
        return self.needs


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
    def __init__(self, owner, pile: ResourcePile, price: float):
        self.owner = owner
        self.pile = pile
        self.price = price

    def __str__(self):
        return f"SellOrder: {self.pile} for at least {self.price:.2f}cr"

    def __repr__(self):
        return f"Sell: {self.pile} for {self.price:.2f}cr"


class BuyOrder:
    def __init__(self, owner, pile: ResourcePile, price: float):
        self.owner = owner
        self.pile = pile
        self.price = price

    def __str__(self):
        return f"BuyOrder: {self.pile} for {self.price:.2f}cr at maximum"

    def __repr__(self):
        return f"Buy: {self.pile} for {self.price:.2f}cr"
