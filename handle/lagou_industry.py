#-*- coding: utf-8 -*-
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
import mysql.connector

def get_industry():
    '''
    获取网页html内容并返回
    '''
    ua = UserAgent()
    headers = {
        'User-Agent': ua.random ,
        'Accept': '*/*',
        'Accept-Encoding': 'gzip, deflate, br',
        'Accept-Language': 'zh-CN,zh;q=0.9',
        'Host': 'www.lagou.com',
        'Referer': 'https://www.lagou.com/',
    }
    cookies = {
        'Cookie': '***' #这里填你用Chrome浏览器F12看到的请求头中的Cookie
    }

    url = 'https://www.lagou.com'
    try:
        # 获取网页内容，返回html数据
        response = requests.get(url, headers=headers)
        # 通过状态码判断是否获取成功
        if response.status_code == 200:
            # print(response.text)
            save_datas(response.text)
        return None
    except Exception as e:
        print(e)
        print('请求失败~')
        # return None

def save_datas(html):
    # 连接数据库
    conn = mysql.connector.connect(user='***', password='***', database='recruit')  #这里到时根据自己的mysql用户名和密码填，recruit是我当时的数据库名
    cursor = conn.cursor()
    # 先清空原本数据
    cursor.execute('delete from industry_lagou')

    soup = BeautifulSoup(html, 'html.parser')
    # 解析招聘列表
    for div in soup.find_all('div', class_='menu_sub'):
        for dl in div.find_all('dl'):
            for a in dl.find('dd').find_all('a'):
                industry_name = a.get_text()
                cursor.execute('insert into industry_lagou (name) values (%s)', [industry_name])

    # 提交事务
    conn.commit()
    cursor.close()

    print('数据插入成功！')

def main():
    '''
    主函数
    '''
    get_industry()

if __name__ == '__main__':
    main()