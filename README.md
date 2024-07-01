# Python Code Utilities

This repository contains various utility classes and functions to facilitate working with different technologies such as MongoDB, message queues, Excel, text files, and MySQL. Each utility class is designed to provide simple and efficient ways to perform common operations.

## Table of Contents

- [MongoDB](#mongodb_tool)


## MongoDB Util

The MongoDB util provide convenient methods to interact with MongoDB databases. These include connecting to the database, performing CRUD operations, and handling collections.

### Features
- Connect to MongoDB
- Create, read, update, and delete documents
- Handle collections

### Usage
```python
# 使用示例
if __name__ == '__main__':
    db = MongoDB(host='localhost',
                 port=27017,
                 username=None,
                 password=None,
                 db_name='test',
                 collection_name='test')
    # 示例用法：
    # 保存数据
    info = {
        'name': '张三',
        'age': 20,
        'email': 'zhangsan@example.com'
    }
    db.save_dict_to_collection(info)

    # 根据query_key更新
    info = {
        'name': '张三',
        'age': 20,
        'email': 'zhangsan@qq.com'
    }
    db.save_dict_to_collection(info, query_key='name')

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
    db.use(collection_name='test1')

