import esper
import icontract as icontract

from components import OrderStatus, BuyOrder, Details, Wallet, SellOrder, Storage, Terminated
from log import log
from .pure import total_money_locked_in_orders, total_money_in_wallets


class OrderCancellation(esper.Processor):
    def __init__(self):
        super().__init__()

    @icontract.require(lambda buy_order: buy_order.status == OrderStatus.UNPROCESSED)
    @icontract.ensure(lambda buy_order: buy_order.status == OrderStatus.CANCELLED)
    def cancel_buy_order(self, buy_order: BuyOrder):
        owner_name = self.world.component_for_entity(buy_order.owner, Details).name
        self.world.component_for_entity(buy_order.owner, Wallet).money += buy_order.price
        buy_order.status = OrderStatus.CANCELLED
        self.world.component_for_entity(buy_order.owner, Wallet).register_order(buy_order)
        log.debug(f"{owner_name} gained {buy_order.price} back as the order for {buy_order.resource} was cancelled")

    @icontract.require(lambda sell_order: sell_order.status == OrderStatus.UNPROCESSED)
    @icontract.ensure(lambda sell_order: sell_order.status == OrderStatus.CANCELLED)
    def cancel_sell_order(self, sell_order: SellOrder):
        owner_name = self.world.component_for_entity(sell_order.owner, Details).name
        owner_storage = self.world.component_for_entity(sell_order.owner, Storage)
        owner_storage.add_one_of(sell_order.resource)
        sell_order.status = OrderStatus.CANCELLED
        self.world.component_for_entity(sell_order.owner, Wallet).register_order(sell_order)
        log.debug(f"{owner_name} gained {sell_order.resource} back as the order for {sell_order.price} was cancelled")

    @icontract.snapshot(lambda self: self)
    @icontract.ensure(
        lambda OLD, self: total_money_locked_in_orders(self.world) + total_money_in_wallets(self.world)
        == total_money_locked_in_orders(OLD.self.world) + total_money_in_wallets(OLD.self.world)
    )
    def process(self):
        # self.world._clear_dead_entities()
        log.debug("\nOrder Cancellation Phase started.")
        sell_orders = self.world.get_component(SellOrder)
        buy_orders = self.world.get_component(BuyOrder)
        log.debug(f"Locks will be released for {len(sell_orders)} sell and {len(buy_orders)} buy orders still on market")
        for ent, buy_order in filter(lambda o: o[1].status == OrderStatus.UNPROCESSED, buy_orders):
            # we return money back as the order didn't happen
            self.cancel_buy_order(buy_order)

        for ent, sell_order in filter(lambda o: o[1].status == OrderStatus.UNPROCESSED, sell_orders):
            # we return resources back as the order didn't happen
            self.cancel_sell_order(sell_order)

        # mark all orders for deletion
        for ent, order in self.world.get_component(SellOrder):
            self.world.add_component(ent, Terminated())
        for ent, order in self.world.get_component(BuyOrder):
            self.world.add_component(ent, Terminated())
