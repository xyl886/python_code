# -*- coding: utf-8 -*-
import threading
from concurrent.futures import ThreadPoolExecutor

import pymongo.errors
from loguru import logger
from pymongo import MongoClient
import hashlib
import time
from excel_tool import save_dict_list_to_excel


class MongoDB:
    _instance_lock = threading.Lock()  # 线程锁
    _instance = None  # 单例实例

    @logger.catch
    def __new__(cls, *args, **kwargs):
        """
        利用线程锁，实现多线程下的单例模式
        """
        if not cls._instance:
            with cls._instance_lock:
                if not cls._instance:
                    cls._instance = super().__new__(cls)
        return cls._instance

    @logger.catch
    def __init__(self,
                 host='localhost',
                 port=27017,
                 db_name: str = '',
                 collection_name: str = None,
                 username: str = None,
                 password: str = None):
        """
        初始化 MongoDB 连接
        :param host: MongoDB服务器地址
        :param port: MongoDB服务器端口
        :param db_name: 数据库名称
        :param collection_name: 集合名称
        :param username: 用户名
        :param password: 密码
        """
        if not hasattr(self, 'initialized'):  # 避免重复初始化
            self.client = None
            self.db = None
            self.collection = None
            self.db_name = db_name
            self.collection_name = collection_name
            self.rlock = threading.RLock()  # 添加实例级别的锁
            self._connect_to_db(host, port, username, password)
            self.initialized = True

    def _connect_to_db(self, host, port, username, password):
        try:
            self.client = MongoClient(host=host, port=port, username=username, password=password)
            if self.db_name:
                self.db = self.client[self.db_name]
                if self.collection_name:
                    self.collection = self.db[self.collection_name]
                    logger.info(f"已连接 MongoDB: {self.db_name}:{self.collection_name}")
                else:
                    logger.info(f"已连接 MongoDB: {self.db_name}")
            else:
                logger.info("已连接到 MongoDB 服务器，但未选择数据库。")
        except Exception as e:
            self._handle_connection_error(e, host, port, username, password)

    def _handle_connection_error(self, e, host, port, username, password):
        error_msg = f"无法连接到 MongoDB 数据库 ({self.db_name})，请检查以下信息："
        if not username or not password:
            error_msg += "\n- 用户名和/或密码未提供或无效"
        error_msg += f"\n- 主机: {host}\n- 端口: {port}\n\n详细错误：{str(e)}"
        raise ConnectionError(error_msg)

    @logger.catch
    def use(self, collection_name: str = '', db_name: str = ''):
        """
        切换当前使用的 MongoDB 集合。
        :param db_name: (str)新的库名称。
        :param collection_name: (str)新的集合名称。
        :return: None
        """
        try:
            if db_name:
                self.db_name = db_name
                self.db = self.client[db_name]
            if collection_name:
                self.collection_name = collection_name
                self.collection = self.db[collection_name]
            logger.info(f"已连接 MongoDB: {self.db_name}:{self.collection_name}")
        except Exception as e:
            logger.error(f"切换到数据库: {db_name} 或集合: {collection_name} 失败。错误信息: {str(e)}")
            raise RuntimeError(f"无法切换到数据库: {db_name} 或集合: {collection_name}。错误信息: {str(e)}")

        return self

    @logger.catch
    def find_documents(self,
                       query: dict = None,
                       projection: dict = None,
                       limit: int = 0,
                       skip: int = 0,
                       distinct_key: str = None,
                       explain: bool = False):
        """
        根据给定的查询条件（query）从指定集合中查找文档。

        参数:
            query (dict): 查询条件，使用 MongoDB 查询语法。
            projection (dict, optional): 返回字段投影，仅返回指定的字段。默认返回所有字段。
            limit (int, optional): 返回结果的最大数量，默认返回所有匹配的文档。
            skip (int, optional): 跳过指定数量的文档，用于分页。
            distinct_key(str,optional): 根据某个key的value进行去重
            explain (bool, optional): 是否返回查询计划。默认为False。

        返回:
            - list[dict]: 匹配查询条件的文档列表（字典形式）。
            - dict: 如果`explain=True`，返回查询计划。
        """

        start_time = time.perf_counter()
        try:
            if distinct_key is not None:
                with self.rlock:
                    self.collection.create_index(distinct_key)
                    distinct_values = self.collection.distinct(distinct_key, filter=query)
                    cursor = self.collection.find(query, projection=projection, limit=limit, skip=skip)
                    data = [doc for doc in cursor if doc[distinct_key] in distinct_values]
            else:
                with self.rlock:
                    cursor = self.collection.find(query, projection=projection, limit=limit, skip=skip)
                    data = [doc for doc in cursor]
            cursor.batch_size = 10000  # 或根据实际情况调整 batch_size
            logger.info(
                f"{self.db_name}:{self.collection_name} 查询到 {len(data)} 条数据, 耗时: {time.perf_counter() - start_time:.6f} 秒")
            if explain:
                return cursor.explain()
            else:
                return data
        except pymongo.errors.ConnectionFailure as e:
            logger.error(f"连接数据库失败: {e}")
        except pymongo.errors.ExecutionTimeout as e:
            logger.error(f"查询超时: {e.details['errmsg']}")
        except pymongo.errors.OperationFailure as e:
            logger.error(f"查询数据失败: {e.details['errmsg']}")
        except pymongo.errors.PyMongoError as e:
            logger.error(f"Database query failed: {str(e)}")
        except Exception as e:
            logger.error(f"查询数据时发生未知错误: {e}")

    @logger.catch
    def batch_find_documents(self, query=None, projection: dict = None, batch_size: int = 1000, skip: int = 0):
        """
        分批查询文档，每次查询`batch_size`条数据。

        参数:
            query (dict): 查询条件，使用 MongoDB 查询语法。
            projection (dict, optional): 返回字段投影，仅返回指定的字段。默认返回所有字段。
            batch_size (int, optional): 每批次查询的文档数量。默认为1000。

        返回:
            Generator[List[dict]]: 生成器，逐批返回匹配查询条件的文档列表（字典形式）。
        """

        if query is None:
            query = {}
        while True:
            logger.info(f'开始查询第 {skip} 条到第 {batch_size + skip} 条的数据')
            docs_batch = self.find_documents(query=query, projection=projection, limit=batch_size, skip=skip)
            if not docs_batch:
                break
            yield docs_batch
            skip += batch_size

    @logger.catch
    def stream_find_documents(self, query: dict, projection: dict = None, batch_size: int = 1000, skip: int = 0):
        """
        流式查询文档，逐条返回匹配查询条件的文档。

        参数:
            query (dict): 查询条件，使用 MongoDB 查询语法。
            projection (dict, optional): 返回字段投影，仅返回指定的字段。默认返回所有字段。

        返回:
            Generator[dict]: 生成器，逐条返回匹配查询条件的文档（字典形式）。
        """
        if query is None:
            query = {}
        cursor = self.find_documents(query=query, projection=projection, limit=batch_size, skip=skip)
        cursor.batch_size = 10000  # 或根据实际情况调整 batch_size
        for doc in cursor:
            yield doc

    def export_data_to_excel(self,
                             output_file: str = None,
                             sheet_name: str = None,
                             check_columns: bool = True,
                             query: dict = None,
                             projection: dict = None,
                             limit: int = 0,
                             skip: int = 0,
                             distinct_key: str = None,
                             explain: bool = False
                             ):
        """
        将查询到的数据保存到Excel文件中。
        """
        if output_file is None:
            if self.db_name == '':
                logger.error("请选择MongoDB数据库")
                return
            else:
                output_file = self.db_name
        if not output_file.endswith('.xlsx') or not output_file.endswith('.xls'):
            output_file += '.xlsx'
        if sheet_name is None:
            if self.collection_name == '':
                logger.error(f"当前库为{self.db_name} 请选择集合")
                return
            else:
                sheet_name = self.collection_name
        try:
            infos = self.find_documents(query=query,
                                        projection=projection,
                                        limit=limit,
                                        skip=skip,
                                        distinct_key=distinct_key,
                                        explain=explain)
        except Exception as e:
            logger.error(f"查询数据时发生错误: {e}")
            return
        if not infos:
            logger.error("请先执行find_documents方法查询数据")
            return
        save_dict_list_to_excel(infos,
                                output_file=output_file,
                                sheet_name=sheet_name,
                                check_columns=check_columns)

    @logger.catch
    def save_dict_to_collection(self, dict, query_key: str = None):
        """
        根据传入的字典的某个key的值进行查询，判断是否已经存在相同记录，
        如果存在则更新，否则插入新记录。

        Args:
            dict (dict): 待保存或更新的数据字典。
            query_key (str, optional): 用于查询和判断重复的键名，默认为None。
                                      如果为None，则直接插入新记录，不进行查询和更新操作。
        """
        collection_info = f"{self.db_name}:{self.collection_name}"
        result = None
        _id = 0
        start_time = time.perf_counter()
        try:
            if query_key is None:
                with self.rlock:
                    result = self.collection.insert_one(dict)
                operation_result = f"1条数据成功保存到mongodb {collection_info}, 耗时: {time.perf_counter() - start_time:.6f} 秒"
                logger.info(f"{operation_result}, {dict}")
                _id = result.inserted_id
            elif isinstance(query_key, str) and query_key:
                query_value = dict[query_key]
                if query_value is None:
                    raise ValueError(f"{collection_info} 指定的查询键'{query_key}'在传入的记录数据中不存在")
                with self.rlock:
                    existing_document = self.collection.find_one({query_key: query_value}, projection={'_id': 0})
                if existing_document is not None:
                    # 更新已有记录
                    update_filter = {
                        query_key: query_value,
                    }
                    with self.rlock:
                        result = self.collection.update_one(update_filter, {'$set': dict}, upsert=True)
                    _id = result.upserted_id
                    operation_result = f"数据成功更新到mongodb {collection_info}, 耗时: {time.perf_counter() - start_time:.6f} 秒"
                    logger.info(f"{operation_result}, {dict}")
                else:
                    # 插入新记录
                    with self.rlock:
                        result = self.collection.insert_one(dict)
                    operation_result = f"1条数据成功保存到mongodb {collection_info}, 耗时: {time.perf_counter() - start_time:.6f} 秒"
                    logger.info(f"{operation_result}, {dict}")
                    _id = result.inserted_id
            if result:
                return _id
            else:
                logger.error("保存数据失败")
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    @logger.catch
    def save_dict_list_to_collection(self, dict_list, query_key: str = None):
        """
        将字典列表批量保存至 MongoDB。
        """

        start_time = time.perf_counter()
        collection_info = f"{self.db_name}:{self.collection_name}"

        try:
            if query_key is None:
                # 直接批量插入，不进行查询和更新
                with self.rlock:
                    result = self.collection.insert_many(dict_list)  # 批量插入
                logger.info(
                    f"{len(result.inserted_ids)} 条数据成功保存到mongodb {collection_info}, 耗时: {time.perf_counter() - start_time:.6f} 秒")
                return result.inserted_ids  # 返回插入的ID列表
            else:
                # 根据query_key查询出所有的数据的query_key存入list，
                with self.rlock:
                    existing_query_keys = set(
                        doc[query_key] for doc in self.collection.find({query_key: {"$exists": True}}, {query_key: 1}))
                # 分割新数据和已存在数据
                new_data = [data for data in dict_list if data[query_key] not in existing_query_keys]
                update_data = [data for data in dict_list if data[query_key] in existing_query_keys]
                # 插入新数据
                new_result = []
                if new_data:
                    with self.rlock:
                        new_result = self.collection.insert_many(new_data)
                    logger.info(
                        f"{len(new_result.inserted_ids)} 条新数据成功保存到mongodb {collection_info}, 耗时: {time.perf_counter() - start_time:.6f} 秒")
                # 更新已存在数据
                if update_data:
                    for data in update_data:
                        self.save_dict_to_collection(data, query_key)
                return new_result.inserted_ids if new_data else []  # 返回新数据的插入ID列表
        except pymongo.errors.BulkWriteError as e:
            logger.error(f"Failed to save data: {str(e.details)}")
            raise
        except Exception as e:
            logger.error(f"保存数据失败: {e}")

    def md5_encrypt(self, text):
        text = str(text)
        md5 = hashlib.md5()
        md5.update(text.encode('utf-8'))
        return md5.hexdigest()

    def delete_documents(self, query, recyclable=False):
        """
        删除满足条件的文档并根据需要将其移至回收站。
        :param query: 查询条件，字典格式
        :param recyclable: 是否将文档移至回收站，默认为False
        :return: 删除的文档数量
        """

        if self.collection is None:
            raise Exception("未选择集合")
        try:
            # 查找要删除的文档
            with self.rlock:
                documents_to_delete = list(self.collection.find(query))

            # 检查是否有文档需要删除
            if not documents_to_delete:
                logger.error("没有满足条件的文档需要删除。")
                return 0

            if recyclable:
                # 连接到回收站集合
                recycle_db = 'recycle_bin'
                recycle_collection_name = f"{self.db_name}:{self.collection_name}"
                recycle_bin_collection = self.client[recycle_db][recycle_collection_name]

                # 将要删除的文档移至回收站集合
                recycle_bin_collection.insert_many(documents_to_delete)
                logger.info(
                    f"已将 {len(documents_to_delete)} 个文档移至回收站 {recycle_db}.{recycle_collection_name}。")

            # 从原始集合中删除文档
            with self.rlock:
                result = self.collection.delete_many(query)
            logger.info(f"已删除 {result.deleted_count} 个文档。")

            return result.deleted_count
        except Exception as e:
            logger.error(f"删除文档时出错：{str(e)}")
            raise

    def close(self):
        """
        关闭与 MongoDB 的连接。
        """
        with self._instance_lock:
            try:
                if self.client:
                    self.client.close()
                    logger.info("MongoDB 连接已关闭")
            except Exception as e:
                logger.error(f"关闭MongoDB连接时发生错误: {e}")


