import esper

from components import Storage, Consumer, Details, Producer


class TurnSummaryProcessor(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print("Another turn has passed.")


class Consumption(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print(f"Consumption starting.")
        consumers = self.world.get_components(Details, Storage, Consumer)
        for ent, (details, storage, consumer) in consumers:
            if storage.has_at_least(consumer.needed_pile()):
                storage.remove(consumer.needed_pile())
                print(f"Removed {consumer.needed_pile()} from {details.name}")
            else:
                print(f"Consumer {details.name} did not have {consumer.needed_pile()}")


class Production(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        print(f"Production starting")
        producers = self.world.get_components(Details, Storage, Producer)
        for ent, (details, storage, producer) in producers:
            if not storage.has_at_least(producer.needed_pile()):
                print(f"Producer {details.name} did not have {producer.needed_pile()} to start production")
            elif not storage.will_fit(producer.created_pile()):
                print(f"Producer {details.name} did not have place to hold {producer.created_pile()}")
            else:
                storage.remove(producer.needed_pile())
                storage.add(producer.created_pile())
                print(f"Producer {details.name} produced {producer.created_pile()}")
