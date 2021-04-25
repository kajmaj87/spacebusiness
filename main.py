import time
from random import random

import esper # type: ignore

from components import StatsHistory, StarDate
from entities import create_person, create_farm, create_well
from processors import TurnSummaryProcessor, Consumption, Production, Ordering, Exchange, OrderCancellation, Timeflow


def createManyEntities(world):
    for i in range(100):
        create_person(world, f"MAN-{i}", food_consumption=0.5, food_amount=int(random()*10), water_amount=3, water_consumption=0.25,
                      money=1000)
    for i in range(20):
        create_farm(world, f"Farm-{i}", labour_consumption=1, food_production=1, food_storage=10, money=1500)
    for i in range(6):
        create_well(world, f"Well-{i}", labour_consumption=1, water_production=10, water_storage=100, money=1000)

def createFewEntities(world):
    for name in ["Jacek", "Wacek", "Placek", "Gacek", "Macek", "Lacek", "Picek", "XXX", "YYY"]:
        create_person(world, f"{name}", food_consumption=0.5, food_amount=int(random()*10), water_amount=3, water_consumption=0.25,
                      money=1000)
    for name in ["Folwark", "Kołko Rolnicze"]:
        create_farm(world, f"{name}", labour_consumption=1, food_production=1, food_storage=10, money=1500)
    for name in ["Mpwik", "Cisowianka"]:
        create_well(world, f"{name}", labour_consumption=1, water_production=10, water_storage=100, money=1000)

def create2Entities(world):
    for name in ["Jacek"]:
        create_person(world, f"{name}", food_consumption=0.5, food_amount=int(random()*10), water_amount=3, water_consumption=0.25,
                      money=1000)
    for name in ["Folwark"]:
        create_farm(world, f"{name}", labour_consumption=1, food_production=1, food_storage=10, money=1500)

def createGlobalEntities(world):
    globals = world.create_entity()
    world.add_component(globals, StarDate())
    world.add_component(globals, StatsHistory())

def init():
    new_world = esper.World()
    createManyEntities(new_world)
    createGlobalEntities(new_world)
    new_world.add_processor(Timeflow())
    new_world.add_processor(Consumption())
    new_world.add_processor(Production())
    new_world.add_processor(Ordering())
    new_world.add_processor(Exchange())
    new_world.add_processor(OrderCancellation())
    new_world.add_processor(TurnSummaryProcessor())
    return new_world


if __name__ == '__main__':
    world = init()

    while True:
        world.process()
        input()
        #time.sleep(1)
