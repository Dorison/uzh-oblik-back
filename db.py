from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, Boolean, Integer, DateTime, Column, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from dataclasses import dataclass, asdict

class Base(DeclarativeBase):
  pass

db = SQLAlchemy(model_class=Base)
ranks = ["Головний майстер-сержант",	"Старший майстер-сержант",	"Майстер-сержант",	"Штаб-сержант",	"Головний сержант",	"Старший сержант",	"Сержант",	"Молодший сержант",	"Старший солдат",	"Солдат",	"Рекрут"]
officer_ranks = ["Генерал", 	"Генерал-лейтенант",	"Генерал-майор",	"Бригадний генерал", 	"Полковник", 	"Підполковник", 	"Майор",	"Капітан", 	"Старший лейтенант",	"Лейтенант",	"Молодший лейтенант",	"Курсант"]
sex = ["Чоловік", "Жінка"]
class DbUser(db.Model):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    hash: Mapped[str] = mapped_column(String)
    is_admin: Mapped[Boolean] = mapped_column(Boolean)

@dataclass
class Item(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    returnable: Mapped[bool] = mapped_column(Boolean)
    #TODO something reasonble Timedelta
    term: Mapped[int] = mapped_column(Integer)

    def to_dict(self):
        return asdict(self)


@dataclass
class Serviceman(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String)
    surname: Mapped[str] = mapped_column(String)
    patronymic: Mapped[str] = mapped_column(String)
    issues = relationship("Issue", backref="serviceman")

    def to_dict(self):
        d = asdict(self)
        d["issues"] = [issue.to_dict() for issue in self.issues]
        return d


@dataclass()
class Issue(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_id = Column(Integer, ForeignKey(Item.id))
    item = relationship(Item)
    serviceman_id = Column(Integer, ForeignKey(Serviceman.id))
    size: Mapped[str] = mapped_column(String)
    expire: Mapped[datetime] = mapped_column(DateTime)
    date: Mapped[datetime] = mapped_column(DateTime)

    def to_dict(self):
        d = asdict(self)
        d["date"] = d.get("date").strftime("%d.%m.%Y")
        d["item"] = self.item.to_dict()
        d["expire"] = d.get("expire").strftime("%d.%m.%Y")
        return d


