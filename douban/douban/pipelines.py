# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: https://doc.scrapy.org/en/latest/topics/item-pipeline.html
import pymongo



class DoubanPipeline(object):
    def open_spider(self, spider):
        client = pymongo.MongoClient()
        self.collection = client.douban.db_tv

    def process_item(self, item, spider):
        self.collection.insert(item)
        return item
