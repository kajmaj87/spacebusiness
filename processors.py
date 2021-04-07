import esper

from components import Storage, Consumer, Details


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
            if(storage.amount(consumer.resource_type()) >= consumer.needed_amount()):
                storage.remove(consumer.resource_type(), consumer.needed_amount())
                print(f"Removed {consumer.needed_amount()} of {consumer.resource_type()} from {details.name}")
            else:
                print(f"{details.name} had not enough {consumer.resource_type()} to remove (has: {storage.amount(consumer.resource_type())}, needed {consumer.needed_amount()})")

