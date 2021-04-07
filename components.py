from collections import defaultdict
from enum import Enum


class Resource(Enum):
    MAN_DAY = 0
    FOOD = 1
    LUXURY = 2


class ResourcePile:
    def __init__(self, resource_type: Resource, amount_needed: float):
        self.resource_type = resource_type
        self.amount = amount_needed

class Details:
    def __init__(self, name):
        self.name = name


class Storage:
    def __init__(self):
        self.stored_resources = defaultdict(float)

    def amount(self, resource_type):
        return self.stored_resources[resource_type]

    def add(self, resource_type, amount):
        self.stored_resources[resource_type] += amount

    def remove(self, resource_type, amount):
        if self.amount(resource_type) >= amount:
            self.stored_resources[resource_type] -= amount
        else:
            raise Exception(f"Attempted to remove more resources then there were available for {resource_type} (amount: {amount})")

class Consumer:
    def __init__(self, needs: ResourcePile):
        self.needs = needs

    def resource_type(self):
        return self.needs.resource_type

    def needed_amount(self):
        return self.needs.amount


class Producer:
    def __init__(self, needs: ResourcePile, gives: ResourcePile):
        self.needs = needs
        self.gives = gives
