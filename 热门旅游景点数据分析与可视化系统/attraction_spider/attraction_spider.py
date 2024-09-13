# ChromiumOptions 配置
import hashlib
import time
from concurrent.futures import ThreadPoolExecutor
from itertools import islice

from DrissionPage._configs.chromium_options import ChromiumOptions
from DrissionPage._pages.chromium_page import ChromiumPage
from loguru import logger

from models import RegionInformation, Attraction, Session, Review

# ChromiumOptions 配置
co = ChromiumOptions()
co.set_browser_path(r'C:\Users\18034\AppData\Local\Google\Chrome\Application\chrome.exe')
co.headless()  # 启用无头模式


def md5_encrypt(text):
    text = str(text)
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()


class CitySpider():
    def __init__(self, *args, **kwargs):
        start_url = kwargs.pop('start_url', 'https://www.mafengwo.cn/mdd/citylist/21536.html')
        self.page = ChromiumPage(co)
        self.session = Session()  # 创建数据库会话

        self.run_spider(start_url)

    def run_spider(self, url):
        self.page.get(url)
        self.parse_page()

        # 循环处理分页
        while self.page.ele('.pg-next _j_pageitem'):
            self.page.ele('.pg-next _j_pageitem').click()
            time.sleep(1)
            self.parse_page()

    def parse_page(self):
        for li in self.page.ele('#citylistlist').eles('t:li'):
            item = RegionInformation()
            item.url = li.ele('.img').ele('t:a').attr('href')
            item.region_id = item.url.split('/')[-1].replace('.html', '')
            name, item.pinyin = li.ele('.img').text.split('\n')
            item.name = name
            item.nums = li.ele('.caption').ele('.nums').text.replace('人去过', '')
            item.detail = li.ele('.caption').ele('.detail').text
            item.top3 = ', '.join(li.ele('.caption').ele('t:dd').texts())
            item.attraction = False  # 根据实际需求设置
            item.attraction_review = False  # 根据实际需求设置
            # 保存到数据库
            self.save_region_information(item)

    def save_region_information(self, item):
        try:
            # 这里需要根据实际情况检查是否已存在相同的记录
            existing_item = self.session.query(RegionInformation).filter_by(region_id=item.region_id).first()
            if existing_item is None:
                self.session.add(item)
                self.session.commit()
                print(f'Saved RegionInformation: {item.name}')
            else:
                print(f'RegionInformation already exists: {item.name}')
        except Exception as e:
            self.session.rollback()
            print(f'Error saving RegionInformation: {e}')


class AttractionSpider():
    def __init__(self, *args, **kwargs):
        self.city_id = kwargs.pop('city_id', None)
        self.page = ChromiumPage(co)
        self.session = Session()  # 创建数据库会话

        self.run_spider()

    def run_spider(self):
        url = f'https://www.mafengwo.cn/jd/{self.city_id}/gonglve.html'
        self.page.get(url)
        self._parse_page()

        # 循环处理分页
        while self.page.ele('.pi pg-next'):
            self.page.ele('.pi pg-next').click()
            time.sleep(1)
            self._parse_page()

    def _parse_page(self):
        for li in self.page.ele('.scenic-list clearfix').eles('t:li'):
            name = li.ele('t:a').attr('title')
            url = li.ele('t:a').attr('href')
            attraction_id = url.split('/')[-1].replace('.html', '')
            attraction = Attraction(
                attraction_id=f"{attraction_id}_{name}",
                name=name,
                url=url,
                city_id=self.city_id,
                detail_fetch=False,  # 初始设为未抓取详细信息
                price_list='',
                review_num=0,
                summary='',
                transport='',
                open_time='',
                time_reference='',
                ticket_info='',
                phone='',
                review_fetch=False
            )
            # 保存到数据库
            self.save_attraction(attraction)

    def save_attraction(self, attraction):
        try:
            # 这里需要根据实际情况检查是否已存在相同的记录
            existing_attraction = self.session.query(Attraction).filter_by(
                attraction_id=attraction.attraction_id).first()
            if existing_attraction is None:
                self.session.add(attraction)
                self.session.commit()
                print(f'Saved Attraction: {attraction.name}')
            else:
                print(f'Attraction already exists: {attraction.name}')
        except Exception as e:
            self.session.rollback()
            print(f'Error saving Attraction: {e}')


