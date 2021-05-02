import esper

from components import Consumer, Details, Hunger, Resource, ResourcePile, Storage
from log import log


class Consumption(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        def consume_if_possible(ent, storage: Storage, pile: ResourcePile):
            if storage.has_at_least(pile):
                storage.remove(pile)
                log.debug(f"Removed {pile} from {details.name}")
            else:
                log.debug(f"Consumer {details.name} did not have {pile} and will suffer consequences")
                if pile.resource_type == Resource.FOOD:
                    self.world.add_component(ent, Hunger())

        log.debug("\nConsumption Phase started.")
        consumers = self.world.get_components(Details, Storage, Consumer)
        for ent, (details, storage, consumer) in consumers:
            for need in consumer.needs:
                consume_if_possible(ent, storage, need)
