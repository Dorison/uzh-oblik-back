from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column


class Base(DeclarativeBase):
  pass


db = SQLAlchemy(model_class=Base)


class DbUser(db.Model):
    id: Mapped[str] = mapped_column(String, primary_key=True)
    hash: Mapped[str] = mapped_column(String)
    is_admin: Mapped = mapped_column(Boolean)
