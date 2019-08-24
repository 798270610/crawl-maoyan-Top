import requests
import re
import json
from requests.exceptions import  RequestException
import time
import pymongo


MONGO_DB = 'maoyan'
MONGO_URI = 'localhost'
client = pymongo.MongoClient(MONGO_URI)
db = client[MONGO_DB]
collection = 'top_movie'


def save_to_mongo(item):
    db[collection].insert(item)


def get_one_page(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return response.text
        return None
    except RequestException:
        return "请求失败"


""" 
    单条电影html信息为：
             <dd>
                        <i class="board-index board-index-1">1</i>
    <a href="/films/1203" title="霸王别姬" class="image-link" data-act="boarditem-click" data-val="{movieId:1203}">
      <img src="//s3plus.meituan.net/v1/mss_e2821d7f0cfe4ac1bf9202ecf9590e67/cdn-prod/file:5788b470/image/loading_2.e3d934bf.png" alt="" class="poster-default" />
      <img data-src="https://p1.meituan.net/movie/20803f59291c47e1e116c11963ce019e68711.jpg@160w_220h_1e_1c" alt="霸王别姬" class="board-img" />
    </a>
    <div class="board-item-main">
      <div class="board-item-content">
              <div class="movie-item-info">
        <p class="name"><a href="/films/1203" title="霸王别姬" data-act="boarditem-click" data-val="{movieId:1203}">霸王别姬</a></p>
        <p class="star">
                主演：张国荣,张丰毅,巩俐
        </p>
<p class="releasetime">上映时间：1993-01-01</p>    </div>
    <div class="movie-item-number score-num">
<p class="score"><i class="integer">9.</i><i class="fraction">5</i></p>        
    </div>
"""
"""
    说明:yield{}可生成一个可迭代对象，此处是把它复制为一个个的字典，形成结构化数据
"""


def parse_one_page(html):
    par_str = '<dd>.*?board-index.*?>(.*?)</i>.*?data-src="(.*?)".*?name.*?a.*?>(.*?)</a>.*?star.*?>(.*?)</p>.*?releasetime.*?>(.*?)</p>.*?integer.*?>(.*?)</i>.*?fraction.*?>(.*?)</i>.*?</dd>'
    pattern = re.compile(par_str, re.S)
    items = re.findall(pattern, html)
    for item in items:
        yield {
            '排名': item[0],
            '海报': item[1],
            '影片名称': item[2].strip(),
            '主演': item[3].strip()[3:]if len(item[3]) > 3 else '',
            '上映时间': item[4].strip()[5:]if len(item[4]) > 5 else '',
            '评分': item[5].strip()+item[6].strip()
        }
        item_map = {
            'rank': item[0],
            'pic': item[1],
            'name': item[2].strip(),
            'actor': item[3].strip()[3:]if len(item[3]) > 3 else '',
            'release': item[4].strip()[5:]if len(item[4]) > 5 else '',
            'score': item[5].strip()+item[6].strip()
        }
        save_to_mongo(item_map)


def write_to_file(content):
    """
        说明：利用JSON库中的dumps()可实现字典的序列化
              并指定ensure_ascii为False，可以保证输出结果是中文，而不是Unicode编码
    """
    with open('result.txt', 'a+', encoding='utf-8')as f:
        f.write(json.dumps(content, ensure_ascii=False)+'\n')


def main(offset):
    url = 'http://maoyan.com/board/4?offset='+str(offset)
    html = get_one_page(url)
    for item in parse_one_page(html):
        print(item)
        write_to_file(item)


if __name__ == '__main__':
    # 抓取排名100
    for i in range(10):
        main(offset=i*10)
        time.sleep(1)
