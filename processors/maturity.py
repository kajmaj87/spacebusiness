from random import randint

import esper

from components import Details, Resource, ResourcePile, Storage
from entities import create_person
from log import log


class Maturity(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, (details, storage) in self.world.get_components(Details, Storage):
            if storage.has_one(Resource.GROWN_HUMAN):
                log.warning(f"{details.name} created a grown human!")
                storage.remove_one_of(ResourcePile(Resource.GROWN_HUMAN))
                # FIXME cloning center should also have bought this water
                # FIXME those values should be constant and same as for other people in the world
                create_person(
                    self.world,
                    f"Clone-{randint(0,10000)}",
                    food_consumption=0.5,
                    food_amount=5,
                    water_amount=5,
                    water_consumption=0.25,
                    money=0,
                )
