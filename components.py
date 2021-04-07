from collections import defaultdict
from enum import Enum


class Resource(Enum):
    NOTHING = -1
    MAN_DAY = 0
    FOOD = 1
    LUXURY = 2

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


class SellOrder:
    def __init__(self, owner, pile: ResourcePile, minimum_bid: float):
        self.owner = owner
        self.pile = pile
        self.minimum_bid = minimum_bid

    def __str__(self):
        return f"SellOrder: {self.pile} for at least {self.minimum_bid}cr"


class BuyOrder:
    def __init__(self, owner, pile: ResourcePile, maximum_bid: float):
        self.owner = owner
        self.pile = pile
        self.maximum_bid = maximum_bid

    def __str__(self):
        return f"BuyOrder: {self.pile} for {self.maximum_bid}cr at maximum"
