import re
from datetime import datetime, date
import random
from decimal import Decimal

import demjson

from flask import render_template

from app import create_app
from app.tools.downloader import Downloader
import app.tools.dateutil as dateutils
from fund import findFundTodayValuation

app = create_app()
db = app.db


def getFundRankUrl(date_sc, page_size):
    """
    拼接得到基金排行的地址
    :param date_sc:
    :param page_size:
    :return:
    """
    common_url = 'http://fund.eastmoney.com/data/rankhandler.aspx?op=ph&dt=kf&ft=all&rs=&gs=0&sc={date_sc}zf&st=desc&sd={today}&ed={today}&qdii=&tabSubtype=,,,,,&pi=1&pn={pn}&dx=1&v={random_v}'

    # 当前日期
    today = date.today()

    # 生成0-1之间的16位小数
    random_v = random.uniform(0, 1)
    random_v = round(random_v, 16)

    url = common_url.format(date_sc=date_sc, today=today, pn=page_size, random_v=random_v)

    return url


def getTopRank():
    """
    根据4433原则筛选基金，返回基金编码信息
    :return:
    """
    top_num = 2000
    top_num2 = 2600
    url_list = []
    # 爬取一年期业绩排名在前1/4的，这里直接爬取前2000的URL地址
    url1 = getFundRankUrl('1n', top_num)
    url_list.append(url1)
    # 爬取两年期业绩排名在前1/4的，这里直接爬取前2000的URL地址
    url2 = getFundRankUrl('2n', top_num)
    url_list.append(url2)
    # 爬取三年期业绩排名在前1/4的，这里直接爬取前2000的URL地址
    url3 = getFundRankUrl('3n', top_num)
    url_list.append(url3)
    # 爬取今年以来业绩排名在前1/4的，这里直接爬取前2000的URL地址
    url4 = getFundRankUrl('jn', top_num)
    url_list.append(url4)
    # 爬取近三月业绩排名在前1/3的，这里直接爬取前2600的URL地址
    url5 = getFundRankUrl('3y', top_num2)
    url_list.append(url5)
    # 爬取近六月业绩排名在前1/3的，这里直接爬取前2600的URL地址
    url6 = getFundRankUrl('6y', top_num2)
    url_list.append(url6)

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Cookie': 'qgqp_b_id=5b08305fd8f71dd958e2dd38b5cdf2e7; AUTH_FUND.EASTMONEY.COM_GSJZ=AUTH*TTJJ*TOKEN; searchbar_code=740001; st_si=29826834347683; '
                  'st_asi=delete; FundWebTradeUserInfo=JTdCJTIyQ3VzdG9tZXJObyUyMjolMjIlMjIsJTIyQ3VzdG9tZXJOYW1lJTIyOiUyMiUyMiwlMjJWaXBMZXZlbCUyMjolMjIlMjIsJTIyTFRva2VuJTIyOiUyMiUyMiwlMjJJc1Zpc2l0b3IlMjI6JTIyJTIyLCUyMlJpc2slMjI6JTIyJTIyJTdE; '
                  'ASP.NET_SessionId=uzl3ulvkulthqx0gtuio405c; EMFUND0=06-02%2018%3A23%3A38@%23%24%u519C%u94F6%u65B0%u80FD%u6E90%u4E3B%u9898@%23%24002190; '
                  'EMFUND1=06-02%2014%3A12%3A54@%23%24%u62DB%u5546%u4E2D%u8BC1%u7164%u70AD%u7B49%u6743%u6307%u6570%28LOF%29@%23%24161724; '
                  'EMFUND2=06-02%2014%3A18%3A14@%23%24%u5357%u534E%u4E30%u6DF3%u6DF7%u5408A@%23%24005296; EMFUND3=06-02%2015%3A18%3A17@%23%24%u5148%u950B%u65E5%u6DFB%u5229A@%23%24004151; '
                  'EMFUND4=06-02%2017%3A05%3A55@%23%24%u957F%u5B89%u5B8F%u89C2%u7B56%u7565%u6DF7%u5408@%23%24740001; EMFUND5=06-03%2010%3A09%3A07@%23%24%u56FD%u5BFF%u521B%u7CBE%u900988ETF%u8054%u63A5C@%23%24008899; '
                  'EMFUND6=06-03%2010%3A13%3A48@%23%24%u62DB%u5546%u62DB%u8F69%u7EAF%u503AA@%23%24003371; EMFUND7=06-03%2018%3A17%3A25@%23%24%u6D66%u94F6%u5B89%u76DB%u533B%u7597%u5065%u5EB7%u6DF7%u5408@%23%24519171; _'
                  'adsame_fullscreen_18503=1; EMFUND8=06-07%2014%3A22%3A17@%23%24%u5E73%u5B89%u8F6C%u578B%u521B%u65B0%u6DF7%u5408A@%23%24004390; EMFUND9=06-07 14:22:17@#$%u91D1%u4FE1%u884C%u4E1A%u4F18%u9009%u6DF7%u5408%u53D1%u8D77%u5F0F@%23%24002256; '
                  'st_pvi=51861310378525; st_sp=2021-05-27%2018%3A03%3A03; st_inirUrl=http%3A%2F%2Ffund.eastmoney.com%2F005827.html; st_sn=29; st_psi=20210607142512230-112200312936-3336338298',
        'Host': 'fund.eastmoney.com',
        'Referer': 'http://fund.eastmoney.com/data/fundranking.html',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    }

    D = Downloader(delay=0, user_agent='wswp3', proxies=None,
                   num_retries=1, cache=None, headers=headers)
    res_list = []
    # 遍历需要爬取的网址
    for url in url_list:
        html = D(url=url)
        html = html.replace('var rankData =', '').replace(';', '')
        # 下载处理后的数据格式类似："datas:[\"004244,东方周期优选灵活配置混合\"],lofNum:329,fofNum:16}"
        # 数据转成json
        html = demjson.decode(html)
        datas = html['datas']
        # 存放本次遍历到的基金编码
        code_list = []
        for data in datas:
            code_list.append(data.split(',')[0])
        # 求交集
        res_list = set(res_list).intersection(code_list) if res_list else code_list

    return res_list


