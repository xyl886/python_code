# -*- coding: utf-8 -*-
import ast
import json
from collections import defaultdict, Counter

from loguru import logger
from pyecharts.charts import Bar, Line, Page, Map, Pie, Scatter, HeatMap
from pyecharts.commons.utils import JsCode
from pyecharts.options import TitleOpts, AxisOpts, ToolboxOpts, LabelOpts, VisualMapOpts, InitOpts, LegendOpts, \
    DataZoomOpts, TooltipOpts
from snownlp import SnowNLP

from .models import Review, RegionInformation, Attraction


def gen_analyze_hot_opts():
    # 从数据库获取城市名称和对应的nums数据
    region_data = RegionInformation.objects.filter(nums__isnull=False).values('name', 'nums')

    # 将数据按nums进行升序排序
    region_data = region_data.order_by('-nums')

    # 提取城市名称和对应的nums值
    city_names = [item['name'] for item in region_data]
    city_nums = [item['nums'] for item in region_data]

    # 创建柱状图
    bar_chart = (
        Bar()
        .add_xaxis(city_names)
        .add_yaxis("Nums", city_nums)
        .set_global_opts(
            title_opts=TitleOpts(title="城市热度可视化", subtitle="各城市的访问人数统计"),
            xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=-45)),
            yaxis_opts=AxisOpts(name="Nums"),
            datazoom_opts=[DataZoomOpts(type_="slider", range_start=0, range_end=15)],
        )
    )

    # 返回可视化图表的JSON
    return bar_chart.dump_options_with_quotes()


def generate_price_opts():
    # 查询所有景点和价格信息
    attractions = Attraction.objects.all()

    # 用于存储每个城市的价格类型和对应价格
    city_price_data = defaultdict(list)
    price_type_count = defaultdict(int)

    # 遍历每个景点，解析价格信息
    for attraction in attractions:
        city_id = attraction.city_id  # 获取景点所属城市ID
        if city_id:
            try:
                city_name = RegionInformation.objects.get(region_id=str(city_id)).name  # 获取城市名称
            except:
                continue
        else:
            continue
        if attraction.price_list:
            price_list = ast.literal_eval(attraction.price_list)
            if price_list:
                for price_info in price_list[1:]:
                    price_type = price_info['type']
                    try:
                        price = float(price_info['price'].replace('￥', '').replace('起', ''))
                    except:
                        price = None
                    city_price_data[city_name].append((price_type, price))
                    price_type_count[(price_type, city_name)] += 1

    # 准备第一个热力图（城市和价格类型的数量统计）
    city_list = list(set([city for city, prices in city_price_data.items() for _, _ in prices]))
    price_type_list = list(set([price_type for city, prices in city_price_data.items() for price_type, _ in prices]))

    heatmap_data_city_price_type = []
    for city in city_list:
        for price_type in price_type_list:
            count = price_type_count.get((price_type, city), 0)
            heatmap_data_city_price_type.append([city_list.index(city), price_type_list.index(price_type), count])

    # 构建第一个热力图
    heatmap_city_price_type = HeatMap(init_opts=InitOpts(width="1000px", height="600px"))
    heatmap_city_price_type.add_xaxis(city_list)
    heatmap_city_price_type.add_yaxis("Price Type", price_type_list, heatmap_data_city_price_type)
    heatmap_city_price_type.set_global_opts(
        title_opts=TitleOpts(title="按城市分布的价格类型"),
        xaxis_opts=AxisOpts(type_="category", name="City", axislabel_opts=LabelOpts(rotate=45)),
        yaxis_opts=AxisOpts(name="Price Type"),
        visualmap_opts=VisualMapOpts(min_=0, max_=max([item[2] for item in heatmap_data_city_price_type])),
        datazoom_opts=[DataZoomOpts(type_="slider", range_start=25, range_end=75)],
    )

    # 准备第二个热力图（价格区间和价格类型的数量统计）
    price_bins = [0, 50, 100, 200, 300, 400, 500, 600, 700, 800, 900, 1000]
    price_type_count_bins = defaultdict(int)
    for city, prices in city_price_data.items():
        for price_type, price_value in prices:
            if price_value is not None:
                for i in range(len(price_bins) - 1):
                    if price_bins[i] <= price_value < price_bins[i + 1]:
                        price_type_count_bins[(price_type, i)] += 1
                        break

    heatmap_data_price_type_price = []
    for price_type in price_type_list:
        for i in range(len(price_bins) - 1):
            count = price_type_count_bins.get((price_type, i), 0)
            heatmap_data_price_type_price.append([i, price_type_list.index(price_type), count])

    # 构建第二个热力图
    heatmap_price_type_price = HeatMap(init_opts=InitOpts(width="1000px", height="600px"))
    heatmap_price_type_price.add_xaxis([f"{price_bins[i]}-{price_bins[i + 1]}" for i in range(len(price_bins) - 1)])
    heatmap_price_type_price.add_yaxis("价格类型", price_type_list, heatmap_data_price_type_price)
    heatmap_price_type_price.set_global_opts(
        title_opts=TitleOpts(title="按价格分布的价格类型"),
        xaxis_opts=AxisOpts(type_="category", name="价格区间"),
        yaxis_opts=AxisOpts(name="价格类型"),
        visualmap_opts=VisualMapOpts(min_=0, max_=max([item[2] for item in heatmap_data_price_type_price])),
    )

    # 返回两个热力图的 JSON 数据，便于前端渲染
    return {
        'city_price_type_heatmap': json.loads(heatmap_city_price_type.dump_options_with_quotes()),
        'price_type_price_heatmap': json.loads(heatmap_price_type_price.dump_options_with_quotes())
    }


