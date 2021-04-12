import time
from random import random

import esper

from components import StatsHistory, StarDate
from entities import create_person, create_farm, create_well
from processors import TurnSummaryProcessor, Consumption, Production, Ordering, Exchange, OrderCancellation, Timeflow


def createEntities(world):
    #for name in ["Jacek", "Wacek", "Placek", "Gacek", "Macek", "Lacek", "Picek"]:
    for i in range(100):
        create_person(world, f"MAN-{i}", food_consumption=0.5, food_amount=int(random()*10), water_amount=3, water_consumption=0.25,
                      money=10)
    #for name in ["Folwark", "Kołko Rolnicze"]:
    for i in range(20):
        create_farm(world, f"Farm-{i}", labour_consumption=1, food_production=1, food_storage=10, money=15)
    for i in range(6):
        create_well(world, f"Well-{i}", labour_consumption=1, water_production=10, water_storage=100, money=10)

def createGlobalEntities(world):
    globals = world.create_entity()
    world.add_component(globals, StarDate())
    world.add_component(globals, StatsHistory())

def init():
    new_world = esper.World()
    createEntities(new_world)
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