@app.route("/recommend")
def recommend(code_list=None):
    # code_list = ['519987']
    print(datetime.now())
    recommend_list = []
    if code_list is None:
        code_list = getTopRank()
    for code in code_list:
        # 当日净值估算数据
        today_valuation = findFundTodayValuation(code)
        # 如果基金的涨跌幅 < 0，表示基金在跌，此时才考虑基金的买入
        if today_valuation and Decimal(today_valuation['gszzl']) < 0:
            # 拿到该基金最近三个月的历史净值明细数据
            lsjz_list = getFundValueHistory(code)['LSJZList']
            # 单位净值数据
            dwjz_list = []
            for lsjz in lsjz_list:
                # 单位净值
                dwjz = lsjz['DWJZ']
                dwjz_list.append(dwjz)
            # 该基金这段时间最小的单位净值
            dwjz_minimum = Decimal(min(dwjz_list))
            # 当日估算的单位净值
            dwjz_today = Decimal(today_valuation['gsz'])
            # 当日净值估算值相比最近这段时间的最低值的增长率
            growth_rate = (dwjz_today - dwjz_minimum) / dwjz_minimum * 100
            print(growth_rate)
            # 增长率在5%以内的表示为低值阶段，推荐购买
            if growth_rate < Decimal('10'):
                growth_rate = growth_rate.quantize(Decimal("0.000"))
                data = {'code': today_valuation['fundcode'],
                        'name': today_valuation['name'],
                        'dwjz_today': dwjz_today,
                        'dwjz_minimum': dwjz_minimum,
                        'growth_rate': str(growth_rate)+'%'}
                recommend_list.append(data)
    recommend_list.sort(key=lambda k: (k.get('growth_rate', 0)))
    result = {'data': recommend_list, 'today': date.today()}
    print(datetime.now())
    return render_template('recommend.html', result=result)


