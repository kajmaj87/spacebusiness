import esper

from components import Details, Producer, Storage
from log import log


class Production(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        log.debug("Production Phase started")
        producers = self.world.get_components(Details, Storage, Producer)
        for ent, (details, storage, producer) in producers:
            while storage.has_at_least(producer.needed_pile()) and storage.will_fit(producer.created_pile()):
                storage.remove(producer.needed_pile())
                storage.add(producer.created_pile())
                log.debug(f"Producer {details.name} produced {producer.created_pile()}")
            if not storage.will_fit(producer.created_pile()):
                log.debug(f"Producer {details.name} did not have place to hold {producer.created_pile()}")
            if not storage.has_at_least(producer.needed_pile()):
                log.debug(f"Producer {details.name} did not have {producer.needed_pile()} to start production")
