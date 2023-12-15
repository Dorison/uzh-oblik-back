import datetime

from db import Item, SKU, db
from typing import List, Dict
from dataclasses import dataclass, asdict
@dataclass
class Requirement:
    item: Item
    sizes: Dict[str, int]

    def to_dict(self):
        return asdict(self)


class ItemManager:

    def __init__(self, db):
        self.db = db

    def create_item(self, name: str, returnable: bool):
        item = Item(name=name, returnable=returnable)
        self.db.session.add(item)
        self.db.session.commit()
        return item.id

    def get_by_id(self, id):
        return self.db.get_or_404(Item, id)

    def get_all(self) -> List[Item]:
        return self.db.session.execute(db.select(Item).order_by(Item.name)).scalars()

    def add_stock(self, item: Item, stock: dict[str: int]):
        for size, count in stock.items():
            if size not in item.sizes:
                sku = SKU(size=size, count=0)
                item.sizes[size] = sku
            item.sizes[size].count += count
        self.db.session.commit()

    def get_requirements(self, obligations: List[Dict]) -> List[Requirement]:
        reqs: Dict[int, Dict[str, int]] = {}
        items: Dict[int, Item] = {}
        for servicemnan_obligations in obligations:
            for obligation_list in servicemnan_obligations.values():
                for obligation in obligation_list:
                    item = obligation.item
                    if item.id in reqs:
                        req = reqs[item.id]
                        if obligation.size in req:
                            req[obligation.size] += obligation.count
                        else:
                            req[obligation.size] = obligation.count
                    else:
                        reqs[item.id] = {obligation.size: obligation.count}
                        items[item.id] = item
        return [Requirement(items[i], req) for i, req in reqs.items()]

""" def get_expires(self, from_date, term: int):
        to_date = from_date + datetime.timedelta(term)
        return self.db.session.execute(db.select(Issue).filter(Issue.expire > from_date).filter(Issue.expire < to_date)
                                       .order_by(Issue.expire)).scalars()"""


item_manager = ItemManager(db)
