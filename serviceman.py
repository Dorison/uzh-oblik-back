from db import db, Serviceman, Issue, Item
from typing import List


class ServicemanManager:
    def __init__(self, db):
        self.db = db

    def create_service_man(self, name, surname, patronymic):
        serviceman = Serviceman(name=name, surname=surname, patronymic=patronymic)
        self.db.session.add(serviceman)
        self.db.session.commit()
        return serviceman.id

    def get_by_id(self, id)-> Serviceman:
        return self.db.get_or_404(Serviceman, id)


    def get_all(self)->List[Serviceman]:
        return db.session.execute(db.select(Serviceman).order_by(Serviceman.surname)).scalars()

    def issue_item(self, servicemen: Serviceman, item: Item, size: str, date)->int:
        issue = Issue(item=item, term=item.term, servicemen_id=servicemen.id, size=size)
        servicemen.issues.add(issue)
        self.db.session.add(issue)
        self.db.session.commit()
        return issue.id







serviceman_manager = ServicemanManager(db)