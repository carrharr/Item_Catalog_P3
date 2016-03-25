#!/usr/bin/env python

"""db_model.py

Draivcan 2016

Udacity FSND P3 Item Catalog models apllied for a Tenerife (Canary Islands, Spain) car sharing webapp

# This is a project for Udacity FSND and is under development, DO NOT DEPLOY!
# Using SQLite for quick concept testing, will move onto a RNDB (probably Postgres) in the future
# No form of caching will be implemented for now

"""

__author__ = 'danielcarrilloharris@gmail.com (CarrHarr)'

from sqlalchemy import Column, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine
import enum

Base = declarative_base()

class User(Base):
    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(250), nullable=False)
    description = Column(String(250))
    picture = Column(String(250))


class Drivers(Base):
    __tablename__ = 'drivers'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    image = Column(String(250))
    email = Column(String(250))
    phone = Column(String(16))
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        """ Serialise data for json. """
        return {
            'id': self.id,
            'name': self.name,
            'image': self.image,
            'email': self.email,
            'phone': self.phone,
            'user_id': self.user_id
        }


class Trips(Base):
    __tablename__ = 'trips'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    description = Column(String(250))
    origin = Column(String(250), nullable=False)
    destination = Colum(String(250), nullable=False)
    departs = Column(Datetime, nullable=False)
    price = Column(String(8))
    category = Column(String, Enum(Ctg))
    driver_id = Column(Integer, ForeignKey('Driver.id'))
    driver = relationship(Driver)
    user_id = Column(Integer, ForeignKey('user.id'))
    user = relationship(User)

    @property
    def serialize(self):
        ''' Serialise data for json.  '''
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'origin': self.origin,
            'destination': self.destination,
            'departs': self.departs,
            'price': self.price,
            'category': self.category,
            'user_id': self.user_id
        }


class Ctg(enum.Enum):
    ''' Enum for categories. '''
    1 = "North"
    2 = "South"
    3 = "Metropolitan"
    4 = "West"
    5 = "University"
    6 = "North Airport"
    7 = "South Airport"


engine = create_engine('sqlite:///catalog.db')


Base.metadata.create_all(engine)