def translate_keys(data_dict):
    """
    将字典中的中文键替换为对应的英文键。

    :param data_dict: 需要处理的字典，包含中文键
    :return: 返回一个新的字典，键为英文
    """
    translation_map = {
        '交通': 'transport',
        '开放时间': 'open_time',
        '用时参考': 'time_reference',
        '门票': 'ticket_info',
        '电话': 'phone',
        '地址': 'address',
        '简介': 'introduction',
        '英文名称': 'en_name',
        '当地名称': 'cn_name',
    }

    # 创建一个新的字典来存储转换后的键值对
    new_dict = {}

    for key, value in data_dict.items():
        if key in translation_map:
            # 获取对应的英文键
            english_key = translation_map[key]

            # 仅在英文键不在原始字典中时，进行替换
            if english_key not in data_dict:
                new_dict[english_key] = value
        else:
            # 如果键不在 translation_map 中，直接添加原始键值对
            new_dict[key] = value

    return new_dict


def get_detail(page, info):
    def save_rev():
        for li in page.eles('.rev-item comment-item clearfix'):
            lv = li.ele('.user').text
            nick_name = li.ele('t:a@class=name').text
            user_url = li.ele('t:a').attr('href')
            star = li.ele('t:span@class:s-star').attr('class')
            rev_txt = li.ele('.rev-txt').text
            try:
                rev_img = [img.attr('src') for img in li.ele('.rev-img').eles('t:img')]
            except:
                logger.info('该条评论图片获取失败')
                rev_img = []
            rev_time = li.ele('.info clearfix').ele('.time').text
            rev = {
                'attraction_id': attraction_id,
                'lv': lv,
                'nick_name': nick_name,
                'user_url': user_url,
                'rev_txt': rev_txt,
                'rev_img': rev_img,
                'rev_time': rev_time,
                'star': star,
            }
            rev['review_id'] = md5_encrypt(rev)
            try:
                new_review = Review(
                    review_id=rev.get('review_id', ''),
                    attraction_id=rev.get('attraction_id', ''),
                    nick_name=rev.get('nick_name', ''),
                    user_url=rev.get('user_url', ''),
                    rev_txt=rev.get('rev_txt', ''),
                    rev_img=','.join(rev.get('rev_img', '')),
                    rev_time=rev.get('rev_time', ''),
                    star=rev.get('star', ''),
                )
                if not session.query(Review).filter(Review.review_id == new_review['review_id']).first():
                    session.merge(new_review)
                    session.commit()  # 每插入一条记录后提交事务
                    print(f"Review {new_review['review_id']} saved successfully.")
            except Exception as e:
                session.rollback()  # 出错时回滚事务
                print(f"Error saving review {rev['review_id']}: {e}")

    def parse():
        info['review_num'] = int(
            str(page.ele('@data-scroll=commentlist').ele('t:span').text).replace('条）', '').replace('（', ''))
        detail_ele = page.ele('.mod mod-detail')
        try:
            info['summary'] = detail_ele.ele('.summary').text
        except:
            info['summary'] = '暂无'
        try:
            for li in detail_ele.ele('.baseinfo clearfix').eles('t:li'):
                info[li.ele('.label').text] = li.ele('.content').text
        except:
            logger.warning(f'{info['url']} 景点基本信息获取失败')
        try:
            for dl in detail_ele.eles('t:dl'):
                info[dl.ele('t:dt').text] = dl.ele('t:dd').text
        except:
            logger.warning(f'{info['url']} 景点详细信息获取失败')
        try:
            info['address'] = page.ele('.mod mod-location mfw-acc-hide').ele('.mhd').ele('t:p').text
        except:
            logger.warning(f'{info['url']} 景点地址获取失败')
        price_list = []
        if page.ele('.mod mod-promo', timeout=5):
            for price_ele in page.ele('.mod mod-promo').eles('t:tr'):
                price = {
                    'type': price_ele.ele('.type').text,
                    'pro': price_ele.ele('.pro').text,
                    'price': price_ele.ele('.price').text,
                }
                price_list.append(price)
        info['price_list'] = price_list

        translate_keys(info)

    def save_attraction(attraction):
        try:
            # 这里需要根据实际情况检查是否已存在相同的记录
            existing_attraction = session.query(Attraction).filter_by(
                attraction_id=attraction.attraction_id).first()
            if existing_attraction is None:
                session.merge(attraction)
                session.commit()
                print(f'Saved Attraction: {attraction.name}')
            else:
                print(f'Attraction already exists: {attraction.name}')
        except Exception as e:
            session.rollback()
            print(f'Error saving Attraction: {e}')

    session = Session()

    if 'review_fetch' in info and info['review_fetch']:
        return
    attraction_id = info['url'].split('/')[-1].replace('.html', '')
    page.get(info['url'])
    try:
        if 'detail_fetch' in info and info['detail_fetch'] == False:
            parse()
            info['detail_fetch'] = True
            attraction = Attraction(
                attraction_id=info['attraction_id'],
                name=info.get('name', ''),
                url=info.get('url', ''),
                city_id=info.get('city_id', ''),
                detail_fetch=info['review_fetch'] if 'review_fetch' in info and info[
                    'review_fetch'] != '' else False,  # 默认值为 False
                price_list=str(info.get('price_list', '')),
                review_num=info.get('review_num', 0),  # 默认值为 0
                summary=info.get('summary', ''),
                transport=info.get('交通', ''),
                open_time=info.get('开放时间', ''),
                time_reference=info.get('用时参考', ''),
                ticket_info=info.get('门票', ''),
                phone=info.get('电话', ''),
                address=info.get('address', ''),
                introduction=info.get('简介', ''),
                en_name=info.get('英文名称', ''),
                cn_name=info.get('当地名称', ''),
                review_fetch=info.get('review_fetch', False)  # 默认值为 False
            )
            save_attraction(attraction)

        save_rev()
        while page.ele('.pi pg-next'):
            page.ele('.pi pg-next').click()
            time.sleep(1)
            save_rev()
        info['review_fetch'] = True
        attraction = Attraction(
            attraction_id=info['attraction_id'],
            name=info.get('name', ''),
            url=info.get('url', ''),
            city_id=info.get('city_id', ''),
            detail_fetch=info['review_fetch'] if 'review_fetch' in info and info[
                'review_fetch'] != '' else False,  # 默认值为 False
            price_list=str(info.get('price_list', '')),
            review_num=info.get('review_num', 0),  # 默认值为 0
            summary=info.get('summary', ''),
            transport=info.get('交通', ''),
            open_time=info.get('开放时间', ''),
            time_reference=info.get('用时参考', ''),
            ticket_info=info.get('门票', ''),
            phone=info.get('电话', ''),
            address=info.get('address', ''),
            introduction=info.get('简介', ''),
            en_name=info.get('英文名称', ''),
            cn_name=info.get('当地名称', ''),
            review_fetch=info.get('review_fetch', False)  # 默认值为 False
        )
        save_attraction(attraction)

        # 保存到数据库
    except Exception as e:
        logger.info(f'{info['url']} 爬取失败 {e}')


