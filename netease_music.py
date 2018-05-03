# 实现网易云音乐下载，三个功能
# 1.给歌单链接,下载歌单内所有歌曲
# 2.给专辑链接,下载专辑内所有歌曲
# 3.给单个歌曲链接,下载歌曲
import os
import re
import base64
import requests
import json

from lxml import etree
from Crypto.Cipher import AES  # 安装使用pip install pycrypto



class MusicDownload(object):
    def __init__(self):
        self.headers = {
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/63.0.3239.132 Safari/537.36"
        }
        # self.playlist_url_temp = 'http://music.163.com/playlist?id={}'  # 歌单页面真实url,填充歌单的id,从用户传来的链接中提取
        # self.album_url_temp = 'http://music.163.com/album?id={}'  # 专辑真实url,填充专辑id
        # self.song_url_temp = 'http://music.163.com/song?id={}'  # 单曲真实url

        self.second_param = "010001"  # 不可变
        # 不可变
        self.third_param = "00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7"
        self.forth_param = "0CoJUm6Qyw8W8jud"  # 不可变
        self.song_url = 'http://music.163.com/weapi/song/enhance/player/url?csrf_token='

    def get_option(self):
        print('下载:歌单内容,输入1;  专辑内容,输入2;  单曲内容,输入3;  退出按q')
        api = input('请输入要下载的内容编号:')

        return api

    def get_id(self, url):
        """获取不同请求的id,限于歌单,专辑,单曲id"""
        # 先对格式进行验证
        p = re.compile(r'http://music.163.com/#/(.*)\?id=(\d+)')
        ret = p.findall(url)
        cate, id_num = (ret[0][0], ret[0][1]) if ret else (None, None)
        # print(cate, id_num)
        return cate, id_num

    def get_real_url(self, api):
        while True:
            if api == '1':
                cate = 'playlist'
                print('歌单链接格式为:http://music.163.com/#/playlist?id=数字')
            elif api == '2':
                cate = 'album'
                print('专辑链接格式为:http://music.163.com/#/album?id=数字')
            elif api == '3':
                cate = 'song'
                print('单曲链接格式为:http://music.163.com/#/song?id=数字')
            print('返回上一层请按0')
            url = input('请输入链接:')
            if url == '0':
                return None
            # 校验链接是否正确
            r_cate, id_num = self.get_id(url)
            if id_num and r_cate == cate:
                url = re.sub(r'#/', '', url)
                return url
            else:
                print('请输入正确的链接')
                continue

    def enter(self):
        while True:
            api = self.get_option()
            file_name = input('请输入要保存的文件名:')
            if api == 'q':
                break
            elif api not in ["1", "2", "3"]:
                print('Warning:请输入正确编号')
                continue
            else:
                real_url = self.get_real_url(api)
                if real_url is None:
                    continue
                else:
                    return real_url, api, file_name

    def parse_url(self, real_url):
        """对url进行请求,获取响应返回"""
        resp = requests.get(real_url, headers=self.headers)
        return resp.content

    def get_song_id_name(self, resp):
        # 适用于歌单和专辑链接
        resp = resp.decode()
        html_ele = etree.HTML(resp)
        a_list = html_ele.xpath('//div[@id="song-list-pre-cache"]//a')
        if a_list:
            # 找到了a标签
            content_list = []
            for a in a_list:
                item = {}
                song_name = a.xpath('./text()')[0] if a.xpath('./text()') else None
                song_id = a.xpath('./@href')[0] if a.xpath('./@href') else None
                if song_id:
                    # 提取出来纯数字
                    ret = re.match(r'/song\?id=(\d+)', song_id)
                    song_id = ret.group(1) if ret else None
                item[song_name] = song_id
                content_list.append(item)
            return content_list
        return None  # 说明响应中没有数据

    def get_params(self, song_id):
        """根据原js代码改为python加密"""
        iv = "0102030405060708"  # 不可变
        first_key = self.forth_param
        second_key = 16 * 'F'  # 随机数,自定义即可
        first_param = "{\"ids\":\"[" + song_id + "]\",\"br\":128000,\"csrf_token\":\"\"}"  # 可变,从浏览器watch中截获
        h_encText = self.AES_encrypt(first_param, first_key, iv)
        h_encText = self.AES_encrypt(h_encText.decode('utf-8'), second_key, iv)
        return h_encText.decode('utf-8')

    def get_encSecKey(self):
        """生成这个参数所要的参数都是固定值,因此在浏览器console中,将生成这个参数的函数
        贴到控制台中,然后将固定的参数传进去即可
        固定参数i:FFFFFFFFFFFFFFFF,
                 e:010001
                 f:00e0b509f6259df8642dbc35662901477df22677ec152b5ff68ace615bb7b725152b3ab17a876aea8a5aa76d2e417629ec4ee341f56135fccf695280104e0312ecbda92557c93870114af6c9d05c4f7f0c3685b7a46bee255932575cce10b424d813cfe4875d3e82047b97ddef52741d546b8e289dc6935b3ece0462db0a22b8e7
        """
        encSecKey = "257348aecb5e556c066de214e531faadd1c55d814f9be95fd06d6bff9f4c7a41f831f6394d5a3fd2e3881736d94a02ca919d952872e7d0a50ebfa1769a7a62d512f5f1ca21aec60bc3819a9c3ffca5eca9a0dba6d6f7249b06f5965ecfff3695b54e1c28f3f624750ed39e7de08fc8493242e26dbc4484a01c76f739e135637c"
        return encSecKey

    def AES_encrypt(self, text, key, iv):
        pad = 16 - len(text) % 16
        text = text + pad * chr(pad)
        encryptor = AES.new(key, AES.MODE_CBC, iv)
        encrypt_text = encryptor.encrypt(text)
        encrypt_text = base64.b64encode(encrypt_text)
        return encrypt_text

    def get_json(self, params, encSecKey):
        data = {
            "params": params,
            "encSecKey": encSecKey
        }
        response = requests.post(self.song_url, headers=self.headers, data=data)
        return response.content.decode()

    def get_song_content(self, song_id):
        params = self.get_params(song_id)
        encSecKey = self.get_encSecKey()
        json_text = self.get_json(params, encSecKey)
        json_dict = json.loads(json_text)
        song_real_url = json_dict.get('data')[0].get('url')
        music_format = json_dict.get('data')[0].get('type')
        song_content = self.parse_url(song_real_url)  # 得到歌曲二进制数据
        return song_content, music_format

    def save_song(self, song_name, music_format, song_content, filename):
        print(song_name, '开始下载')
        with open('.\\' + filename + '\\' + song_name + '.' + music_format, 'wb') as f:
            f.write(song_content)
        print(song_name, '下载完成')

    def run(self):
        # 入口页面编写,获取真实url
        real_url, api, filename = self.enter()
        os.mkdir('.\\' + filename)
        # print(real_url, api)
        if real_url is None:
            print('欢迎再次使用')
            return

        resp = self.parse_url(real_url)  # 发送请求,获取响应

        if api == '1' or api == '2':
            # 得到的是歌单页面
            # 提取数据,得到列表,包含的是每首歌的字典[{name},{id}],适用于歌单和专辑
            song_id_name = self.get_song_id_name(resp)
            # 调用下载模块,传递歌曲id编号,下载
            for song in song_id_name:
                song_id = list(song.values())[0]
                song_name = list(song.keys())[0]
                # print(song_name, song_id)

                # 下边是获取歌曲真实的url请求得到数据
                song_content, music_format = self.get_song_content(song_id)
                self.save_song(song_name, music_format, song_content, filename)

        elif api == '3':
            # 单曲
            html_ele = etree.HTML(resp.decode())
            song_name = html_ele.xpath('//em[@class=f-ff2]/text()')
            song_id = real_url.split('=')[-1]

            song_content, music_format = self.get_song_content(song_id)
            self.save_song(song_name, music_format, song_content, filename)


if __name__ == '__main__':
    netease = MusicDownload()
    netease.run()
