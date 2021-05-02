import esper
import hypothesis.strategies as st
from hypothesis import given

from components import (
    BuyOrder,
    Money,
    OrderStatus,
    Resource,
    SellOrder,
    Storage,
    Wallet,
)
from processors.exchange import Exchange


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
    sell_price=st.integers(max_value=10, min_value=1),
)
def test_process_transaction(buyer_money, seller_money, buy_price, sell_price):
    world = esper.World()
    exchange = Exchange()
    exchange.world = world
    buyer, buy_order, seller, sell_order = prepare_transaction_arguments(world, buyer_money, seller_money, buy_price, sell_price)
    transaction_price = exchange.process_transaction(buy_order, sell_order)

    # buy and sell price ar as close as possible
    assert transaction_price.creds - transaction_price.creds <= 1, "Transaction prices differ too much"
    # amount of transferred money is same as mount of total offer
    assert abs((transaction_price + transaction_price).creds - (buy_price + sell_price)) <= 1, "Amount of money in transaction other then offering"
    assert world.component_for_entity(seller, Wallet).money.creds == seller_money + transaction_price.creds, "Seller did not got correct amount of money"
    assert world.component_for_entity(seller, Wallet).last_transaction_details_for(Resource.FOOD) == (
        transaction_price,
        OrderStatus.SOLD,
    ), "Seller did not register his transaction correctly"
    assert sell_order.status == OrderStatus.SOLD
    # buyer gets a refund as he had locked some money before transaction
    assert world.component_for_entity(buyer, Wallet).money.creds == buyer_money + (buy_price - transaction_price.creds), "Buyer did not get a refund"
    assert world.component_for_entity(buyer, Wallet).last_transaction_details_for(Resource.FOOD) == (
        transaction_price,
        OrderStatus.BOUGHT,
    ), "Buyer did not register his transaction correctly"
    # buyer did not have anything before exchange
    assert world.component_for_entity(buyer, Storage).amount(Resource.FOOD) == 1, "Buyer did not get what he bought"
    assert buy_order.status == OrderStatus.BOUGHT


@given(
    buy_price=st.integers(min_value=1),
    sell_price=st.integers(min_value=1),
)
def test_whole_process_method_single_transaction(buy_price, sell_price):
    world = esper.World()
    exchange = Exchange()
    exchange.world = world
    world.add_processor(exchange)
    buyer = world.create_entity(Wallet(Money(0)), Storage())
    seller = world.create_entity(Wallet(Money(0)), Storage())
    buy = BuyOrder(buyer, Resource.FOOD, Money(buy_price))
    sell = SellOrder(seller, Resource.FOOD, Money(sell_price))
    world.create_entity(buy)
    world.create_entity(sell)

    world.process()

    if buy_price >= sell_price:
        assert buy.status == OrderStatus.BOUGHT
        assert sell.status == OrderStatus.SOLD
    else:
        assert buy.status == OrderStatus.UNPROCESSED
        assert sell.status == OrderStatus.UNPROCESSED


@given(
    buy_prices=st.lists(st.integers(min_value=1, max_value=1000)),
    sell_prices=st.lists(st.integers(min_value=1, max_value=1000)),
)
def test_fair_transaction_assignment(buy_prices, sell_prices):
    world = esper.World()
    exchange = Exchange()
    exchange.world = world
    world.add_processor(exchange)
    buy_orders = []
    sell_orders = []
    for buy_price in buy_prices:
        buyer = world.create_entity(Wallet(Money(0)), Storage())
        buy = BuyOrder(buyer, Resource.FOOD, Money(buy_price))
        buy_orders.append(buy)
        world.create_entity(buy)
    for sell_price in sell_prices:
        seller = world.create_entity(Wallet(Money(0)), Storage())
        sell = SellOrder(seller, Resource.FOOD, Money(sell_price))
        sell_orders.append(sell)
        world.create_entity(sell)

    world.process()

    buy_orders = sorted(buy_orders, key=lambda x: x.price)
    sell_orders = sorted(sell_orders, key=lambda x: x.price)

    for cheap, expensive in zip(buy_orders, buy_orders[1:]):
        if cheap.price < expensive.price and cheap.status == OrderStatus.BOUGHT:
            assert expensive.status == OrderStatus.BOUGHT

    for cheap, expensive in zip(sell_orders, sell_orders[1:]):
        if cheap.price < expensive.price and expensive.status == OrderStatus.SOLD:
            assert cheap.status == OrderStatus.SOLD
