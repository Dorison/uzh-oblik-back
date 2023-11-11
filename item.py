from db import Item, db


class ItemManager:

    def __init__(self, db):
        self.db = db

    def create_item(self, name: str, returnable: bool, term: float):
        item = Item(name=name, returnable=returnable, term=term)
        self.db.session.add(item)
        self.db.session.commit()
        return item.id

    def get_by_id(self, id):
        return self.db.get_or_404(Item, id)
