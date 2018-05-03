import re
from lxml import etree
import requests


def get_pid():
    pc_header = {
        'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/65.0.3325.181 Safari/537.36'
    }
    url = input('请输入要下载的公开课链接:')
    # 先判断格式 http://open.163.com/special/opencourse/nealacree.html?1436514307961
    show = re.match(r'http://open\.163\.com/special/opencourse/.+?\.html', url)
    play = re.match(r'http://open\.163\.com/movie/.*?\.html', url)
    print(show, play)
    if show or play:
        # 两者存在,再判断到底哪个存在
        if show:
            resp = requests.get(url, headers=pc_header)
            html_ele = etree.HTML(resp.text)  # 使用content.decode()会报错,无法解码,使用content后用etree会改变内容
            url = html_ele.xpath('//a[@class="plybtn"]/@href')  # 这里拿到的和第二种请求方式的url一致
            url = url[0] if url else None
        # 从url中提取公开课pid
        if url:
            pid = url.split('/')[-1].split('_')[0]
            return pid
    else:
        return None  # 格式不正确