def generate_review_opts():
    # 查询所有景点和城市
    attractions = Attraction.objects.all()
    regions = RegionInformation.objects.all()

    # 创建字典存储每个景点的评论分析
    review_data = defaultdict(lambda: {"positive": 0, "negative": 0})

    # 查询所有评论
    reviews = Review.objects.all()

    # 统计每个景点的正面和负面评论数
    for review in reviews:
        if str(review.sentiment) != 'positive' and str(review.sentiment) != 'negative' and str(
                review.sentiment) != 'unknown':
            if review.rev_txt != '':
                s = SnowNLP(review.rev_txt)
                sentiment_score = s.sentiments
                review.sentiment = 'positive' if sentiment_score > 0.5 else 'negative'
            else:
                review.sentiment = 'unknown'
            review.save()
            logger.info(review.sentiment + '  ' + str(review.review_id))
        if str(review.sentiment) == 'positive':
            review_data[review.attraction_id]["positive"] += 1
        elif str(review.sentiment) == 'negative':
            review_data[review.attraction_id]["negative"] += 1
    # 1. 按城市统计景点评价数量
    city_names = []
    attraction_counts = []
    for region in regions:
        city_attractions = attractions.filter(city_id=int(region.region_id))
        city_names.append(region.name)
        attraction_counts.append(city_attractions.count())
    bar_city = (
        Bar()
        .add_xaxis(city_names)
        .add_yaxis("景点数量", attraction_counts)
        .set_global_opts(
            title_opts=TitleOpts(title="每个城市的景点数量"),
            xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=-15)),
            yaxis_opts=AxisOpts(name="景点"),
            # 默认30-50%的缩放
            datazoom_opts=DataZoomOpts(range_start=30, range_end=50),
        )
    )

    # 2. 每个景点的正面和负面评论柱状图
    attraction_names = []
    positive_counts = []
    negative_counts = []

    for attraction in attractions:
        attraction_names.append(attraction.name)
        attraction_id = str(attraction.attraction_id).split('_')[0]
        positive_counts.append(review_data[attraction_id]["positive"])
        negative_counts.append(review_data[attraction_id]["negative"])
    # logger.info(review_data)
    logger.info(positive_counts)
    logger.info(negative_counts)
    # 将所有数据组合在一起，并计算每个景点的评论总数
    combined_data = [
        (name, positive, negative, positive + negative)
        for name, positive, negative in zip(attraction_names, positive_counts, negative_counts)
    ]
    sorted_data = sorted(combined_data, key=lambda x: x[3], reverse=True)
    top_1000_data = sorted_data[:1000]
    attraction_names, positive_counts, negative_counts, _ = zip(*top_1000_data)

    bar_attraction = (
        Bar()
        .add_xaxis(list(attraction_names))
        .add_yaxis("积极评论", list(positive_counts), stack="stack1")
        .add_yaxis("负面评论", list(negative_counts), stack="stack1")
        .set_global_opts(
            title_opts=TitleOpts(title="景点点评情绪发布"),
            xaxis_opts=AxisOpts(axislabel_opts=LabelOpts(rotate=-15)),
            yaxis_opts=AxisOpts(name="点评数量"),
            datazoom_opts=DataZoomOpts(range_start=45, range_end=50),
        )
    )

    # 3. 正面评论和负面评论的总体趋势折线图
    total_positive = sum(positive_counts)
    total_negative = sum(negative_counts)
    logger.info(total_positive)
    logger.info(total_negative)
    line_trend = (
        Line()
        .add_xaxis(["积极", "消极"])
        .add_yaxis("点评情感趋势", [total_positive, total_negative])
        .set_global_opts(
            title_opts=TitleOpts(title="整体情绪趋势"),
            xaxis_opts=AxisOpts(name="Sentiment"),
            yaxis_opts=AxisOpts(name="Count"),
        )
    )
    # 使用 dump_options_with_quotes 获取图表配置的 JSON 字符串
    attraction_opts = json.loads(bar_attraction.dump_options_with_quotes())  # 转换为字典
    trend_opts = json.loads(line_trend.dump_options_with_quotes())  # 转换为字典
    city_opts = json.loads(bar_city.dump_options_with_quotes())  # 转换为字典

    # 返回包含所有图表 opts 的字典
    return {
        "city_chart": city_opts,
        "attraction_chart": attraction_opts,
        "trend_chart": trend_opts
    }


