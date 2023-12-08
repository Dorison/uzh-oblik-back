import datetime

from db import db, Serviceman, Issue, Item, Gender, Size
from typing import List


class ServicemanManager:
    def __init__(self, db):
        self.db = db

    def create_service_man(self, name, surname, patronymic, gender: Gender, rank: int, group: str):
        now = datetime.datetime.now()
        history = (rank+1)*[now]
        serviceman = Serviceman(name=name, surname=surname, patronymic=patronymic, rank_history=history, gender=gender, group=group)
        self.db.session.add(serviceman)
        self.db.session.commit()
        return serviceman.id

    def get_by_id(self, serviceman_id) -> Serviceman:
        return self.db.get_or_404(Serviceman, serviceman_id)

    def get_all(self) -> List[Serviceman]:
        return self.db.session.execute(db.select(Serviceman).order_by(Serviceman.surname)).scalars()

    def issue_item(self, servicemen: Serviceman, item: Item, size: str, date:datetime, granted:datetime, count: int) -> int:
        issue = Issue(item=item, size=size, date=date, granted=granted, count=count)
        servicemen.issues.append(issue)
        self.db.session.add(issue)
        self._set_size(servicemen, item, size)
        self.db.session.commit()
        return issue.id

    def _set_size(self, servicemen: Serviceman, item:Item, size_str: str):
        size = Size(size=size_str, item=item)
        self.db.session.add(size)
        servicemen.sizes[item.id] = size

    def set_size(self, servicemen: Serviceman, item: Item, size: str):
        self._set_size(servicemen, item, size)
        self.db.session.commit()


serviceman_manager = ServicemanManager(db)
