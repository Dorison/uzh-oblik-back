import datetime

from db import Item, db, Issue
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

    def get_expires(self, from_date , term:int):
        to_date = from_date + datetime.timedelta(term)
        return self.db.session.execute(db.select(Issue).filter(Issue.expire > from_date).filter(Issue.expire < to_date)
                                       .order_by(Issue.expire)).scalars()


item_manager = ItemManager(db)
