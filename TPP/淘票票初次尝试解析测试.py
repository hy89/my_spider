import json
import execjs
import time
import re
import requests
from pymongo import MongoClient

client = MongoClient(host='127.0.0.1', port=27017)
db = client.movie


class TPP(object):
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1'
        }
        # appKey={}   t={}  sign={}   city{}  以下两个都是这四个参数
        # self.get_cookie_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopadvertiseapi.queryadvertise/5.0/?appKey={}&t={}&sign={}&data=%7B%22city%22%3A{}%2C%22advertiseCode%22%3A%221%2C19%2C18%22%2C%22advertiseType%22%3A4071%2C%22platform%22%3A%228%22%7D'
        self.get_cookie_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopadvertiseapi.queryadvertise/5.0/?appKey={}&t={}&sign={}&data=%7B%22advertiseCode%22%3A%221%2C19%2C18%22%2C%22advertiseType%22%3A4071%2C%22platform%22%3A%228%22%7D'
        self.get_content_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopshowapi.getshowsbycitycode/4.0/?appKey={}&t={}&sign={}&data=%7B%22field%22%3A%22i%3Aid%3Bposter%3BshowName%3BshowMark%3Bremark%3Bdirector%3BleadingRole%3BpreviewNum%3BopenDay%3BopenTime%3BwantCount%3Bfantastic%3BspecialSchedules(i%3Aid%3Btag%3Btitle%3Bdescription)-1%3BderivationList(i%3Aid%3Blabel%3Btitle%3Blinks%3BadvertiseType)%3Bactivities(i%3Aid%3BactivityTag%3BactivityExtType%3BactivityTitle%3BlongDescription)%3Btype%3Bduration%3Bcountry%3BopenCountry%3BfriendCount%3Bfriends%3BstarMeeting%3BpreScheduleDates%3BsoldTitle%3BsoldType%22%2C%22pageIndex%22%3A1%2C%22pagesize%22%3A10%2C%22citycode%22%3A%22{}%22%2C%22pageCode%22%3A%22%22%2C%22platform%22%3A%228%22%7D'
        self.get_city_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopregionapi.getallregion/4.0/?appKey={}&t={}&sign={}&data=%7B%22platform%22%3A%228%22%7D'
        # 电影院每次请求10条数据
        self.get_cinema_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopcinemaapi.getcinemalistinpage/7.5/?appKey={}&t={}&sign={}&data=%7B%22pageSize%22%3A{}%2C%22pageIndex%22%3A{}%2C%22pageCode%22%3A%22APP_CINEMA%22%2C%22regionName%22%3A%22%22%2C%22support%22%3A0%2C%22showTime%22%3A%22%22%2C%22sortType%22%3A1%2C%22brandCode%22%3A%22%22%2C%22showDate%22%3A0%2C%22cityCode%22%3A%22{}%22%2C%22longitude%22%3A0%2C%22latitude%22%3A0%2C%22platform%22%3A%228%22%7D'
        self.get_movie_url = 'https://acs.m.taopiaopiao.com/h5/mtop.film.mtopscheduleapi.getcinemaschedules/7.0/?appKey={}&t={}&sign={}&data=%7B%22cinemaId%22%3A%22{}%22%2C%22hall%22%3A%22%22%2C%22showVersion%22%3A%22%22%2C%22platform%22%3A%228%22%7D'
        self.appkey = '12574478'

    @staticmethod
    def get_js():
        """获取本地js文件内容"""
        js_str = ''
        with open('get_sign.js', 'r') as f:
            line = f.readline()
            while line:
                js_str += line
                line = f.readline()
        js = execjs.compile(js_str)
        return js

    def get_sign(self, js, token='undefined', city=None):
        # 默认情况下undefined,令牌过期,和初次都通过这个值,计算得到首次的sign
        t = int(time.time() * 1000)
        data = ''
        # 城市信息需要后期更改
        if token == 'undefined':
            # data = '{"city":%s,"advertiseCode":"1,19,18","advertiseType":4071,"platform":"8"}' % city
            data = '{"advertiseCode":"1,19,18","advertiseType":4071,"platform":"8"}'
            print(data)
            sign = js.call('c', token + "&" + str(t) + "&" + self.appkey + "&" + data)
            print(t, sign, 'first_t')
            return t, sign
        else:
            # 这个针对的是请求列表页数据的参数
            # data_content = '{"field":"i:id;poster;showName;showMark;remark;director;leadingRole;previewNum;openDay;openTime;wantCount;fantastic;specialSchedules(i:id;tag;title;description)-1;derivationList(i:id;label;title;links;advertiseType);activities(i:id;activityTag;activityExtType;activityTitle;longDescription);type;duration;country;openCountry;friendCount;friends;starMeeting;preScheduleDates;soldTitle;soldType","pageIndex":1,"pagesize":10,"citycode":"%s","pageCode":"","platform":"8"}' % city
            data_city = '{"platform":"8"}'  # 针对请求city
            # sign_content = js.call('c', token + "&" + str(t) + "&" + self.appkey + "&" + data_content)
            sign_city = js.call('c', token + "&" + str(t) + "&" + self.appkey + "&" + data_city)
            return t, sign_city

    def get_cookies(self, t, sign, city=None):
        # 令牌如果过期,将token设置为undefined,重新获取cookie
        url = self.get_cookie_url.format(self.appkey, t, sign)
        resp = requests.get(url, headers=self.headers)
        resp_dict = json.loads(resp.content.decode())
        # print(resp.content.decode())
        if resp_dict['ret'][0] == "FAIL_SYS_TOKEN_EMPTY::令牌为空":
            cookiesjar = resp.cookies
            cookies = requests.utils.dict_from_cookiejar(cookiesjar)
            return cookies

    def get_first_token_cookies(self, js, city):
        first_t, first_sign = self.get_sign(js)
        # 请求获取带有初始token的cookie,获取cookie需要city代码
        cookies = self.get_cookies(first_t, first_sign)  # 字典
        print(cookies)
        token = cookies.get('_m_h5_tk').split('_')[0]
        return token, cookies

    def get_city(self, t, sign, cookies):
        url = self.get_city_url.format(self.appkey, t, sign)
        city_ = requests.get(url, headers=self.headers, cookies=cookies)
        city_str = city_.content.decode()
        city_dict = json.loads(city_str)
        all_city_dict = city_dict.get('data').get('returnValue')
        all_city = []
        for city_list in all_city_dict.values():
            # 得到依据首字母拼音划定的列表
            for city in city_list:
                all_city.append(city)
                # 获取cityCode,请求所有城市的数据,上海的数据也放到这里提取
        return all_city

    def save_city_into_mongo(self, js):
        first_token, cookies = self.get_first_token_cookies(js, city='310100')
        # 获取城市列表,为了方便,初始城市直接设置为上海,这样才能得到cookie,不知道不带城市是否能得到cookie
        # 得到城市列表的目的是存到数据库中,可以在这判断一下数据库中是否有city存在,如果有,就不再执行下面的语句
        t, sign_city = self.get_sign(js, token=first_token,
                                                   city='310100')  # 这里的目的是得到sign_city,只有带上这个才能得到城市列表
        all_city = self.get_city(t, sign_city, cookies)
        for city in all_city:
            city['_id'] = city['id']
            city.pop('id')
            db.city.save(city)  # 如果id存在,更新

    def get_cinema_sign(self, js, city, token):
        t = int(time.time() * 1000)
        data_cinema = '{"pageSize":200,"pageIndex":1,"pageCode":"APP_CINEMA","regionName":"","support":0,"showTime":"","sortType":1,"brandCode":"","showDate":0,"cityCode":"%s","longitude":0,"latitude":0,"platform":"8"}' % (
            city)
        sign_cinema = js.call('c', token + "&" + str(t) + "&" + self.appkey + "&" + data_cinema)
        return t, sign_cinema

    def get_movie_sign(self, js, cinema_id, token):
        t = int(time.time() * 1000)
        data_movie = '{"cinemaId":"%s","hall":"","showVersion":"","platform":"8"}' % (cinema_id)
        sign_movie = js.call('c', token + "&" + str(t) + "&" + self.appkey + "&" + data_movie)
        return t, sign_movie

    def get_cinema(self, t, sign, city, cookies):
        url = self.get_cinema_url.format(self.appkey, t, sign, '200', '1', city)  # 10每页数量,1 页数
        resp = requests.get(url, headers=self.headers, cookies=cookies)
        resp_dict = json.loads(resp.content.decode())
        cinema_list = resp_dict.get('data').get('returnValue').get('cinemas')
        print(len(cinema_list))
        return cinema_list

    def get_movie(self, t, sign, cinema_id, cookies):
        url = self.get_movie_url.format(self.appkey, t, sign, cinema_id)
        resp = requests.get(url, headers=self.headers, cookies=cookies)
        resp_dict = json.loads(resp.content.decode())
        movie_list = resp_dict.get('data').get('returnValue').get('showVos')
        movie_schedule_map = resp_dict.get('data').get('returnValue').get('showScheduleMap')
        # print('movie', resp.content.decode())
        return movie_list, movie_schedule_map

    def run(self):
        # 获取编译后的js文件内容
        js = self.get_js()
        # 从数据库取城市信息,如果不存在,就重新下载
        city_cursor = db.city.find()  # cursor对象,游标对象取一次就没了
        city_list = list(city_cursor)
        if len(list(city_list)) == 0:  # 可以定期更新一下地区
            self.save_city_into_mongo(js)
            city_cursor = db.city.find()  # cursor对象,游标对象取一次就没了
            city_list = list(city_cursor)

        # print(list(city_list))
        for city in list(city_list):
            city_code = city.get('cityCode')
            city_name = city.get('regionName')
            print(city_code, city_name)
            token, cookies = self.get_first_token_cookies(js, city_code)

            # 获取城市内的所有电影院信息
            t_cinema, sign_cinema = self.get_cinema_sign(js, city_code, token)
            cinema_list = self.get_cinema(t_cinema, sign_cinema, city_code, cookies)
            # print(cinema_list)
            for cinema in cinema_list:
                cinema_id = cinema.get('cinemaId')
                cinema_name = cinema.get('cinemaName')
                cinema_addr = cinema.get('address')
                t, sign_movie = self.get_movie_sign(js, cinema_id, token)

                movie_list, movie_schedule_map = self.get_movie(t, sign_movie, cinema_id, cookies)
                for movie in movie_list:
                    item = {}
                    item['city'] = city_name
                    item['cinema_name'] = cinema_name
                    item['cinema_addr'] = cinema_addr
                    movie_name = movie.get('showName')
                    item['movie_name'] = movie_name
                    movie_id = movie.get('showId')
                    movie_duration = movie.get('duration')
                    item['duration'] = movie_duration
                    print(movie_id, movie_name, movie_duration)
                    if movie_id in movie_schedule_map:
                        for movie_date_cate in movie_schedule_map.get(movie_id):
                            date = movie_date_cate.get('dateDesc')
                            date = re.search(r'\d{2}-\d{2}', date)
                            date = date.group() if date else None
                            schedule_vos = movie_date_cate.get('scheduleVos')
                            item[date] = schedule_vos
                        print(item)
                        db.movies.insert(item)


if __name__ == '__main__':
    tpp = TPP()
    tpp.run()
