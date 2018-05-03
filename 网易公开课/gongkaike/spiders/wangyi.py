# -*- coding: utf-8 -*-
import json
import os
import scrapy
from copy import deepcopy
from scrapy.mail import MailSender
from gongkaike.get_url import get_pid


class WangyiSpider(scrapy.Spider):
    name = 'wangyi'
    allowed_domains = ['163.com', 'mov.bn.netease.com']
    # start_urls = ['http://163.com/']
    play_url = 'http://c.open.163.com/mob/{}/getMoviesForAndroid.do'

    def start_requests(self):
        # 完成交互设计,提取公开课的id,得到数据链接url,发起请求
        while True:
            pid = get_pid()
            if pid:
                url = self.play_url.format(pid)
                yield scrapy.Request(
                    url,
                    callback=self.parse,
                    # errback=self.parse_err
                )
                break
            else:
                # url格式错误
                print('url格式错误,请重新输入')
                continue

    def parse(self, response):
        item = {}
        # print(response.text)
        resp_dict = json.loads(response.text)
        video_list = resp_dict.get('data').get('videoList')
        b_title = resp_dict.get('data').get('title')
        play_count = resp_dict.get('data').get('playCount')  # 总计多少节
        print('本课程共计{}节'.format(play_count))
        item['folder_name'] = b_title
        for video in video_list:
            l_title = video.get('title')
            p_num = video.get('pNumber')
            if video.get('mp4ShdUrlOrign'):
                mp4_url = video.get('mp4ShdUrlOrign')
            elif video.get('mp4HdUrlOrign'):
                mp4_url = video.get('mp4HdUrlOrign')
            if video.get('mp4SdUrlOrign'):
                mp4_url = video.get('mp4SdUrlOrign')
            elif video.get('mp4ShdUrl'):
                mp4_url = video.get('mp4ShdUrl')
            elif video.get('mp4HdUrl'):
                mp4_url = video.get('mp4HdUrl')
            elif video.get('mp4SdUrl'):
                mp4_url = video.get('mp4SdUrl')
            _type = mp4_url.split('.')[-1]
            item['file_name'] = str(p_num) + '-' + l_title + '.' + _type
            print(mp4_url, item['file_name'])
            print('第{}节开始下载'.format(p_num))
            yield scrapy.Request(
                mp4_url,
                callback=self.get_video,
                meta={
                    'item': deepcopy(item),
                    'download_warnsize': 0
                }
            )

    def get_video(self, response):
        item = response.meta.get('item')
        # 创建文件夹,名称为课程的大名称
        try:
            os.mkdir('./' + item.get('folder_name'))
        except Exception as e:
            pass
        os.chdir('./' + item.get('folder_name'))
        with open(item.get('file_name'), 'wb') as f:
            f.write(response.body)
