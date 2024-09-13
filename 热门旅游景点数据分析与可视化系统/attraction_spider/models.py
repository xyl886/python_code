# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, Column, Integer, String, Text, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()


class RegionInformation(Base):
    __tablename__ = 'region_information'

    region_id = Column(String(10), primary_key=True)  # 指定长度为10
    pinyin = Column(String(50))
    name = Column(String(50))
    nums = Column(Integer)
    detail = Column(Text)
    top3 = Column(Text)
    url = Column(String(255))
    attraction = Column(Boolean, default=False)
    attraction_review = Column(Boolean, default=False)


class Attraction(Base):
    __tablename__ = 'attraction'

    attraction_id = Column(String(255), primary_key=True)
    name = Column(String(255))
    url = Column(String(255))
    address = Column(String(255))
    detail_fetch = Column(Boolean, default=False)
    price_list = Column(Text)
    review_num = Column(Integer, default=0)
    summary = Column(Text)
    transport = Column(Text)
    open_time = Column(Text)
    time_reference = Column(String(255))
    ticket_info = Column(Text)
    phone = Column(String(255))
    introduction = Column(Text)
    en_name = Column(Text)
    cn_name = Column(Text)
    city_id = Column(Integer)
    review_fetch = Column(Boolean, default=False)


class Review(Base):
    __tablename__ = 'review'

    review_id = Column(String(255), primary_key=True)
    attraction_id = Column(String(255))
    lv = Column(String(50))
    nick_name = Column(String(255))
    user_url = Column(String(255))
    rev_txt = Column(Text)
    rev_img = Column(Text)  # JSONField is not supported directly, using Text to store JSON data
    rev_time = Column(String(50))  # Assuming storing as string; you can use DateTime if it stores datetime data
    star = Column(String(50))


# 数据库连接配置
DATABASE_URL = 'mysql+pymysql://root:root@localhost:3306/attraction_admin'

engine = create_engine(DATABASE_URL,
                       pool_size=20,  # 连接池大小
                       max_overflow=10,  # 允许溢出的连接数
                       pool_timeout=30  # 等待连接超时时间
                       )
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)
