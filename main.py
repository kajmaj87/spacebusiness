import time

import esper

from entities import create_person, create_farm, create_well
from processors import TurnSummaryProcessor, Consumption, Production, Ordering, Exchange, OrderCancellation


def createEntities(world):
    for name in ["Jacek", "Wacek", "Placek", "Gacek", "Macek", "Lacek", "Picek"]:
        create_person(world, name, food_consumption=0.5, food_amount=len(name) / 2, water_amount=3, water_consumption=0.25,
                      money=10)
    for name in ["Folwark", "Kołko Rolnicze"]:
        create_farm(world, name, labour_consumption=1, food_production=1, food_storage=10, money=15)
    for name in ["MPWiK", "Cisowianka"]:
        create_well(world, name, labour_consumption=1, water_production=10, water_storage=100, money=10)


def init():
    new_world = esper.World()
    createEntities(new_world)
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
        # input()
        time.sleep(1)
