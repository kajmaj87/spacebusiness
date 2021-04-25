import esper

from hypothesis import given
import hypothesis.strategies as st

from components import Money, Wallet, Storage, ResourcePile, Resource, SellOrder, BuyOrder, OrderStatus
from processors import Exchange


def prepare_transaction_arguments(world, buyer_money, seller_money, buy_price, sell_price):
    buyer = world.create_entity()
    seller = world.create_entity()
    world.add_component(buyer, Wallet(Money(buyer_money)))
    world.add_component(buyer, Storage())
    world.add_component(seller, Wallet(Money(seller_money)))
    world.add_component(seller, Storage())

    sell_ent = world.create_entity()
    sell_order = SellOrder(seller, Resource.FOOD, Money(sell_price))
    buy_ent = world.create_entity()
    buy_order = BuyOrder(buyer, Resource.FOOD, Money(buy_price))

    world.add_component(buy_ent, buy_order)
    world.add_component(sell_ent, sell_order)
    return buyer, buy_order, seller, sell_order


@given(
    buyer_money=st.integers(max_value=100, min_value=0),
    seller_money=st.integers(max_value=100, min_value=0),
    buy_price=st.integers(max_value=20, min_value=10),
    sell_price=st.integers(max_value=10, min_value=1)
)
def test_process_transaction(buyer_money, seller_money, buy_price, sell_price):
    world = esper.World()
    exchange = Exchange()
    exchange.world = world
    buyer, buy_order, seller, sell_order = prepare_transaction_arguments(world, buyer_money,
                                                                                            seller_money, buy_price,
                                                                                            sell_price)
    transaction_buy_price, transaction_sell_price = exchange.process_transaction(buy_order, sell_order)

    # buy and sell price ar as close as possible
    assert transaction_buy_price.creds - transaction_sell_price.creds <= 1, "Transaction prices differ too much"
    # amount of transferred money is same as mount of total offer
    assert (transaction_buy_price + transaction_sell_price).creds == buy_price + sell_price, "Amount of money in transaction other then offering"
    assert world.component_for_entity(seller, Wallet).money.creds == seller_money + transaction_sell_price.creds, "Seller did not got correct amount of money"
    assert world.component_for_entity(seller, Wallet).last_transaction_details_for(Resource.FOOD) == (transaction_sell_price, OrderStatus.SOLD), "Seller did not register his transaction correctly"
    assert sell_order.status == OrderStatus.SOLD
    # buyer gets a refund as he had locked some money before transaction
    assert world.component_for_entity(buyer, Wallet).money.creds == buyer_money + (buy_price - transaction_buy_price.creds), "Buyer did not get a refund"
    assert world.component_for_entity(buyer, Wallet).last_transaction_details_for(Resource.FOOD) == (transaction_buy_price, OrderStatus.BOUGHT), "Buyer did not register his transaction correctly"
    # buyer did not have anything before exchange
    assert world.component_for_entity(buyer, Storage).amount(Resource.FOOD) == 1, "Buyer did not get what he bought"
    assert buy_order.status == OrderStatus.BOUGHT