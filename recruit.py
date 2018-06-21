#-*- coding: utf-8 -*-
import mysql.connector
# 连接数据库
conn = mysql.connector.connect(user='***', password='***', database='recruit')  #这里到时根据自己的mysql用户名和密码填，recruit是我当时的数据库名
cursor = conn.cursor(buffered=True)

from flask import Flask
from flask import request
import json
recruit = Flask(__name__, static_url_path='')

# 返回json字符串
def returnJson(dictObj):
    return json.dumps(dictObj, ensure_ascii=False)

@recruit.route('/')
def index():
    return recruit.send_static_file('index.html')

# 返回现有城市
@recruit.route('/recruit/getCities', methods=['GET'])
def get_cities():
    if request.method == 'GET':
        # 查询该市所有区名
        sql_query1 = 'select name from cities_lagou'
        cursor.execute(sql_query1)
        result1 = cursor.fetchall()
        cities = []
        for city in result1:
            cities.append(city[0])

        return returnJson({
            "success": 1,
            "msg": "查找成功！",
            "cities": cities
        })
    return returnJson({
        "success": 0,
        "msg": "请求方式有误：/recruit/getCities"
    })

# 根据搜索关键字返回匹配的行业结果（模糊查询）
@recruit.route('/recruit/matchIndustry', methods=['POST'])
def match_industry():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)

        keyword = dict1["keyword"]

        # 验证接收的数据
        if(keyword == ''):
            return returnJson({
                "success": 0,
                "msg": "请求参数不能为空值：/recruit/matchIndustry"
            })


        # 查询匹配行业结果
        sql_query1 = 'select name from industry_lagou where name like "%' + keyword + '%"'
        cursor.execute(sql_query1)
        result1 = cursor.fetchall()
        industries = []
        for industry in result1:
            industries.append(industry[0])

        # 搜索热度加1
        sql_query2 = 'select keyword from custom_keywords where keyword="' + keyword + '"'
        cursor.execute(sql_query2)
        result2 = cursor.fetchone()
        if(result2 is not None):
            cursor.execute('update custom_keywords set hot=hot+1 where keyword="' + keyword + '"')
            if(cursor.rowcount < 1):
                return returnJson({
                    "success": 0,
                    "msg": "搜索热度更新失败：/recruit/matchIndustry",
                    "industries": []
                })
        else:
            cursor.execute('insert into custom_keywords (keyword, hot) values (%s, %s)', [keyword, 1])
            if(cursor.rowcount < 1):
                return returnJson({
                    "success": 0,
                    "msg": "搜索热度插入失败：/recruit/matchIndustry",
                    "industries": []
                })
        
        # 提交事务
        conn.commit()

        return returnJson({
            "success": 1,
            "msg": "查找成功！",
            "industries": industries
        })
    return returnJson({
        "success": 0,
        "msg": "请求方式有误：/recruit/matchIndustry"
    })

# 返回分析结果
@recruit.route('/recruit/getAnalyse', methods=['POST'])
def get_analyse():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)

        keyword = dict1["keyword"]
        city = dict1["city"]

        # 验证接收的数据
        if(keyword == '' and city == ''):
            return returnJson({
                "success": 0,
                "msg": "请求参数不能为空值：/recruit/getAnalyse"
            })

        # 查询该市所有区名
        sql_query1 = 'select districts from cities_lagou where name="' + city + '"'
        cursor.execute(sql_query1)
        result1 = cursor.fetchone()

        #搜索热度加1
        cursor.execute('update analyses_lagou set hot=hot+1 where keyword="' + keyword + '" and city="' + city + '"')

        # 查询分析结果
        sql_query2 = 'select salaryLowest,salaryHighest,salaryAverage,demand,education,experience,welfare from analyses_lagou where keyword="' + keyword + '" and city="' + city + '"'
        cursor.execute(sql_query2)
        result2 = cursor.fetchone()
        salaryLowest = result2[0].split(",") #各区最低薪酬
        salaryHighest = result2[1].split(",") #各区最高薪酬
        salaryAverage = result2[2].split(",") #各区平均薪酬
        #各区招聘需求
        if(result2[3] == ''):
            demand = []
        else:
            demand = result2[3].split(",")
        #学历要求
        education = result2[4].split(";")
        if(len(education) == 2):
            educationType = education[0].split(",")
            educationValues = education[1].split(",")
        else:
            educationType = []
            educationValues = []
        #工作经验要求
        experience = result2[5].split(";")
        if(len(experience) == 2):
            experienceType = experience[0].split(",")
            experienceValues = experience[1].split(",")
        else:
            experienceType = []
            experienceValues= []
        #福利待遇热词
        welfare = result2[6].split(";")
        if(len(welfare) == 2):
            welfareType = welfare[0].split(",")
            welfareValues = welfare[1].split(",")
        else:
            welfareType = []
            welfareValues = []

        # 提交事务
        conn.commit()

        return returnJson({
            "success": 1,
            "msg": "查找成功！",
            "districts": result1[0].split(","),
            "salaryLowest": salaryLowest,
            "salaryHighest": salaryHighest,
            "salaryAverage": salaryAverage,
            "demand": demand,
            "education": {
                "type": educationType,
                "values": educationValues
            },
            "experience": {
                "type": experienceType,
                "values": experienceValues
            },
            "welfare": {
                "type": welfareType,
                "values": welfareValues
            }
        })
    return returnJson({
        "success": 0,
        "msg": "请求方式有误：/recruit/getAnalyse"
    })

# 保存用户提交的意见反馈
@recruit.route('/recruit/saveSuggestion', methods=['POST'])
def save_suggestion():
    if request.method == 'POST':
        a = request.get_data()
        dict1 = json.loads(a)

        contact = dict1["contact"]
        content = dict1["content"]

        # 验证接收的数据
        if(contact == '' and content == ''):
            return returnJson({
                "success": 0,
                "msg": "请求参数不能为空值：/recruit/saveSuggestion"
            })

        cursor.execute('insert into suggestions (content, contact) values (%s, %s)', [content, contact])
        if(cursor.rowcount < 1):
            return returnJson({
                "success": 0,
                "msg": "意见反馈插入失败：/recruit/saveSuggestion"
            })

        # 提交事务
        conn.commit()

        return returnJson({
            "success": 1,
            "msg": "意见反馈插入成功！"
        })
    return returnJson({
        "success": 0,
        "msg": "请求方式有误：/recruit/saveSuggestion"
    })

if __name__ == '__main__':
    recruit.run()