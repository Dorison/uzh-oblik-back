from db import db, Serviceman
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
        return db.session.execute(db.select(Serviceman).order_by.surname).scalars()






serviceman_manager = ServicemanManager(db)