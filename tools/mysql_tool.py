# -*- coding: utf-8 -*-
"""
Created by 18034 on 2024/4/27.
"""
import pandas as pd
import pymysql
from loguru import logger
from pymysql import cursors


class MySQLTool:
    def __init__(self, host='localhost', user='root', password='root', database=None, table_name=None):
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.table_name = table_name

        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        self.conn = pymysql.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database,
            charset='utf8mb4',
            cursorclass=cursors.DictCursor
        )
        self.cursor = self.conn.cursor()

    def close(self):
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()

    def create_table(self, schema):
        """
        Create the table for storing crawler dictionaries.
        Schema should be a string defining the CREATE TABLE statement.

        Example:
            schema =
        """

        query = schema.format(table_name=self.table_name)
        self.cursor.execute(query)
        self.conn.commit()

    def save_dict_to_mysql(self, data_dict, update_keys=None, update_all=True):
        """
        向表中插入一个字典。如果主键或唯一键已经存在，则更新记录。

        参数:
        data_dict (dict):包含要插入的键值对的字典。
        update_keys (list):要在重复时更新的键的列表。如果为None，则update_all为True时更新所有列。
        update_all (bool): update_keys为None时，是否更新重复的所有列。
        """
        columns = ', '.join(data_dict.keys())
        placeholders = ', '.join(['%s'] * len(data_dict))

        if update_keys:
            update_placeholders = ', '.join([f"{col} = VALUES({col})" for col in update_keys])
        elif update_all:
            update_placeholders = ', '.join([f"{col} = VALUES({col})" for col in data_dict.keys()])
        else:
            update_placeholders = ''

        query = f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders})"
        if update_placeholders:
            query += f" ON DUPLICATE KEY UPDATE {update_placeholders}"

        values = tuple(data_dict.values())
        self.cursor.execute(query, values)
        self.conn.commit()

    def save_dict_list_to_mysql(self, dict_list, update_keys=None, update_all=True):
        """
        向表中插入一个字典列表。

        参数:
        dict_list (list[dict]):包含要插入的键值对的字典列表。
        """
        if not dict_list:
            print("Error: dict_list is empty")
            return
        if update_keys and isinstance(update_keys, list):
            for data_dict in dict_list:
                try:
                    self.save_dict_to_mysql(data_dict, update_keys=update_keys, update_all=update_all)
                except Exception as e:
                    print(f"Error saving dict {data_dict}\n{e}")
        else:
            print("Error: update_keys must be a list ")

    def update_dict_by_key(self, key, updated_data):
        """
        根据字典的唯一键更新表中的字典。

        参数:
        key (str):要更新的字典的唯一键。
        updated_data (dict):包含更新的键值对的字典。
        """
        set_clauses = ', '.join([f"{col} = %s" for col in updated_data.keys()])
        query = f"UPDATE {self.table_name} SET {set_clauses} WHERE key = %s"
        values = tuple(updated_data.values()) + (key,)
        self.cursor.execute(query, values)
        self.conn.commit()

    def _execute_query(self, query, params=None, fetch_one=False):
        """
        执行SQL查询并返回结果。

        参数:
            query (str): 要执行的SQL查询语句。
            params (tuple or None): 查询参数，如果没有参数则为None。
            fetch_one (bool): 是否仅获取第一条结果，默认为False。

        返回:
            dict or list[dict]: 单个字典（fetch_one=True）或字典列表（fetch_one=False），
                                如果未找到结果，则返回None或空列表。
        """
        self.cursor.execute(query, params or ())
        if fetch_one:
            result = self.cursor.fetchone()
            return result if result else None
        else:
            results = self.cursor.fetchall()
            return results if results else []

    def query_dict_by_key(self, key):
        """
        通过表的唯一键从表中检索单个字典。

        参数:
            key (str): 要检索的字典的唯一键。

        返回:
            dict: 匹配的字典，如果未找到，则为 None。
        """
        query = f"SELECT * FROM {self.table_name} WHERE key = %s"
        return self._execute_query(query, (key,), fetch_one=True)

    def query_dicts_by_key(self, key):
        """
        通过表的指定键从表中检索所有相关字典。

        参数:
            key (str): 要检索的字典的键。

        返回:
            list[dict]: 与指定键关联的字典列表，如果未找到，则返回空列表。
        """
        query = f"SELECT * FROM {self.table_name} WHERE key = %s"
        return self._execute_query(query, (key,))

    def query(self):
        """
        从表中检索所有字典。

        返回:
            list[dict]: 存储在表中的字典列表。
        """
        query = f"SELECT * FROM {self.table_name}"
        return self._execute_query(query)

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


if __name__ == '__main__':
    host = 'localhost'
    user = 'root'
    password = 'root'
    database = 'test'
    table_name = 'movie_top_250'
    schema = create_table_query = f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        detail_url TEXT,
        img_url TEXT,
        cn_name TEXT,
        en_name TEXT,
        score FLOAT,
        evaluation_num INT,
        overview TEXT,
        related_information TEXT,
        _5_stars TEXT,
        _4_stars TEXT,
        _3_stars TEXT,
        _2_stars TEXT,
        _1_stars TEXT,
        director TEXT,
        screen_writer TEXT,
        starring_role TEXT,
        types TEXT,
        producer_country_region TEXT,
        language TEXT,
        release_date TEXT,
        length_of_film TEXT,
        aka TEXT,
        IMDb TEXT,
        introduction TEXT,
        info TEXT,
        official_website TEXT,
        official_station TEXT
    );
    """
    data_list = pd.read_excel('movie_top_250.xlsx')
    with MySQLTool(host, user, password, database, table_name) as db_manager:
        db_manager.create_table(schema)
        db_manager.save_dict_list_to_mysql(data_list)
