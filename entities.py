from components import Consumer, ResourcePile, Resource, Details, Storage, Producer, SellOrder, Wallet, Needs, Need


def create_person(world, name, food_consumption, food_amount):
    person = world.create_entity()
    storage = Storage()
    storage.add(ResourcePile(Resource.FOOD, food_amount))
    # not possible to store man days
    storage.set_limit(ResourcePile(Resource.MAN_DAY, 1))

    needs = Needs()
    needs.add(Need("have food for tomorrow", priority=1, pile=ResourcePile(Resource.FOOD, food_consumption), price_change_on_buy=1, price_change_on_failed_buy=1.5))
    needs.add(Need("have food for next few days", priority=2, pile=ResourcePile(Resource.FOOD, 4*food_consumption), price_change_on_buy=0.9, price_change_on_failed_buy=1.1))
    needs.add(Need("have a big stash of food", priority=3, pile=ResourcePile(Resource.FOOD, 10*food_consumption), price_change_on_buy=0.8, price_change_on_failed_buy=1.05))

    world.add_component(person, Details(name))
    world.add_component(person, Wallet(20))
    world.add_component(person, Consumer(ResourcePile(Resource.FOOD, food_consumption)))
    # man days are produced from nothing
    world.add_component(person, Producer(ResourcePile(Resource.NOTHING), ResourcePile(Resource.MAN_DAY, 1)))
    world.add_component(person, storage)
    world.add_component(person, needs)
    return person

def create_farm(world, name, labour_consumption, food_production, food_storage, money):
    farm = world.create_entity()
    storage = Storage()
    storage.set_limit(ResourcePile(Resource.FOOD, food_storage))

    needs = Needs()
    needs.add(Need("have someone in work", priority=1, pile=ResourcePile(Resource.MAN_DAY, 1), price_change_on_buy=0.9, price_change_on_failed_buy=1.1))
    needs.add(Need("have someone in work", priority=2, pile=ResourcePile(Resource.MAN_DAY, 1), price_change_on_buy=0.8, price_change_on_failed_buy=1.05))
    needs.add(Need("have someone in work", priority=3, pile=ResourcePile(Resource.MAN_DAY, 1), price_change_on_buy=0.7, price_change_on_failed_buy=1.02))

    world.add_component(farm, Details(name))
    world.add_component(farm, Wallet(money))
    world.add_component(farm, Producer(ResourcePile(Resource.MAN_DAY, labour_consumption), ResourcePile(Resource.FOOD, food_production)))
    world.add_component(farm, storage)
    world.add_component(farm, needs)
    return farm