def multi_thread(infos):
    max_workers = len(infos)
    page = ChromiumPage(co)
    page_list = []
    tabs = []
    for index in range(0, max_workers):
        logger.info(f'开始打开第{index}个')
        if index == 0:
            tab = page.get_tab(0)
        else:
            tab = page.new_tab()
        tab.get(infos[index]['url'])
        page_tab = page.get_tab(tab)
        page_list.append((page_tab, infos[index]))
        tabs.append(tab)
        time.sleep(0.5)
        logger.info(f'打开了第{index}个')
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        tasks = [
            executor.submit(get_detail, page_obj, info)
            for page_obj, info in page_list
        ]
        for task in tasks:
            task.result()
    page.close_tabs(tabs)


def chunked_iterable(iterable, size):
    iterator = iter(iterable)
    while chunk := list(islice(iterator, size)):
        yield chunk


def run_city_spider(start_url=None):
    CitySpider(start_url=start_url)


def run_attraction_spider(city_id):
    AttractionSpider(city_id=city_id)


def run_review_spider(nums):
    session = Session()

    # 查询所有城市，并按人数进行排序，取前50个
    cities = session.query(RegionInformation).order_by(RegionInformation.nums).limit(100).all()

    for city in cities:
        # 查询该城市的景点信息
        db_infos = session.query(Attraction).filter_by(city_id=city.region_id).all()

        # 根据 review_num 进行排序，取 review_num 最大的前10个
        infos = sorted(db_infos, key=lambda x: int(x.review_num if x.review_num else 0), reverse=True)
        infos_dict_list = [info.__dict__ for info in infos]
        for info_dict in infos_dict_list:
            info_dict.pop('_sa_instance_state', None)

        shou_infos = []
        for info in infos_dict_list[:10]:
            if info.get('review_fetch'):  # 如果已经抓取过评论，跳过
                continue
            else:
                shou_infos.append(info)

        if len(shou_infos) == 0:
            continue

        # 使用多线程处理评论抓取任务
        for chunk in chunked_iterable(shou_infos, 10):
            multi_thread(chunk)

    # 关闭数据库会话
    session.close()


def main():
    # 首先运行 CitySpider 获取城市信息
    run_city_spider('https://www.mafengwo.cn/mdd/citylist/21536.html')

    # 从数据库中获取所有城市ID并运行 AttractionSpider
    session = Session()
    city_ids = session.query(RegionInformation.region_id).all()
    session.close()
    for city_id in city_ids:
        run_attraction_spider(city_id[0])  # city_id 是一个元组，所以需要取 [0]


if __name__ == '__main__':
    # main()
    run_review_spider(100)
