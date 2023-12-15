import datetime

from db import db, Serviceman, Issue, Item, Gender, Size, ParentalLeave
from typing import List
from flask import abort

import logging
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
        # TODO understand this behaviour
        serviceman.rank_history = rank_history[:]+[date] * (rank - len(rank_history) + 1)
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
            serviceman.parental_leaves.append(parental_leave)
        self.db.session.add(serviceman)
        self.db.session.commit()
        return parental_leave.id

    def parental_leave_close(self, serviceman: Serviceman, leave_id: int, to_date: datetime) -> int:
        for leave in serviceman.parental_leaves:
            if leave.id == leave_id:
                break
        else:
            abort(404, f"{leave_id} not found in leaves of {serviceman.id}")
        if leave.to_date is not None:
            abort(403, f"leave already closed {leave.to_date}")
        leave.to_date = to_date
        self.db.session.add(serviceman)
        self.db.session.commit()
        return leave_id


serviceman_manager = ServicemanManager(db)
