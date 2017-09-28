# -*- coding: utf-8 -*-
import os
import re
import json
import time
import random
import requests
import itertools
from bs4 import BeautifulSoup
from multiprocessing import Pool
from requests.exceptions import ConnectionError


# 随机更换user-agents
def choice_headers():
    agents = [
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:46.0) Gecko/20100101 Firefox/46.0',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.87 Safari/537.36 OPR/37.0.2178.32',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.57.2 (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/46.0.2486.0 Safari/537.36 Edge/13.10586',
        'Mozilla/5.0 (Windows NT 10.0; WOW64; Trident/7.0; rv:11.0) like Gecko',
        'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
        'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.106 BIDUBrowser/8.3 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Maxthon/4.9.2.1000 Chrome/39.0.2146.0 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/47.0.2526.80 Safari/537.36 Core/1.47.277.400 QQBrowser/9.4.7658.400',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 UBrowser/5.6.12150.8 Safari/537.36',
        'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/38.0.2125.122 Safari/537.36 SE 2.X MetaSr 1.0',
    ]
    Agent = random.choice(agents)
    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
        'Connection': 'keep-alive',
        'Host': 'tuchong.com',
        'Referer': 'https://tuchong.com/explore/',
        'User-Agent': Agent
    }
    return headers


def get_tag_page(url):
    try:
        response = requests.get(url=url, headers=choice_headers(), timeout=10)
        if response.status_code == 200:
            json_text = json.loads(response.text)
            return json_text
    except ConnectionError:
        print('Error:连接标签页失败！')
        return None


def parse_img_page(url):
    try:
        response = requests.get(url, headers=choice_headers(), timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'lxml')
            img_urls = [result['src'] for result in soup.select('.multi-photo-image')]
            return img_urls
    except ConnectionError:
        print('Error:连接作品页失败！')
        return None


def dowmload_imgs(img_urls, filename):
    for i, img_url in enumerate(img_urls):
        img_name = re.search('(.*?\]).*', filename).group(1)
        # 为每张照片命名唯一名字（不采用md5，因为难看）
        file_path = (
            os.path.dirname(os.path.abspath(__file__)) + "/" + filename + "/" + img_name + '第' + str(
                i + 1) + '张' + '.jpg')
        with open(file_path, 'wb') as f:
            f.write(requests.get(img_url).content)
            print('正在下载：', img_name, '第' + str(i + 1) + '张')


def main(page_num):
    # 标签内‘小清新’可自行按网站标签更换
    tag_name = '私房'
    start_url = 'https://tuchong.com/rest/tags/' + tag_name + '/posts?page=' + str(page_num) + '&count=20&order=weekly'
    tag_page_html = get_tag_page(start_url)
    print('正在下载，请耐心等待')
    for img_page_datil in tag_page_html['postList']:
        # 每一页下载延迟5秒
        time.sleep(5)
        img_urls = parse_img_page(img_page_datil['url'])
        # 有标题且照片大于5张才爬取
        if img_urls:
            if len(img_urls) >= 5 and img_page_datil['title']:
                # 以标题名字+作者id作为标题，去除文件夹命名的非法字符
                filename = ''.join(itertools.chain(*re.split('/|\\|:|<|>|\?|"|\*|\n|\\\|\||:| ',
                                                             '{0}-[{2}P]-大师ID{1}'.format(img_page_datil['title'],
                                                                                         img_page_datil['author_id'],
                                                                                         img_page_datil['image_count']))))
                # 创建文件夹
                if os.path.exists(filename) is False:
                    print('正在下载：', filename)
                    os.mkdir(os.path.dirname(os.path.abspath(__file__)) + "/" + filename)
                    dowmload_imgs(img_urls, filename)
                else:
                    # 如果文件夹存在：判断文件夹内照片数量如果小于照片url数量，则补充下载，反之跳过该合集
                    if int(len([x for x in os.listdir(os.path.dirname(__file__) + "/" + filename)])) < int(
                            img_page_datil['image_count']) * 8 // 10:
                        dowmload_imgs(img_urls, filename)
                    else:
                        print(filename, '已经存在')


if __name__ == '__main__':
    groups = [num for num in range(1, 20)]
    pool = Pool(3)
    pool.map(main, groups)
