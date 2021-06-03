import datetime
import sys
import os

# sys.path.append(os.path.dirname(sys.path[0]))

from decimal import Decimal
from app import create_app
from app.tools.downloader import Downloader
import pandas as pd
import re

from flask import Flask, render_template

app = create_app()
db = app.db


def getExcelData(file, usecols):
    df = pd.read_excel(file, sheet_name=0, usecols=usecols)
    return df


def importExcel():
    excelData = getExcelData('E://note//基金实盘日常操作.xlsx', usecols=[1, 4])
    nameList = excelData['Unnamed: 1'].values.T.tolist()
    positionList = excelData['Unnamed: 4'].values.T.tolist()
    for i in range(len(nameList)):
        if isinstance(nameList[i], str):
            p1 = re.compile(r"[（](.*?)[）]", re.S)
            temp = re.findall(p1, nameList[i])
            if len(temp) > 0:
                code = temp[0]
                name = nameList[i][:-8]
                position = positionList[i]
                user_fund = UserFund(name=name, code=code, position=position, remark=None)
                db.session.add(user_fund)
    db.session.commit()


def findFundNetValue(code):
    common_url = 'http://fundgz.1234567.com.cn/js/'
    D = Downloader(delay=0, user_agent='wswp3', proxies=None,
                   num_retries=1, cache=None)
    url = common_url + code + '.js'
    html = D(url)
    temp = html[8:-2]
    if temp != '':
        res = eval(temp)
        # 涨跌幅
        gszzl = Decimal(res['gszzl'])
    else:
        return None
    return gszzl


@app.route("/index")
def index():
    data_list = UserFund.query.all()
    fund_sum = 0
    position_sum = 0
    res = {}
    for data in data_list:
        code = data.code
        # 涨跌幅
        gszzl = findFundNetValue(code)
        data.position = data.position.quantize(Decimal("0.000"))
        if gszzl is not None:
            data.net_value = gszzl
            fund_sum = fund_sum + gszzl * data.position
            position_sum = position_sum + data.position

    rate = (fund_sum / position_sum).quantize(Decimal("0.00"))
    amount = rate * position_sum * 10
    res['list'] = data_list
    res['rate'] = rate
    res['amount'] = amount.quantize(Decimal("0.00"))
    res['date'] = datetime.date.today()
    return render_template('index.html', result=res)


class UserFund(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    code = db.Column(db.String(10))
    position = db.Column(db.String(10))
    remark = db.Column(db.String(255))

    def __init__(self, name, code, position, remark):
        self.name = name
        self.code = code
        self.position = position
        self.remark = remark

    def __repr__(self):
        return 'UserFund=[name=' + self.name + ',code=' + self.code \
               + ',position=' + str(self.position) + ',remark=' + str(self.remark) + ']'


if __name__ == "__main__":
    # importExcel()
    app.run(host='0.0.0.0', port=5000, debug=True)
