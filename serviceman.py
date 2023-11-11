from db import db, Serviceman


class ServicemanManager:
    def __init__(self, db):
        self.db = db

    def create_service_man(self, name, surname, patronymic):
        serviceman = Serviceman(name=name, surname=surname, patronymic=patronymic)
        self.db.session.add(serviceman)
        self.db.session.commit()


serviceman_manager = ServicemanManager(db)