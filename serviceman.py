import datetime

from db import db, Serviceman, Issue, Item, Gender, Size, ParentalLeave
from typing import List


class ServicemanManager:
    def __init__(self, db):
        self.db = db

    def create_service_man(self, name, surname, patronymic, gender: Gender, rank: int, group: str, date: datetime):
        history = (rank+1)*[date]
        serviceman = Serviceman(name=name, surname=surname, patronymic=patronymic, rank_history=history, gender=gender, group=group)
        self.db.session.add(serviceman)
        self.db.session.commit()
        return serviceman.id


    def get_by_id(self, serviceman_id) -> Serviceman:
        return self.db.get_or_404(Serviceman, serviceman_id)

    def get_all(self) -> List[Serviceman]:
        return self.db.session.execute(db.select(Serviceman).order_by(Serviceman.surname)).scalars()

    def promote(self, serviceman: Serviceman, rank: int, date: datetime):
        rank_history = serviceman.rank_history
        serviceman.rank_history.extend([date]*(rank-len(rank_history)+1))
        self.db.session.add(serviceman)
        self.db.session.commit()

    def issue_item(self, servicemen: Serviceman, item: Item, size: str, date:datetime, granted:datetime, count: int) -> int:
        issue = Issue(item=item, size=size, date=date, granted=granted, count=count)
        servicemen.issues.append(issue)
        item.sizes[size].count -= count
        self.db.session.add(issue)
        self._set_size(servicemen, item, size)
        self.db.session.commit()
        return issue.id

    def history_issue_item(self, servicemen: Serviceman, item: Item, date: datetime, granted: datetime, count:int):
        issue = Issue(item=item, date=date, granted=granted, count=count)
        servicemen.issues.append(issue)
        self.db.session.add(issue)
        self.db.session.commit()
        return issue.id

    def _set_size(self, servicemen: Serviceman, item:Item, size_str: str):
        size = Size(size=size_str, item=item)
        self.db.session.add(size)
        servicemen.sizes[item.id] = size
        return size

    def set_size(self, servicemen: Serviceman, item: Item, size: str):
        size = self._set_size(servicemen, item, size)
        self.db.session.commit()
        return size.id

    def terminate(self, serviceman:Serviceman, date: datetime):
        serviceman.termination_date = date
        self.db.session.add(serviceman)
        self.db.session.commit()
        return serviceman.id

    def parental_leave(self, serviceman: Serviceman, from_date: datetime, to_date: datetime):
        parental_leave = ParentalLeave(from_date=from_date, to_date=to_date)
        if serviceman.parental_leaves is None:
            serviceman.parental_leaves = [parental_leave]
        else:
            serviceman.parental_leaves.appent(parental_leave)
        self.db.session.add(serviceman)
        self.db.session.commit()
        return parental_leave.id





serviceman_manager = ServicemanManager(db)
