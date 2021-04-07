import esper

from entities import createPerson
from processors import TurnSummaryProcessor, Consumption, Production


def createEntities(world):
    for name in ["Jacek", "Wacek", "Placek"]:
        createPerson(world, name, 0.5, len(name)/2)


def init():
    new_world = esper.World()
    createEntities(new_world)
    new_world.add_processor(Consumption())
    new_world.add_processor(Production())
    new_world.add_processor(TurnSummaryProcessor())
    return new_world


if __name__ == '__main__':
    world = init()

    while True:
        world.process()
        input()
