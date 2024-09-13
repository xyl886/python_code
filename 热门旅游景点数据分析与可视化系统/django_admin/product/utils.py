import MySQLdb
import pandas as pd
from loguru import logger
from snownlp import SnowNLP
import os
import json
from django.conf import settings

# 数据库连接参数
DB_HOST = 'localhost'
DB_USER = 'root'
DB_PASSWORD = 'root'
DB_NAME = 'attraction_admin'


def analyze_and_save_sentiment(reviews):
    # 连接数据库
    db = MySQLdb.connect(DB_HOST, DB_USER, DB_PASSWORD, DB_NAME, charset='utf8')
    cursor = db.cursor()

    for review in reviews:
        s = SnowNLP(review['review'])
        sentiment_score = s.sentiments
        sentiment_label = 'positive' if sentiment_score > 0.5 else 'negative'

        # 插入情感分析结果到 ReviewSentiment 表
        insert_sql = """
        INSERT INTO review_sentiment (sentiment_text, sentiment, sentiment_score)
        VALUES (%s, %s, %s)
        """
        cursor.execute(insert_sql, (review['review'], sentiment_label, sentiment_score))

        # 提交当前事务
        db.commit()

        print(f"Review ID analyzed: {sentiment_label} ({sentiment_score})")

    # 关闭数据库连接
    cursor.close()
    db.close()
    print("情感分析已完成并入库。")


def get_or_generate_opts(file_name: str, generate_opts_func):
    """
    读取静态 JSON 文件的 opts，若文件不存在则生成 opts 并保存到该文件中。

    :param file_name: 静态文件名，包含路径
    :param generate_opts_func: 生成 opts 的函数
    :return: 返回 opts (字典形式)
    """
    file_path = os.path.join(settings.BASE_DIR, 'static', 'charts', file_name)

    # 如果文件存在，直接读取并返回
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            opts = json.load(f)
        return opts

    # 如果文件不存在，调用生成函数获取 opts，并保存到文件中
    opts = generate_opts_func()

    # 将 opts 写入到 JSON 文件中
    os.makedirs(os.path.dirname(file_path), exist_ok=True)  # 确保目录存在
    with open(file_path, 'w', encoding='utf-8') as f:
        if isinstance(opts, str):
            opts = json.loads(opts)
        json.dump(opts, f, ensure_ascii=False, indent=4)
    logger.info(type(opts))
    return json.loads(opts) if isinstance(opts, str) else opts


if __name__ == "__main__":
    # 读取ChnSentiCorp_htl_all.csv文件
    reviews = pd.read_csv(
        r'D:\soft\pythonProject\yfcst_python\热门旅游景点数据分析与可视化系统\django_admin\data\ChnSentiCorp_htl_all.csv')
    reviews = reviews.to_dict('records')
    # 从数据库查询
    analyze_and_save_sentiment(reviews)
