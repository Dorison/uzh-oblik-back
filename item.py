import datetime

from db import Item, SKU, db, Shipment, Issue
from typing import List, Dict
from dataclasses import dataclass, asdict
from sqlalchemy import func
@dataclass
class Requirement:
    item: Item
    sizes: Dict[str, int]

    def to_dict(self):
        d = asdict(self)
        d['sizes'] = {"?" if k is None else k: v for k, v in self.sizes.items()}
        return d

@dataclass()
class StockDTO:
    item_name: str
    item_id: int
    start_stock: int
    end_stock: int
    issued: int
    supplied: int

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

    def update_item(self, item: Item):
        self.db.session.add(item)
        self.db.session.commit()
        return item.id

    def get_by_id(self, id):
        return self.db.get_or_404(Item, id)

    def get_all(self) -> List[Item]:
        return self.db.session.execute(db.select(Item).order_by(Item.name)).scalars()

    def add_stock(self, item: Item, stock: dict[str: int], date):
        for size, count in stock.items():
            if size not in item.sizes:
                sku = SKU(size=size, count=0)
                item.sizes[size] = sku
            item.sizes[size].count += count
        shipment = Shipment(item_id=item.id, date=date, count=sum(stock.values()))
        self.db.session.add(shipment)
        self.db.session.commit()
        return shipment.id

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

    def get_stock(self, from_date, to_date):
        stock_querry = db.select(Item.name, SKU.item_id, func.sum(SKU.count)).join(Item.sizes).group_by(SKU.item_id, Item.name)
        shipment_querry = db.select(Shipment.item_id, Shipment.date<to_date, func.sum(Shipment.count)).where(Shipment.date>from_date)\
            .group_by(Shipment.item_id, Shipment.date < to_date)
        issues_querry = db.select(Issue.item_id, func.sum(Issue.count), Issue.granted< to_date).where(Issue.granted > from_date)\
            .group_by(Issue.item_id, Issue.granted < to_date)
        stock = db.session.execute(stock_querry)
        shipment = db.session.execute(shipment_querry)
        issues = db.session.execute(issues_querry)
        result = {}
        for item_name, item_id, count in stock:
            print(item_name, item_id)
            result[item_id] = StockDTO(item_name = item_name, item_id=item_id, start_stock=count,end_stock=count, issued=0, supplied=0)
        for item_id, count, inside in shipment:
            stockDTO = result[item_id]
            if inside:
                stockDTO.start_stock -= count
                stockDTO.supplied = count
            else:
                stockDTO.start_stock -= count
                stockDTO.end_stock -= count
        for item_id, count, inside in issues:
            stockDTO = result[item_id]
            if inside:
                stockDTO.start_stock += count
                stockDTO.issued = count
            else:
                stockDTO.start_stock += count
                stockDTO.end_stock += count
        return result.values()

""" def get_expires(self, from_date, term: int):
        to_date = from_date + datetime.timedelta(term)
        return self.db.session.execute(db.select(Issue).filter(Issue.expire > from_date).filter(Issue.expire < to_date)
                                       .order_by(Issue.expire)).scalars()"""


item_manager = ItemManager(db)
