import esper

from components import Terminated


class Cleanup(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for ent, terminated in self.world.get_component(Terminated):
            self.world.delete_entity(ent)
