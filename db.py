# -*- coding: utf-8 -*-
from __future__ import with_statement
from peewee import *
import datetime

mysql_db = MySQLDatabase(database='lunary_lviv', user='root', password='123321')

class BaseModel(Model):
    class Meta:
        database = mysql_db

class User(BaseModel):
    login = CharField()
    email = CharField()
    name = CharField()
    password = CharField()

class InfoBlock(BaseModel):
    title = CharField()
    image = CharField()
    description = TextField()

class Registered(BaseModel):
    name = CharField()
    email = CharField()
    message = TextField()
    phone = CharField()

class PageInfo(BaseModel):
    start_date = DateTimeField()
    #slogan = CharField()
    menu_1 = BooleanField()
    menu_2 = BooleanField()
    menu_3 = BooleanField()
    menu_4 = BooleanField()


mysql_db.connect()
#mysql_db.create_tables([PageInfo, Registered, InfoBlock, User])
#new_user = User(login="admin", email="test@test.ua", password="123321", name="Name")
#new_user.save()
#new_info_block = InfoBlock(title="BLOCK #1", image="path", description="descriptiondesdsed")
#new_info_block.save()
#new_page_info = PageInfo(start_date=datetime.datetime.strptime('30-01-19', '%d-%m-%y').date(), menu_1=True, menu_2=True, menu_3=True, menu_4=True)
#new_page_info.save()
#blocks = InfoBlock.select()
#for block in blocks:
#    block.delete_instance()
#block = InfoBlock.get(title='11фі')
#block.delete_instance()