def gen_analyze_city_attraction_distribution():
    # 获取所有城市信息和其景点数量
    cities = RegionInformation.objects.all()
    city_attraction_count = defaultdict(int)

    # 统计每个城市的热门景点数量
    for city in cities:
        city_id = int(city.region_id)
        attraction_count = Attraction.objects.filter(city_id=city_id).count()
        city_attraction_count[city.name] += attraction_count

    # 将城市和景点数量转换为 pyecharts 的数据格式
    city_attraction_data = [(city, count) for city, count in city_attraction_count.items()]

    # 排序，找出景点最多的城市
    city_attraction_data.sort(key=lambda x: x[1], reverse=True)
    # 创建地图
    map_chart = Map(init_opts=InitOpts(width="1400px", height="800px"))
    map_chart.add(
        "景点数量",
        data_pair=city_attraction_data,
        maptype="china",
        is_map_symbol_show=True,

    )

    # 设置颜色深浅（基于景点数量）
    map_chart.set_global_opts(
        title_opts=TitleOpts(title="各城市热门景点数量分布"),
        visualmap_opts=VisualMapOpts(
            max_=max(city_attraction_count.values()),
            is_piecewise=True,
            pieces=[
                {"min": 100, "label": ">100", "color": "#7f1100"},
                {"min": 50, "max": 99, "label": "50-99", "color": "#ff5428"},
                {"min": 20, "max": 49, "label": "20-49", "color": "#ff8c71"},
                {"min": 10, "max": 19, "label": "10-19", "color": "#ffd768"},
                {"min": 1, "max": 9, "label": "1-9", "color": "#efeeb7"},
            ],
        ),
    )
    return map_chart.dump_options_with_quotes()


# 假设你的停用词文件在项目根目录下
STOPWORDS_PATH = 'D:\soft\pythonProject\yfcst_python\热门旅游景点数据分析与可视化系统\django_admin\data\stopwords.txt'


def load_stopwords(file_path=STOPWORDS_PATH):
    stopwords = set()
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            stopwords.add(line.strip())
    return stopwords


def filter_stopwords(text, stopwords):
    import jieba.analyse

    words = jieba.cut(text)
    filtered_words = [word for word in words if word not in stopwords]
    return ' '.join(filtered_words)


def gen_analyze_attraction_introduction():
    import jieba.analyse
    # 加载停用词
    stopwords = load_stopwords()

    # 查询review_num大于0的景点
    attractions = Attraction.objects.all()

    # 统计景点简介中的关键词
    type_counter = Counter()
    for attraction in attractions:
        introduction = attraction.introduction + ' ' + attraction.summary
        if introduction:
            # 使用jieba提取关键词并排除停用词
            filtered_introduction = filter_stopwords(introduction, stopwords)
            keywords = jieba.analyse.extract_tags(filtered_introduction, topK=5)
            type_counter.update(keywords)
    # 设定词频的最小阈值
    min_frequency = 30  # 你可以根据需求调整这个值

    # 过滤掉词频小于 min_frequency 的关键词，并归类为“其他”
    filtered_type_counter = {}
    for keyword, freq in type_counter.items():
        if freq >= min_frequency and keyword != '暂无':
            filtered_type_counter[keyword] = freq

    # 创建饼图展示关键词分布
    chart = Pie(init_opts=InitOpts(width="1400px", height="600px"))
    chart.add(
        "",
        [list(z) for z in zip(filtered_type_counter.keys(), filtered_type_counter.values())]
    )
    chart.set_global_opts(
        legend_opts=LegendOpts(orient="vertical", pos_top="15%", pos_left="0%"),
    )
    chart.set_series_opts(label_opts=LabelOpts(formatter="{b}: {c}"))
    return chart.dump_options_with_quotes()