def getFundValueHistory(code):
    """
    查询过去三个月该基金的历史净值明细数据
    :param code:
    :return:
    """
    common_url = 'http://api.fund.eastmoney.com/f10/lsjz?callback=jQuery18306542268813609817_{timestamp}&fundCode={fund_code}&pageIndex=1&pageSize={page_size}&startDate={start_date}&endDate={end_date}&_={timestamp}'
    timestamp = str(dateutils.get_local_timestamp(datetime.now())).split('.')[0]
    today = date.today()
    # 获取三个月之前的日期
    start_date = dateutils.get_date_month(today, -3)
    url = common_url.format(fund_code=code, page_size=90, start_date=start_date, end_date=today, timestamp=timestamp)

    headers = {
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Connection': 'keep-alive',
        'Cookie': 'qgqp_b_id=5b08305fd8f71dd958e2dd38b5cdf2e7; AUTH_FUND.EASTMONEY.COM_GSJZ=AUTH*TTJJ*TOKEN; st_si=29826834347683; HAList=a-sz-300122-%u667A%u98DE%u751F%u7269; '
                  'em_hq_fls=js; st_asi=delete; EMFUND0=06-02%2014%3A18%3A14@%23%24%u5357%u534E%u4E30%u6DF3%u6DF7%u5408A@%23%24005296; EMFUND1=06-02%2015%3A18%3A17@%23%24%u5148%u950B%u65E5%u6DFB%u5229A@%23%24004151; '
                  'EMFUND2=06-02%2017%3A05%3A55@%23%24%u957F%u5B89%u5B8F%u89C2%u7B56%u7565%u6DF7%u5408@%23%24740001; EMFUND3=06-03%2010%3A09%3A07@%23%24%u56FD%u5BFF%u521B%u7CBE%u900988ETF%u8054%u63A5C@%23%24008899; '
                  'EMFUND4=06-03%2010%3A13%3A48@%23%24%u62DB%u5546%u62DB%u8F69%u7EAF%u503AA@%23%24003371; EMFUND5=06-08%2009%3A35%3A29@%23%24%u6D66%u94F6%u5B89%u76DB%u533B%u7597%u5065%u5EB7%u6DF7%u5408@%23%24519171; '
                  'EMFUND6=06-07%2014%3A22%3A17@%23%24%u5E73%u5B89%u8F6C%u578B%u521B%u65B0%u6DF7%u5408A@%23%24004390; EMFUND7=06-07%2014%3A22%3A17@%23%24%u91D1%u4FE1%u884C%u4E1A%u4F18%u9009%u6DF7%u5408%u53D1%u8D77%u5F0F@%23%24002256; '
                  'EMFUND8=06-08%2009%3A49%3A10@%23%24%u4E2D%u4FE1%u4FDD%u8BDA%u7A33%u9E3FA@%23%24006011; EMFUND9=06-08 13:57:55@#$%u534E%u590F%u6210%u957F%u6DF7%u5408@%23%24000001; st_pvi=51861310378525; st_sp=2021-05-27%2018%3A03%3A03; '
                  'st_inirUrl=http%3A%2F%2Ffund.eastmoney.com%2F005827.html; st_sn=108; st_psi=20210608135755355-112200305282-3476503203',
        'Host': 'api.fund.eastmoney.com',
        'Referer': 'http://fundf10.eastmoney.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.77 Safari/537.36'
    }
    D = Downloader(delay=0, user_agent='wswp3', proxies=None,
                   num_retries=1, cache=None, headers=headers)
    html = D(url=url)

    p1 = re.compile(r'[(](.*?)[)]', re.S)
    html_data = re.findall(p1, html)
    data_list = html_data[0] if html_data and len(html) > 0 else ''
    # 转成JSON
    data_json = demjson.decode(data_list)

    return data_json['Data']


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, debug=True)
    # recommend(code_list=['000001'])
