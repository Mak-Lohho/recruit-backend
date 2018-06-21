#-*- coding: utf-8 -*-
import mysql.connector
import re

def main():
    # 连接数据库
    conn = mysql.connector.connect(user='***', password='***', database='recruit')  #这里到时根据自己的mysql用户名和密码填，recruit是我当时的数据库名
    cursor = conn.cursor()
    
    cursor.execute('select name from cities_lagou')
    cities = cursor.fetchall()
    for i,city in enumerate(cities):
        tempCity = city[0] #城市

        cursor.execute('select districts from cities_lagou where name ="' + tempCity + '"')
        districts = cursor.fetchone()[0]
        
        cursor.execute('select name from industry_lagou')
        industries = cursor.fetchall()
        for j,industry in enumerate(industries):
            tempIndustry = industry[0] #数据库中已有的职位关键字
            
            print('----【' + tempCity + '】:' + tempIndustry + '----')
            # 各区招聘需求分析
            cursor.execute('select district,count(district) as cnt from jobs_lagou where district is not null and city="' + tempCity + '" and industry="' + tempIndustry + '" group by district')
            demandList = cursor.fetchall()
            tempDemand = ''
            for district in districts.split(','):
                hasAdd = False
                for k,demand in enumerate(demandList):
                    if(district == demand[0]):
                        tempDemand += str(demand[1]) + ','
                        hasAdd = True
                    else:
                        if(k == (len(demandList) - 1) and not hasAdd):
                            tempDemand += '0,'
            tempDemand = tempDemand[:-1]
            print(tempDemand)

            # 学历分析
            cursor.execute('select education,count(education) as cnt from jobs_lagou where education is not null and city="' + tempCity + '" and industry="' + tempIndustry + '" group by education')
            educationList = cursor.fetchall()
            tempEducation1 = ''
            tempEducation2 = ''
            tempEducation = ''
            for education in educationList:
                tempEducation1 += education[0] + ','
                tempEducation2 += str(education[1]) + ','
            tempEducation1 = tempEducation1[:-1]
            tempEducation2 = tempEducation2[:-1]
            tempEducation = tempEducation1 + ';' + tempEducation2
            print(tempEducation)

            # 工作经验分析
            cursor.execute('select experience,count(experience) as cnt from jobs_lagou where experience is not null and city="' + tempCity + '" and jobName like "%' + tempIndustry + '%" group by experience')
            experienceList = cursor.fetchall()
            tempExperience1 = ''
            tempExperience2 = ''
            tempExperience = ''
            for experience in experienceList:
                tempExperience1 += experience[0] + ','
                tempExperience2 += str(experience[1]) + ','
            tempExperience1 = tempExperience1[:-1]
            tempExperience2 = tempExperience2[:-1]
            tempExperience = tempExperience1 + ';' + tempExperience2
            print(tempExperience)

            # 各区最低薪酬、最高薪酬、平均薪酬分析
            tempSalaryLow = '' #最低薪酬
            tempSalaryHigh = '' #最高薪酬
            tempAverage = '' #平均薪酬
            for district in districts.split(','):
                #最低薪酬
                cursor.execute('select salaryLow from jobs_lagou where city="' + tempCity + '" and industry="' + tempIndustry + '" and district like "' + district + '%"')
                salaryLowList = cursor.fetchall()
                tempList1 = []
                for salaryLow in salaryLowList:
                    tempList1.append(int(re.sub("\D", "", salaryLow[0].split('-')[0])))
                # print(tempList1)
                if(len(tempList1) < 1):
                    tempList1.append(0)
                tempInt1 = min(tempList1)
                tempSalaryLow += str(tempInt1) + 'k,'

                #最高薪酬
                cursor.execute('select salaryHigh from jobs_lagou where city="' + tempCity + '" and industry="' + tempIndustry + '" and district like "' + district + '%"')
                salaryHighList = cursor.fetchall()
                tempList2 = []
                for salaryHigh in salaryHighList:
                    tList = salaryLow[0].split('-')
                    if(len(tList) > 1):
                        tempList2.append(int(re.sub("\D", "", salaryLow[0].split('-')[1])))
                    else:
                        tempList2.append(int(re.sub("\D", "", salaryLow[0].split('-')[0])))
                if(len(tempList2) < 1):
                    tempList2.append(0)
                tempInt2 = max(tempList2)
                tempSalaryHigh += str(tempInt2) + 'k,'

                #平均薪酬
                allList = tempList1 + tempList2
                tempStr = str(round(sum(allList)/len(allList), 1)).replace('.0', '')
                tempAverage += tempStr + 'k,' 

            tempSalaryLow = tempSalaryLow[:-1] #各区最低薪酬
            tempSalaryHigh = tempSalaryHigh[:-1] #各区最高薪酬
            tempAverage = tempAverage[:-1] #各区平均薪酬
            print(tempSalaryLow)
            print(tempSalaryHigh)
            print(tempAverage)

            #薪酬福利热词
            cursor.execute('select welfare from jobs_lagou where city="' + tempCity + '" and industry="' + tempIndustry + '"')
            welfares = cursor.fetchall()
            welfareStr = ''
            for welfare in welfares:
                welfareStr += welfare[0] + ','
            welfareStr = welfareStr[:-1]
            welfareList = welfareStr.split(',')
            cursor.execute('CREATE TEMPORARY TABLE temp_welfares (name VARCHAR(50) NOT NULL)')
            for w in welfareList:
                if(w == '' or w is None):
                    continue
                cursor.execute('insert into temp_welfares (name) values (%s)', [w])
            cursor.execute('select name,count(name) as cnt from temp_welfares where name is not null group by name order by cnt desc')
            welfareSql = cursor.fetchall()
            maxTimes = 10 #最多取前10条热词
            if(len(welfareSql) < maxTimes):
                maxTimes = len(welfareSql)
            tempName = ''
            tempValue = ''
            for i,tempWelfare in enumerate(welfareSql):
                if(i >= maxTimes):
                    break
                tempName += tempWelfare[0] + ','
                tempValue += str(tempWelfare[1]) + ','
            tempName = tempName[:-1]
            tempValue = tempValue[:-1]
            finalStr = tempName + ';' + tempValue
            print(finalStr)

            cursor.execute('insert into analyses_lagou (keyword, city, salaryLowest, salaryHighest, salaryAverage, demand, education, experience, welfare) values (%s, %s, %s, %s, %s, %s, %s, %s, %s)', [tempIndustry, tempCity, tempSalaryLow, tempSalaryHigh, tempAverage, tempDemand, tempEducation, tempExperience, finalStr])
            cursor.execute('DROP TABLE temp_welfares')
            # 提交事务
            conn.commit()
    
    # 关闭数据库连接
    cursor.close()

if __name__ == '__main__':
    main()