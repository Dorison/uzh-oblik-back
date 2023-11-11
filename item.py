from db import Item, db
from typing import List


class ItemManager:

    def __init__(self, db):
        self.db = db

    def create_item(self, name: str, returnable: bool, term: int):
        item = Item(name=name, returnable=returnable, term=term)
        self.db.session.add(item)
        self.db.session.commit()
        return item.id

    def get_by_id(self, id):
        return self.db.get_or_404(Item, id)

    def get_all(self)->List[Item]:
        return self.db.session.execute(db.select(Item).order_by(Item.name)).scalars()


item_manager = ItemManager(db)
