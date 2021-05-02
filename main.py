from random import random

import esper  # type: ignore

from components import (
    Details,
    InheritancePool,
    Money,
    StarDate,
    StatsHistory,
    Storage,
    Wallet,
)
from entities import create_cloning_center, create_farm, create_person, create_well
from processors.cleanup import Cleanup
from processors.consumption import Consumption
from processors.death import Death
from processors.exchange import Exchange
from processors.inheritance import InheritanceLottery
from processors.maturity import Maturity
from processors.order_cancellation import OrderCancellation
from processors.ordering import Ordering
from processors.production import Production
from processors.summary import TurnSummaryProcessor
from processors.timeflow import Timeflow
from processors.wealth_redistribution import WealthRedistribution


def createManyEntities(world):
    for i in range(100):
        create_person(
            world,
            f"MAN-{i}",
            food_consumption=0.5,
            food_amount=int(random() * 10) + 2,
            water_amount=3,
            water_consumption=0.25,
            money=1000,
        )
    for i in range(60):
        create_farm(world, f"Farm-{i}", labour_consumption=1, food_production=2, food_storage=5, money=1500)
    for i in range(30):
        create_well(world, f"Well-{i}", labour_consumption=1, water_production=2, water_storage=5, money=1000)

    for i in range(3):
        create_cloning_center(world, f"Clone Center-{i}", 5, 5, 1500)


def createFewEntities(world):
    for name in ["Jacek", "Wacek", "Placek", "Gacek", "Macek", "Lacek", "Picek", "XXX", "YYY"]:
        create_person(
            world,
            f"{name}",
            food_consumption=0.5,
            food_amount=int(random() * 10),
            water_amount=3,
            water_consumption=0.25,
            money=1000,
        )
    for name in ["Folwark", "Kołko Rolnicze"]:
        create_farm(world, f"{name}", labour_consumption=1, food_production=1, food_storage=10, money=1500)
    for name in ["Mpwik", "Cisowianka"]:
        create_well(world, f"{name}", labour_consumption=1, water_production=10, water_storage=100, money=1000)

    create_cloning_center(world, "Clone Center", 5, 5, 1500)


def create2Entities(world):
    for name in ["Jacek"]:
        create_person(world, f"{name}", food_consumption=0.5, food_amount=10, water_amount=3, water_consumption=0.25, money=1000)
    for name in ["Folwark"]:
        create_farm(world, f"{name}", labour_consumption=1, food_production=1, food_storage=10, money=1500)

    create_cloning_center(world, "Clone Center", 5, 5, 1500)


def createGlobalEntities(world):
    globals = world.create_entity()
    world.add_component(globals, StarDate())
    world.add_component(globals, StatsHistory())
    inheritance_pool = world.create_entity()
    world.add_component(inheritance_pool, Details("Insurance Pool"))
    world.add_component(inheritance_pool, Storage())
    world.add_component(inheritance_pool, Wallet(Money(0)))
    world.add_component(inheritance_pool, InheritancePool())


def init():
    new_world = esper.World()
    # create2Entities(new_world)
    # createFewEntities(new_world)
    createManyEntities(new_world)
    createGlobalEntities(new_world)
    new_world.add_processor(Timeflow())
    new_world.add_processor(Production())
    new_world.add_processor(Ordering())
    new_world.add_processor(Exchange())
    new_world.add_processor(OrderCancellation())
    new_world.add_processor(Consumption())
    new_world.add_processor(Maturity())
    new_world.add_processor(Death())
    new_world.add_processor(InheritanceLottery())
    new_world.add_processor(WealthRedistribution(0.1))
    new_world.add_processor(TurnSummaryProcessor())
    new_world.add_processor(Cleanup())
    return new_world


if __name__ == "__main__":
    world = init()

    while True:
        world.process()
        input()
        # time.sleep(1)
