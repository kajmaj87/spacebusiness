import esper

from components import (
    Details,
    Hunger,
    InheritancePool,
    Resource,
    Storage,
    Terminated,
    Wallet,
)
from log import log


class Death(esper.Processor):
    def __init__(self):
        super().__init__()

    def process(self):
        for _, (pool_storage, pool_wallet, _) in self.world.get_components(Storage, Wallet, InheritancePool):
            for ent, (details, storage, wallet, _) in self.world.get_components(Details, Storage, Wallet, Hunger):
                log.warning(f"{details.name} died of hunger")
                storage.add_one_of(Resource.SOUL)
                pool_storage.add_all(storage)
                pool_wallet.money += wallet.money
                self.world.add_component(ent, Terminated())
            log.debug(f"Inheritance pool contents: {pool_wallet.money} and {pool_storage}")
