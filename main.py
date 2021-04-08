import esper

from entities import create_person, create_farm
from processors import TurnSummaryProcessor, Consumption, Production, Ordering, Exchange, OrderCancellation


def createEntities(world):
    for name in ["Jacek", "Wacek", "Placek"]:
        create_person(world, name, 0.5, len(name) / 2)
    for name in ["Folwark","Kołko Rolnicze"]:
        create_farm(world, name, labour_consumption=1, food_production=1, food_storage=10, money=30)
        
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
        input()
