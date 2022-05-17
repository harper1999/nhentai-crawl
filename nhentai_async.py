# -*- coding=utf-8 -*-
# @Time: 2022/5/13 1:24
# @Author: Harper
# @File: nhentai_sync.py
# @Software: PyCharm

import yescaptcha
import asyncio
from lxml import etree
import os
import logging
import re
import aiohttp

logging.basicConfig(level=logging.INFO, format='%(asctime)s|%(levelname)s|%(message)s')
favourite_path = r'D:\Python\web crawler\requests\favourites'
if not os.path.exists(favourite_path):
    os.mkdir(favourite_path)
login_url = 'https://nhentai.net/login/'
favourites = 'https://nhentai.net/favorites/'
headers = {
    # ':authority': 'nhentai.net',
    # ':method': 'GET',
    # ':path': '/ favorites /',
    # ':scheme': 'https',
    'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9',
    # 'accept-encoding': 'gzip, deflate, br',
    'accept-language': 'zh-CN,zh;q=0.9',
    'cache-control': 'max - age = 0',
    'cookie': ''  
    'referer': 'https://nhentai.net/favorites/',
    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="101", "Google Chrome";v="101"',
    'sec-ch-ua - mobile': '?0',
    'sec-ch-ua - platform': "Windows",
    'sec-fetch-dest': 'document',
    'sec-fetch-mode': 'navigate',
    'sec-fetch-site': 'same-origin',
    'sec-fetch-user': '?1',
    'upgrade-insecure-requests': '1',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36'}


async def main():
    async with aiohttp.ClientSession(headers=headers) as session:
        async with session.get(favourites) as f_res:  # 获取收藏夹
            last_page_href = \
                etree.HTML(await f_res.text()).xpath('//section[@class="pagination"]/a[@class="last"]/@href')[0]
            last_page = last_page_href[last_page_href.find('page=') + 5:]  # 获取最后的收藏页
            pages = [favourites + '?page={}'.format(i) for i in range(1, int(last_page) + 1)]  # 所有收藏链接
            while pages:  # 服务器限制请求服务数量 最多8次
                separated_pages = pages[:2]
                pages = pages[2:]
                fetch_albums_tasks = [asyncio.create_task(fetch_albums(session, page)) for page in separated_pages]
                await asyncio.wait(fetch_albums_tasks)
                # await asyncio.sleep(2)   # 等待使服务器不返回429


async def fetch_albums(session, page):
    async with session.get(page) as p_res:
        if p_res.status == 200:
            subdomains = etree.HTML(await p_res.text()).xpath('//div[@class="gallery"]/a/@href')  # 相册页子域名
            album_urls = ['https://nhentai.net/' + i for i in subdomains]  # 所有的完整漫画链接
            while album_urls:
                separated_urls = album_urls[:2]
                album_urls = album_urls[2:]
                fetch_album_tasks = [asyncio.create_task(fetch_album(session, url)) for url in separated_urls]
                await asyncio.wait(fetch_album_tasks)
        else:
            # print(p_res)
            logging.info(f'响应状态码: {page, etree.HTML(await p_res.text()).xpath("//title/text()")[0]}')


async def fetch_album(session, url):
    async with session.get(url) as album_res:  # 获取漫画页
        if album_res.status == 200:
            def create_folders():  # 以漫画名创建文件夹
                if not os.path.exists(album_path):
                    # Windows10文件路径限制最多260字符  要把注册表中的LongPathsEnabled的值改为1
                    os.mkdir(album_path)
                logging.info(f'folder created: {title}')

            title = ''.join(etree.HTML(await album_res.text()).xpath('//h1[@class="title"]/span/text()'))
            album_path = favourite_path + '\\' + re.sub('[/:*?"<>|]', '-', title)  # 去掉非法字符
            create_folders()

            async def download_imgs(session, img):  # 下载图片
                async with session.get(img) as img_res:  # 获取图片
                    try:
                        logging.info(f'Downloading: {title}')
                        content = await img_res.content.read()
                        file_name = img.rsplit('/')[-1]
                        with open(album_path + '\\' + file_name + '.jpg', 'wb') as fp:
                            fp.write(content)
                        logging.info(f'Download completed: {title}')
                    except Exception as err:
                        print(err)
                        logging.info(f'code: {img_res.status}, Downloading failed: {title}')

            imgs = etree.HTML(await album_res.text()).xpath('//img[@class="lazyload"]/@data-src')  # 图片地址集合
            download_imgs_tasks = [asyncio.create_task(download_imgs(session, img)) for img in imgs]
            await asyncio.wait(download_imgs_tasks)
        else:
            logging.info(f'响应状态码: {url, etree.HTML(await album_res.text()).xpath("//title/text()")[0]}')


if __name__ == '__main__':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        # 运行协程需要进入异步模式(即进入event_loop)，开始控制整个程序的状态，然后把协程对象转为任务task
        cc = asyncio.run(main())
        # print(cc)
        # loop = asyncio.get_event_loop()  # 生成事件循环对象
        # loop.run_until_complete(startup(remote))  # 检测异步对象任务的状态
    except KeyboardInterrupt as exc:
        logging.info('Quit.')