# 使用示例
if __name__ == '__main__':
    db = MongoDB(host='localhost',
                 port=27017,
                 username=None,
                 password=None,
                 db_name='test',
                 collection_name='test')
    # 示例用法：
    # # 保存数据
    # info = {
    #     'name': '张三',
    #     'age': 20,
    #     'email': 'zhangsan@example.com'
    # }
    # db.save_dict_to_collection(info)

    # 根据query_key更新
    info = {
        'name': '张三',
        'age': 20,
        'email': 'zhangsan@qq.com'
    }
    db.save_dict_to_collection(info, query_key='name')
    with ThreadPoolExecutor(max_workers=10) as executor:
        for i in range(10):
            executor.submit(MongoDB(host='localhost',
                                    port=27017,
                                    username=None,
                                    password=None,
                                    db_name='test',
                                    collection_name='test').save_dict_to_collection, info, query_key='name')
    # 保存数据字典
    info = [
        {
            'name': '张三',
            'age': 20,
            'email': 'zhangsan@example.com'
        },
        {
            'name': '李四',
            'age': 25,
            'email': 'lisi@example.com'
        }
    ]
    db.save_dict_list_to_collection(info)
    # 查询集合所有数据
    db.find_documents()

    # 条件查询 查询 age 大于 18 的用户，并仅返回 name 和 email 字段，限制返回结果数量为 10
    db.find_documents(query={'age': {'$gt': 18}}, projection={'name': 1, 'email': 1}, limit=10)

    # 切换集合
    db.use(collection_name='test')
    # 删除文档
    db.delete_documents(query={'name': '张三'}, recyclable=True)
