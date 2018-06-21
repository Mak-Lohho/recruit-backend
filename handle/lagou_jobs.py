#-*- coding: utf-8 -*-
import json
import requests
import xlwt
# import time
import random
from fake_useragent import UserAgent
from urllib.parse import quote
import re
import math
import mysql.connector

maxPage = 1

#http连接有问题时候，自动重连
def conn_try_again(function):
    RETRIES = 10
    #重试的次数
    count = {"num": RETRIES}
    def wrapped(*args, **kwargs):
        try:
            return function(*args, **kwargs)
        except Exception as err:
            if count['num'] < 2:
                count['num'] += 1
                return wrapped(*args, **kwargs)
            else:
                raise Exception(err)
    return wrapped


#获取存储职位信息的json对象，遍历获得公司名、公司规模、福利待遇、学历要求、发布时间、职位名称、薪资、工作年限等
@conn_try_again
def get_json(url, datas, city, pageNum):

    ua = UserAgent()
    my_headers = {
        'User-Agent': ua.random ,
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'zh-CN,zh;q=0.8,zh-TW;q=0.6,ja;q=0.4,en;q=0.2',
        'Host': 'www.lagou.com',
        'Origin': 'https://www.lagou.com',
        'Referer': 'https://www.lagou.com/jobs/list_' + quote(datas['kd']) + '?city=' + quote(city) + '&cl=false&fromSearch=true&labelWords=&suginput=',
    }
    cookies = {
        'Cookie': '***' #这里填你用Chrome浏览器F12看到的请求头中的Cookie
    }

    try:
        # time.sleep(5 + random.randint(0,5))
        print('----正在抓取第' + str(pageNum) + '页----')
        content = requests.post(url=url,cookies=cookies,headers=my_headers,data=datas)
        # content.encoding = 'utf-8'
        result = content.json()
        # print(result)
        info = result['content']['positionResult']['result']
        if(pageNum == 1):
            global maxPage
            maxPage = math.ceil(result['content']['positionResult']['totalCount'] / result['content']['pageSize'])
        info_list = []
        for job in info:
            information = []
            information.append(job['positionId']) #岗位对应ID
            information.append(job['companyFullName']) #公司全名
            information.append(job['companySize']) #公司规模
            information.append(job['financeStage']) #融资情况
            
            # 福利待遇
            tempList = list(filter(lambda x: x != '""', job['companyLabelList'])) #过滤掉['""']的情况
            if(len(tempList)):
                companyLabelList = ",".join(tempList)
                information.append(companyLabelList)
            else:
                information.append('')
            
            information.append(job['district']) #工作地点
            information.append(job['education']) #学历要求

            information.append(datas['kd']) #行业

            information.append(job['createTime']) #发布时间
            information.append(job['positionName']) #职位名称
            
            #薪资
            if(re.match(r'([1-9]\d*)k\-([1-9]\d*)k', job['salary']) != None):
                tempSalary = job['salary'].split('-')
                information.append(tempSalary[0])
                information.append(tempSalary[1])
            else:
                information.append(job['salary'])
                information.append(job['salary'])
            
            information.append(job['workYear']) #工作年限
            info_list.append(information)
            #将列表对象进行json格式的编码转换,其中indent参数设置缩进值为2
            # print(json.dumps(info_list,ensure_ascii=False,indent=2))
            # print(info_list)
        return info_list
    except Exception as e:
        # print(e)
        # print('正在重连.............................................')
        # get_json(url, datas, city, pageNum)
        return None

def main():
    # 连接数据库
    conn = mysql.connector.connect(user='***', password='***', database='recruit')  #这里到时根据自己的mysql用户名和密码填，recruit是我当时的数据库名
    cursor = conn.cursor()

    #获取所有城市
    cursor.execute('select name from cities_lagou')
    result1 = cursor.fetchall()#获取查询结果
    for cityName in result1:
        # 获取所有行业
        cursor.execute('select name from industry_lagou')
        result2 = cursor.fetchall()#获取查询结果
        for i,industryName in enumerate(result2):
            # print(industryName[0])
            print('--------正在爬取【' + cityName[0] + '】:' + industryName[0] + '--------')
            global maxPage
            maxPage = 1
            # kd = input('请输入你要抓取的职位关键字：')
            # city = input('请输入你要抓取的城市：')
            city = cityName[0]
            info_result = []
            url = 'https://www.lagou.com/jobs/positionAjax.json?city=' + quote(city) + '&needAddtionalResult=false'

            # 请求第一页主要是为了拿到最大请求页数
            datas = {
                'first': True,
                'pn': maxPage,
                'kd': industryName[0]
            }
            info = get_json(url, datas, city, maxPage)
            if info is None:
                i -= 1
                continue
            info_result = info_result + info

            if(maxPage <= 1):
                # 插入数据库
                for col in info_result:
                    cursor.execute('insert into jobs_lagou (jobId, companyName, companyScale, financeStage, welfare, district, education, industry, createTime, jobName, salaryLow, salaryHigh, experience, city) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [col[0], col[1], col[2], col[3], col[4], col[5], col[6], col[7], col[8], col[9], col[10], col[11], col[12], city])
                # 提交事务
                conn.commit()
                continue
                # return None
            # if(maxPage > 30):
            #     maxPage = 30

            for j,x in enumerate(range(2, maxPage + 1)):
                datas = {
                    'first': True,
                    'pn': x,
                    'kd': industryName[0]
                }
                info = get_json(url, datas, city, x)
                if info is None:
                    j -= 1
                    continue
                info_result = info_result + info

            # 插入数据库
            for col in info_result:
                cursor.execute('insert into jobs_lagou (jobId, companyName, companyScale, financeStage, welfare, district, education, industry, createTime, jobName, salaryLow, salaryHigh, experience, city) values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)', [col[0], col[1], col[2], col[3], col[4], col[5], col[6], col[7], col[8], col[9], col[10], col[11], col[12], city])
            # 提交事务
            conn.commit()
    
    # 关闭数据库连接
    cursor.close()

if __name__ == '__main__':
    main()