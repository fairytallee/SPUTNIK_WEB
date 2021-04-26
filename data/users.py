import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from .db_session import SqlAlchemyBase


class User(SqlAlchemyBase, UserMixin):
    __tablename__ = 'users'

    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    surname = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    age = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    email = sqlalchemy.Column(sqlalchemy.String, nullable=True, unique=True)
    password = sqlalchemy.Column(sqlalchemy.String, nullable=True)

    news = orm.relation("News", back_populates='user')
    arts = orm.relation("Arts", back_populates='user')

    def __repr__(self):
        return f"<User> {' '.join(map(str, [self.id, self.surname, self.name]))}"
