# -*- coding: utf-8 -*-

from urllib.parse import urljoin, urlparse

# website_spider.py
import scrapy

from html_deep_spider.items import ImageItem, TextItem
from scrapy import Selector


class WebsiteSpider(scrapy.Spider):
    name = "website_spider"

    def __init__(self, website, crawl_type, depth, page_limit, *args, **kwargs):
        super(WebsiteSpider, self).__init__(*args, **kwargs)
        self.website = website
        self.crawl_type = crawl_type
        self.depth = depth
        self.page_limit = page_limit
        self.seen_urls = set()
        self.sequence_num = 1
        self.base_website_list = self.get_domain_segments(website)
        self.use_custom_cookies = True
        self.use_custom_headers = True

    @staticmethod
    def get_domain_segments(url):  # 获取域名
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        parts = domain.split('.')
        if len(parts) > 2:
            segments = parts[1:-1]
        else:
            segments = parts
        return segments

    def start_requests(self):
        yield scrapy.Request(encoding='utf-8', url=self.website, callback=self.parse, meta={'current_depth': 0})

    def parse(self, response):
        current_depth = response.meta['current_depth']
        if int(current_depth) > int(self.depth) or self.sequence_num >= int(self.page_limit):
            return

        self.seen_urls.add(response.url)
        links = response.xpath('//a[@href] | //p[@href]')  # 获取所有链接
        # 请求,爬取里面链接的文本，生成TextItem
        if self.crawl_type == "text":
            for paragraph in links:
                href = paragraph.xpath('.//@href').get()
                if not href or 'javascript:' in href:
                    continue
                paragraph_url = urljoin(response.url, href)
                if paragraph_url in self.seen_urls:
                    continue
                # 先移除 <style> 和 <script> 标签及其内容
                cleaned_response = Selector(response).xpath('//body//*[not(self::style or self::script)]')
                # 提取文本
                text = cleaned_response.xpath('.//text()').getall()
                # 合并文本并去除多余的空白字符
                text_content = ' '.join(text).strip()
                info = TextItem(
                    sequence_num=self.sequence_num,
                    crawl_url=paragraph_url,
                    referer=response.url,
                    internal_or_external="内链" if any(
                        base in paragraph_url for base in self.base_website_list) else "外链",
                    text_content=text_content,
                    depth=current_depth
                )
                self.sequence_num += 1
                yield info
        # 获取图片，生成ImageItem
        elif self.crawl_type == "image":
            images = response.xpath('//img[@src]')
            for img in images:
                img_url = img.xpath('.//@src').get()
                if not img_url or 'javascript:' in img_url:
                    continue
                img_url = urljoin(response.url, img_url)
                if img_url in self.seen_urls:
                    continue

                info = ImageItem(
                    sequence_num=self.sequence_num,
                    image_url=img_url,
                    referer=response.request.headers.get('Referer', self.website).decode(),
                    internal_or_external="内链" if any(base in img_url for base in self.base_website_list) else "外链",
                    depth=current_depth
                )
                self.sequence_num += 1
                self.seen_urls.add(img_url)
                yield info

        next_depth = current_depth + 1
        for link in links:
            next_url = urljoin(response.url, link.xpath('.//@href').get())
            if next_url not in self.seen_urls:
                yield scrapy.Request(url=next_url, callback=self.parse, meta={'current_depth': next_depth})  # 递归
