# -*- coding: utf-8 -*-

from attraction_spider import translate_keys
from models import RegionInformation, Session, Attraction, Review
from mongodb_tool import MongoDB


def migrate_attractions(session, attraction_c):
    for attraction in attraction_c.find_documents():

        attraction['attraction_id'] = str(int(attraction['url'].split('/')[-1].replace('.html', ''))) + '_' + str(
            attraction['name'])
        attraction.pop('_id')
        new_attraction = Attraction(
            attraction_id=attraction['attraction_id'],
            name=attraction.get('name', ''),
            url=attraction.get('url', ''),
            city_id=attraction.get('city_id', ''),
            detail_fetch=attraction['review_fetch'] if 'review_fetch' in attraction and attraction[
                'review_fetch'] != '' else False,  # 默认值为 False
            price_list=str(attraction.get('price_list', '')),
            review_num=attraction.get('review_num', 0),  # 默认值为 0
            summary=attraction.get('summary', ''),
            transport=attraction.get('交通', ''),
            open_time=attraction.get('开放时间', ''),
            time_reference=attraction.get('用时参考', ''),
            ticket_info=attraction.get('门票', ''),
            phone=attraction.get('电话', ''),
            address=attraction.get('address', ''),
            introduction=attraction.get('简介', ''),
            en_name=attraction.get('英文名称', ''),
            cn_name=attraction.get('当地名称', ''),
            review_fetch=attraction.get('review_fetch', False)  # 默认值为 False
        )
        if not session.query(Attraction).filter(Attraction.attraction_id == attraction['attraction_id']).first():
            session.merge(new_attraction)
            session.commit()  # 每插入一条记录后提交事务
            print(f"Attraction {attraction['attraction_id']} saved successfully.")


def migrate_reviews(session, review_c):
    for review in review_c.find_documents():
        try:
            review['review_id'] = review['_id']
            review.pop('_id')
            new_review = Review(
                review_id=review.get('review_id', ''),
                attraction_id=review.get('attraction_id', ''),
                nick_name=review.get('nick_name', ''),
                user_url=review.get('user_url', ''),
                rev_txt=review.get('rev_txt', ''),
                rev_img=','.join(review.get('rev_img', '')),
                rev_time=review.get('rev_time', ''),
                star=review.get('star', ''),
            )
            if not session.query(Review).filter(Review.review_id == review['review_id']).first():
                session.merge(new_review)
                session.commit()  # 每插入一条记录后提交事务
                print(f"Review {review['review_id']} saved successfully.")
        except Exception as e:
            session.rollback()  # 出错时回滚事务
            print(f"Error saving review {review['review_id']}: {e}")


if __name__ == '__main__':
    db = MongoDB(db_name='mafengwo')
    city_c = db['city']
    attraction_c = db['attraction']
    review_c = db['review']

    session = Session()

    migrate_attractions(session, attraction_c)
    # migrate_reviews(session, review_c)

    session.close()  # 确保 session 关闭
