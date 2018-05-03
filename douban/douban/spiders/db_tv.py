# -*- coding: utf-8 -*-
import json
import re
import scrapy


class DbTvSpider(scrapy.Spider):
    name = 'db_tv'
    allowed_domains = ['m.douban.com']
    start_urls = ['http://m.douban.com/tv/']
    url_temp = 'http://m.douban.com'

    def parse(self, response):
        """从响应中提取出所有的分类url,构造请求"""
        cate_a = response.xpath('//ul[@class="type-list"]//a')
        for a in cate_a:
            _item = {}
            cate_url = a.xpath('./@href').extract_first()
            cate_name = a.xpath('./text()').extract_first()
            url = DbTvSpider.url_temp + cate_url
            _item['cate_name'] = cate_name
            # print(url)
            yield scrapy.Request(
                url,
                callback=self.parse_cate,
                meta={'item': _item}
            )
            # break

    def parse_cate(self, response):
        """从响应中提取出请求数据的url模板"""
        _item = response.meta.get('item')
        resp_data = response.text
        # 使用re匹配出api
        ret = re.search(r'(/rexxar/api/v2/subject_collection/.*/items\?)os=ios&for_mobile=1&callback', resp_data)
        url_temp = ret.group(1)
        url_temp = DbTvSpider.url_temp + url_temp
        start = 0
        count = 50
        headers = {'Referer': 'http://m.douban.com/tv/'}
        while start < 500:
            url = url_temp + 'start={}&count={}'.format(start, count)
            # print(url)
            yield scrapy.Request(
                url,
                callback=self.parse_detail,
                meta={'item': _item},  # 每次循环的item中的分类肯定是一样的,所以不用深拷贝
                headers=headers
            )
            start += count
            # break

    def parse_detail(self, response):
        # response中拿到的item中只有分类数据
        _item = response.meta.get('item')
        resp_json = json.loads(response.text)
        item_list = resp_json.get('subject_collection_items')
        # 如果item_list 不是None,才会保存数据,因为有的不足500条,请求了多次空的
        if item_list:
            for item in item_list:
                item['cate_name'] = _item.get('cate_name')
                print(item.get('title'))
                yield item
