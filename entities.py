from components import Consumer, ResourcePile, Resource, Details, Storage, Producer, SellOrder, Wallet


def create_person(world, name, food_consumption, food_amount):
    person = world.create_entity()
    storage = Storage()
    storage.add(ResourcePile(Resource.FOOD, food_amount))
    # not possible to store man days
    storage.set_limit(ResourcePile(Resource.MAN_DAY, 1))

    world.add_component(person, Details(name))
    world.add_component(person, Wallet(20))
    world.add_component(person, Consumer(ResourcePile(Resource.FOOD, food_consumption)))
    # man days are produced from nothing
    world.add_component(person, Producer(ResourcePile(Resource.NOTHING), ResourcePile(Resource.MAN_DAY, 1)))
    world.add_component(person, storage)
    return person

def create_farm(world, name, labour_consumption, food_production, food_storage, money):
    farm = world.create_entity()
    storage = Storage()
    storage.set_limit(ResourcePile(Resource.FOOD, food_storage))

    world.add_component(farm, Details(name))
    world.add_component(farm, Wallet(money))
    world.add_component(farm, Producer(ResourcePile(Resource.MAN_DAY, labour_consumption), ResourcePile(Resource.FOOD, food_production)))
    world.add_component(farm, storage)
    return farm


