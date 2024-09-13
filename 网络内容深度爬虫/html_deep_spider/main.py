from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
from bs4 import BeautifulSoup
from loguru import logger

cookies = {
    'UN': 'qq_56972807',
    'historyList-new': '%5B%5D',
    'Hm_ct_6bcd52f51e9b3dce32bec4a3997715ac': '6525*1*10_36616570530-1688389729729-846268!5744*1*qq_56972807',
    'Hm_lvt_e5ef47b9f471504959267fd614d579cd': '1697025579,1699360803',
    '__gpi': 'UID=00000c81aa297457:T=1699364409:RT=1699364409:S=ALNI_Ma4yDkzzZayCNUc0pAjUcxfoK9Whg',
    '__gads': 'ID=287bf11b90b4c7b3-226a780e7fe5003a:T=1699364409:RT=1699364416:S=ALNI_Magm_hduSpSLLbUNMmaDCV_r-6FLQ',
    'Hm_up_6bcd52f51e9b3dce32bec4a3997715ac': '%7B%22islogin%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isonline%22%3A%7B%22value%22%3A%221%22%2C%22scope%22%3A1%7D%2C%22isvip%22%3A%7B%22value%22%3A%220%22%2C%22scope%22%3A1%7D%2C%22uid_%22%3A%7B%22value%22%3A%22qq_56972807%22%2C%22scope%22%3A1%7D%7D',
    '_ga': 'GA1.1.1833957224.1708670809',
    '_ga_7W1N0GEY1P': 'GS1.1.1708670809.1.1.1708670825.44.0.0',
    'fpv': 'f4cdc46531e600eb42683af2b49ecad4',
    'cf_clearance': 'aOPLSOfRB3mRrx3VRsR2Z7.WNIby5aIxen7ozyBK8pk-1713946529-1.0.1.1-TB8oIoLUKAlzPA_bKECbh9HCaxA93y2AcLDTs.eX2cq_LnGFt.ZG_FTrMjRvjgT7GJZ6YGsoo8Wx.jHjr3gMBg',
    'c_ins_prid': '-',
    'c_ins_rid': '1715000959066_646372',
    'c_ins_fref': 'https://www.csdn.net/',
    'c_ins_fpage': '/index.html',
    'c_ins_um': '-',
    'chat-version': '2.1.1',
    'Hm_lvt_6bcd52f51e9b3dce32bec4a3997715ac': '1715447990,1715583201,1715858129,1715929292',
    'UserName': 'qq_56972807',
    'UserInfo': 'a70e44ca17834eb1bd76bca0ea46ba53',
    'UserToken': 'a70e44ca17834eb1bd76bca0ea46ba53',
    'UserNick': 'xyl866',
    'AU': '0DF',
    'BT': '1719761989185',
    'p_uid': 'U010000',
    'ssxmod_itna': 'iqmxyGi=qDqGqY5GHqiQRfE4hIhx0K45veoNQD/fQxnqD=GFDK40oEBx5Ko4K+eNQm3YGO07G203QD6eevWifWoPqL7mDB3DEx06+e0Db4GGfxBYDQxAYDGDDp8Dj4ibDYfzODjBItzZCq=D3qDwDB=DmqG2Kn=Dm4DfDDdy8DeKCT=D4qDBDGUqMWiDG4Gf+wxD0whFV2x97DGWCMtUbC0PVjAMAR=DjqGgDBLeKtuto97KSMtzEb9WiM0qxBQD7u2Sl8rDCoUVRLQOMOGWY7DoBOeob7p+fY+K34mnoAYKSGGBTB++lGoi7etGQHG5KmWKBY5WDD==',
    'ssxmod_itna2': 'iqmxyGi=qDqGqY5GHqiQRfE4hIhx0K45veoNG9iuDxBL+x7KqGa+hEOko+Ex8ErUx6lrBv27eYiCiNGoAxRa23V+x+Fe+bVaoq6NeyCmh6EGfSM8neea963hh/fEt5wFCyWzFpppdup2ldv39hIRC0iw3uGqLRpxiQv9Qff9mQ0FRj0=vnrADfTvmj+hbqf9bL5VCuK8YBx+b=d+Sru+Rov798REU=3+fuAEYQy+2R5A86YwlxLEtB554UASAU4zd3Wj8uv2WUS3bFb5Vtgz3FbrO97od9gn1kZ8QaQv6n0X2vKX=I7yBjbxx2mKDSqYCm/rme+LhpwpljNcdC2oIxQuxQX2ouoowBD2Ad485gpdY2e0iwtIbXGbAQPoZtHcquc61hRUcLHSfqKTY+4DQKzD08DiQKYD',
    'tfstk': 'fJ-nXrgKVe7Izt2-thjIPKn-qVgOAWs5BQERwgCr715sFgIpvFfkUI7RzLHCUCANK95z8gJN_TX746uCyTokaC8dTbMCUgAp_kCF8gSN_tXcL7rE4ATGAhLL26hCqLRAqjhxDmpBdasrMjCbUgxC4ToRav9V8iI54jhOU5-YggOvmcS-qdkGeTBFUQrPQAXcLgrFzkza_16P4_Rz45rNHt6Fa6rrQW45iBOvbXA68IrwcI-GKNu9L1y14hXhMsJeXurru9bhgp5iM_eAuNJ5r3w7q6JelQ62TWlARL8Ms9joXyS2IURcCHoYtOTpQKCwn-r2dMYDmM8n1PspthSwYE2z4djhONWGSWcGgH9wcG7t0xvwfBpBjLer4OdA_ptFqmkfxM5FjOt-1k5k7U-dRgNEMw9ySCXh0g8Y7rzjWu6Zehz7PwW1IsOS5CwnpaD71ADglc7FC9iiIA47PwW1IsHiIrzN8O6Ij',
    'uuid_tt_dd': '10_20621270840-1721898302528-711713',
    'fid': '20_83830262615-1723172643734-780807',
    'c_dl_prid': '1722939472835_963561',
    'c_dl_rid': '1723376026279_967700',
    'c_dl_fref': 'https://so.csdn.net/so/search',
    'c_dl_fpage': '/download/linyichao123/88915108',
    'c_dl_um': 'distribute.pc_toolbar_associateword.none-task-associate_word-opensearch_query-1-%3Cem%3E%E5%B0%8F%E5%B0%8F%E4%BC%98%E8%B6%A3%3C/em%3E%E7%A0%B4%E8%A7%A3%E7%89%88-null-null.179%5Ev5%5Epv',
    'log_Id_click': '24',
    'c_segment': '1',
    'dc_sid': 'd1a700dbe82ff32cfa5981f0c6f179e7',
    'qq_56972807comment_new': '1697995665162',
    'dc_session_id': '10_1724296141707.202708',
    'csrfToken': '3GQ3ndHvBOOxTLCpgdS6MPOx',
    'c_pref': 'default',
    'c_ref': 'default',
    'c_first_ref': 'default',
    'c_first_page': 'https%3A//www.csdn.net/',
    'c_dsid': '11_1724296141661.108259',
    'c_page_id': 'default',
    'log_Id_pv': '42',
    'www_red_day_last': 'red',
    'creativeSetApiNew': '%7B%22toolbarImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20230921102607.png%22%2C%22publishSuccessImg%22%3A%22https%3A//img-home.csdnimg.cn/images/20240229024608.png%22%2C%22articleNum%22%3A21%2C%22type%22%3A2%2C%22oldUser%22%3Atrue%2C%22useSeven%22%3Afalse%2C%22oldFullVersion%22%3Atrue%2C%22userName%22%3A%22qq_56972807%22%7D',
    'creative_btn_mp': '1',
    'log_Id_view': '8321',
    'csdn_newcert_qq_56972807': '1',
    'dc_tos': 'silnf4',
}

headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
    'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6,ja;q=0.5',
    'Cache-Control': 'no-cache',
    'Connection': 'keep-alive',
    'Pragma': 'no-cache',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36 Edg/122.0.0.0',
    'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Windows"',
}


def get_domain_segments(url):
    # 解析 URL，获取域名部分
    parsed_url = urlparse(url)
    domain = parsed_url.netloc  # 获取域名部分

    # 分割域名
    parts = domain.split('.')

    # 确保域名部分至少包含三个部分（比如 www.csdn.net 中的 ['www', 'csdn', 'net']）
    if len(parts) > 2:
        # 提取从第一个 '.' 到最后一个 '.' 之前的部分
        segments = parts[1:-1]
    else:
        segments = parts  # 如果没有足够的部分，则返回原始部分

    return segments


def crawl_website(website: str, crawl_type: str, depth: int, page_limit: int):
    import requests

    crawled_data = []
    seen_urls = set()  # 用于去重
    sequence_num = 1

    # 爬取页面的递归函数
    def crawl_page(url, current_depth, refer_url=None):
        global response
        nonlocal sequence_num
        # 检查深度和去重后的页数限制
        if current_depth > depth or len(crawled_data) >= page_limit:
            return
        if 'javascript:' in url:  # 跳过javascript链接
            return

        if url in seen_urls:
            return  # 如果 URL 已经被访问过，则直接返回
            # try:
        response = requests.get(url, cookies=cookies, headers=headers, timeout=5)
        response.encoding = 'utf-8'
        # 如果是404状态码，直接返回
        if response.status_code == 404:
            logger.info(f"404 Not Found: {url}")
        # 如果是其他状态码，记录状态码和URL，但仍继续处理响应内容
        if response.status_code != 200:
            logger.warning(f"Unexpected status code {response.status_code} for {url}, processing content anyway")
        if '' == response.text:
            print(f"Error fetch: {url}\n Response  : {response.text}")
        # except requests.exceptions.RequestException as e:
        #     # 捕获所有请求异常
        #     logger.error(f"Error occurred while fetching {url}: {e}")

        soup = BeautifulSoup(response.text, 'html.parser')

        # 确保统一格式处理URL（移除结尾的斜杠）
        if url.endswith('/'):
            url = url.rstrip('/')
        #
        base_website_list = get_domain_segments(url)  # 获取域名部分

        # 标记是否有新数据
        has_new_data = False

        if crawl_type == "text":
            # 寻找 p 和 a 标签
            paragraphs = soup.find_all(['p', 'a'])
            logger.info(f"Found {len([p for p in paragraphs if 'href' in p.attrs])} hrefs in {url}")
            for paragraph in paragraphs:
                if 'href' not in paragraph.attrs:
                    continue
                href = paragraph.get('href')
                if 'javascript:' in href:
                    return
                # 生成完整URL
                paragraph_url = urljoin(url, href)
                # 去重检查
                if paragraph_url in seen_urls:
                    continue

                info = {
                    "序号": sequence_num,
                    "爬取链接": paragraph_url,
                    "Refer": refer_url if refer_url else url,
                    "内链/外链": "内链" if any(base in paragraph_url for base in base_website_list) else "外链",
                    'res_text': response.text,
                    "爬取文字": soup.get_text(separator=' ').strip(),
                    "深度": current_depth
                }
                # logger.info(info)
                crawled_data.append(info)
                seen_urls.add(paragraph_url)
                sequence_num += 1
                has_new_data = True  # 标记有新数据

        elif crawl_type == "image":
            # 寻找 img 标签
            images = soup.find_all('img')
            logger.info(f"Found {len([img for img in images if 'src' in img.attrs])} images in {url}")

            for img in images:
                if 'src' not in img.attrs:
                    continue
                if 'javascript:' in img['src']:
                    return
                img_url = urljoin(url, img['src'])
                # 去重检查
                if img_url in seen_urls:
                    continue

                info = {
                    "序号": sequence_num,
                    "图片链接": img_url,
                    "Refer": refer_url if refer_url else website,
                    "内链/外链": "内链" if any(base in img_url for base in base_website_list) else "外链",
                    "深度": current_depth
                }
                # logger.info(info)
                crawled_data.append(info)
                seen_urls.add(img_url)
                sequence_num += 1
                has_new_data = True  # 标记有新数据

        # 只有当有新数据时，才递增深度并继续爬取
        next_depth = current_depth + 1 if has_new_data else current_depth

        # 寻找所有链接并递归爬取
        links = soup.find_all(['p', 'a'], href=True)
        for link in links:
            if any(base in link['href'] for base in base_website_list):
                next_url = urljoin(url, link['href'])
            else:
                next_url = link['href']
            print(f"Next URL: {next_url}")
            if next_url not in seen_urls:  # 检查新发现的 URL
                seen_urls.add(next_url)  # 将新发现的 URL 添加到已访问列表
                crawl_page(next_url, next_depth, refer_url=url)
            else:
                print(f"Skipping duplicate URL: {next_url}")

    # 开始爬取
    crawl_page(website, 0)

    # 保存数据到Excel文件
    output_file = f"{crawl_type}_data.xlsx"
    if len(crawled_data) > 0:
        pd.DataFrame(crawled_data).to_excel(output_file, index=False)
        print(f"Crawling completed. Data saved to {output_file}")
    else:
        print("There is no data to save.")
    return crawled_data


# FastAPI 部分保持不变，调用 crawl_website 函数
from fastapi import FastAPI, HTTPException

app = FastAPI()


@app.post("/crawl")
def crawl(website: str, crawl_type: str, depth: int, page_limit: int):
    if crawl_type not in ["text", "image"]:
        raise HTTPException(status_code=400, detail="Invalid crawl_type. Must be 'text' or 'image'.")

    result = crawl_website(website, crawl_type, depth, page_limit)
    return {"message": "Crawl completed", "data_count": len(result)}


if __name__ == "__main__":
    # 启动服务器
    # import uvicorn
    #
    # uvicorn.run(app, host="0.0.0.0", port=8000)
    #

    # 单独调用爬虫函数
    website = 'https://www.csdn.net/'
    crawl_type = "text"  # "text" 或 "image"
    depth = 99  # 爬取深度
    page_limit = 9999  # 要确保爬取的页面数量不超过这个值

    crawl_website(website, crawl_type, depth, page_limit)
