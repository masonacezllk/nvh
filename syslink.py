import xml.etree.ElementTree as ET
import struct
import pandas as pd
import numpy as np
import requests
import glob
import json
import shutil
import optparse
import base64
from datetime import datetime, timedelta
import pandas as pd
import locale
import numpy as np
from numpy import pi, polymul
import os,re
import time,requests
import json,math
from collections import Counter
from textwrap import fill
import io
import zlib
import socket
import msgpack
from concurrent.futures import ProcessPoolExecutor,ThreadPoolExecutor


class SysLink:
    def __init__(self):
        self.loginAuthorization = None
        self.task_result = None

    def login(self, username, passwordin):
        loginAuthorization = None
        task_number_list = None
        task_result = None
        login_flag = False
        login_msg=''

        try:
            # 生成验证码
            captchIamgeUrl = 'http://192.168.133.34:8181/ssiboot/admin/captchaImage'
            captchHost = '192.168.133.34:8181'
            captchReferer = 'http://192.168.133.34:8181/'
            captchIamgeHead = self.sysHeadGen(None, None, captchHost, captchReferer, 'undefined', '/login',
                                              'http://192.168.133.34:8181/#/login')
            captchIamgeRes = requests.get(
                captchIamgeUrl, headers=captchIamgeHead, timeout=10)
            captchIamgeText = json.loads(captchIamgeRes.text)

            # 登录任务单系统
            loginUrl = 'http://192.168.133.34:8181/ssiboot/admin/login'

            passwordo = passwordin + datetime.now().strftime('%Y%m%d')
            password = str(base64.b64encode(
                bytes(passwordo, 'utf-8')), encoding='utf-8')
            code = captchIamgeText['data']['uuid']
            uuid = captchIamgeText['data']['uuid']

            loginJson = {'code': code,
                         'username': username,
                         'password': password,
                         'uuid': uuid}

            loginRes = requests.post(loginUrl, json=loginJson, timeout=10)

            loginText = json.loads(loginRes.text)
            login_msg=loginText['msg']
            if loginText['code'] == 200:
                login_flag = True
                loginAuthorization = loginText['data']
                self.loginAuthorization = loginAuthorization
                task_number_list, task_result = self.get_task_list(self.loginAuthorization, username)
            else:
                login_flag = False
                print(loginText['msg'])
        except:
            login_flag = False
            login_msg='任务单系统登录失败，检查中台系统网络连接'
            print('任务单系统登录失败，检查中台系统网络连接')

        return loginAuthorization, task_number_list, task_result, login_flag,login_msg

    def sysHeadGen(self, Authorization, cookie, host, referer, userName, windowHash, windowHref):
        sysHead = {'Accept': 'application/json, text/plain, */*',
                   'Accept-Encoding': 'gzip, deflate',
                   'Accept-Language': 'zh-CN,zh;q=0.9',
                   'Authorization': Authorization,
                   'Cookie': cookie,
                   'Connection': 'keep-alive',
                   'Host': host,
                   'Referer': referer,
                   'Content-Type': 'application/json',
                   'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                   'Username': userName,
                   'Version': 'v0.3.0',
                   'Windowhash': windowHash,
                   'Windowhref': windowHref}
        return sysHead

    def get_user_info(self, loginAuthorization):
        url = "http://192.168.133.34:8181/ssiboot/admin/getInfo"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "authorization": loginAuthorization,
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "cookie": "Authorization="+loginAuthorization,
            "pragma": "no-cache",
            "referer": "http://192.168.133.34:8181/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "version": "v0.3.0",
            "windowhash": "/login",
            "windowhref": "http://192.168.133.34:8181/#/login"
        }
        response = requests.get(url, headers=headers)
        user_info = json.loads(response.text)
        return user_info

    def get_task_list(self, loginAuthorization, username):
        searchTaskUrl = 'http://192.168.133.34:7070/ssiboot/admin/nast/test/result/list'
        searchTaskHost = '192.168.133.34:7070'
        searchTaskReferer = 'http://192.168.133.34:7070/'
        searchTaskHash = '/checkAndTest/triallResManage'
        searchTaskHerf = 'http://192.168.133.34:7070/#/checkAndTest/triallResManage'
        searchTaskCookie = 'Authorization=' + loginAuthorization
        searchTaskHead = self.sysHeadGen(loginAuthorization, searchTaskCookie, searchTaskHost, searchTaskReferer,
                                         username, searchTaskHash, searchTaskHerf)
        searchTaskJson = {"pageNum": 1, "pageSize": 15, "status": [40, 50, 55, 56]}
        searchTaskRes = requests.post(
            searchTaskUrl, headers=searchTaskHead, json=searchTaskJson, timeout=10)
        task_result = json.loads(searchTaskRes.text)

        task_number_list = []
        if task_result['code'] == 200:
            for j in range(len(task_result['rows'])):
                temp = task_result['rows'][j]['departmentTaskOrderSub'][:16]
                task_number_list.append(temp)                    
        else:
            print(task_result['msg'])

        return task_number_list, task_result

    def load_task(self, loginAuthorization, username, idx, task_result):
        table_data = []
        report_number = []
        report_item_name = []
        check_flag = False
        try:
            searchTaskText = task_result
            # 获取报告号列表
            searchTaskHost = '192.168.133.34:7070'
            searchTaskReferer = 'http://192.168.133.34:7070/'
            searchTaskCookie = 'Authorization=' + loginAuthorization

            taskOrderId = searchTaskText['rows'][idx]['taskOrderId']
            taskDepartmentId = searchTaskText['rows'][idx]['taskDepartmentId']
            taskDepartmentSub = searchTaskText['rows'][idx]['departmentTaskOrderSub']
            checkTypeId = searchTaskText['rows'][idx]['checkTypeId']
            projectTypeId = searchTaskText['rows'][idx]['projectTypeId']
            taskOrderName = searchTaskText['rows'][idx]['taskOrderName'].encode(
                'utf-8').decode('latin-1')
            reportUrl = 'http://192.168.133.34:7070/ssiboot/admin/reportcode/querymakereport?taskOrderId=' + \
                taskOrderId + '&taskDepartmentId=' + taskDepartmentId
            reportHash = '/checkAndTest/triallResManage/report'
            reportHerf = 'http://192.168.133.34:7070/#/checkAndTest/triallResManage/report?taskOrderId=' + \
                taskOrderId + '&taskDepartmentId=' + taskDepartmentId + \
                '&taskDepartmentSub=' + taskDepartmentSub + '&taskOrderName=' + taskOrderName
            reportCookie = 'Authorization=' + loginAuthorization
            reportHead = self.sysHeadGen(loginAuthorization, reportCookie, searchTaskHost, searchTaskReferer, username,
                                         reportHash, reportHerf)
            reportRes = requests.get(reportUrl, headers=reportHead, timeout=10)
            reportText = json.loads(reportRes.text)
            if reportText['code'] == 200:
                # 加载报告号
                report_list = reportText['data']['nastTaskDeptVos'][0]['nastTaskDeptCheckItemVos']
                report_number = []
                report_item_name = []
                for j in range(len(report_list)):
                    try:
                        cur_item = report_list[j]['checkReportDtos']
                        report_item_name.append(
                            report_list[j]['checkItemName'])
                        for k in range(len(cur_item)):
                            report_number.append(cur_item[k]['reportCode'])

                    except:
                        temp = 0

                # 查询任务单信息
                infoUrl = 'http://192.168.133.34:7070/ssiboot/admin/nast/test/schedule/taskOrderInfo/' + \
                    taskDepartmentId + '/' + taskOrderId
                infoHash = '/taskManagement/detail'
                infoHerf = 'http://192.168.133.34:7070/#/taskManagement/detail?departmentId=' + taskDepartmentId + \
                    '&taskOrderId=' + taskOrderId + '&from=/checkAndTest/trialExcution'
                infoHead = self.sysHeadGen(loginAuthorization, searchTaskCookie, searchTaskHost, searchTaskReferer,
                                           username, infoHash, infoHerf)
                infoRes = requests.get(infoUrl, headers=infoHead, timeout=10)
                infoText = json.loads(infoRes.text)

                # 查询订单信息
                orderUrl = 'http://192.168.133.34:7070/ssiboot/admin/nast/order/' + str(infoText['data']['orderId'])
                orderHash = '/taskManagement/detail'
                orderHerf = 'http://192.168.133.34:7070/#/taskManagement/detail?departmentId=' + taskDepartmentId + \
                    '&taskOrderId=' + taskOrderId + '&from=/taskManagement/taskTracking'
                orderHead = self.sysHeadGen(loginAuthorization, searchTaskCookie, searchTaskHost, searchTaskReferer,
                                           username, orderHash, orderHerf)
                orderRes = requests.get(orderUrl, headers=orderHead, timeout=10)
                orderText = json.loads(orderRes.text)

                # 查询试验员
                testerUrl = 'http://192.168.133.34:7070/ssiboot/admin/task/tracking/detail/' + taskDepartmentId
                testerRes = requests.get(
                    testerUrl, headers=infoHead, timeout=10)
                testerText = json.loads(testerRes.text)

                if infoText['code'] == 200 and testerText['code'] == 200:
                    check_flag = True
                    table_data = self.refresh_task(infoText, testerText, orderText)
                else:
                    check_flag = False
                    print(infoText['msg'] + ' ' + testerText['msg'])
            else:
                check_flag = False
                print(reportText['msg'])
        except:
            check_flag = False
            print('任务单信息刷新失败.')
        return table_data, report_number, report_item_name, check_flag

    def refresh_task(self, infoText, testerText,orderText):
        testerName = testerText['data']['checkItemList'][0]['testerName']
        info_res = infoText['data']
        phone_pd = pd.read_excel(r'tables\informations.xlsx', 'Phone')
        # 查询项目经理电话
        phone_number1 = ''
        phone_number = phone_pd[phone_pd['姓名'] == orderText['data']['order']['projectLeader']]['电话'].values
        if len(phone_number) == 0:
            phone_number1 = orderText['data']['order']['projectLeader']
        else:
            phone_number1 = str(phone_number[0])
        
        # 支持多个样车信息
        sample_infos = orderText['data']['sampleInfos']
        carInfo = []
        
        for j in range(len(sample_infos)):
            sample_info = sample_infos[j]
            carInfo.append({
                '开发平台': sample_info['name'],
                '品牌': sample_info['agencyBrand'],
                '整车型号': sample_info['model'],
                '样车编号': sample_info['vin'],
                '载荷类型': '1'  # 默认载荷类型
            })
        
        table_data = {
            '任务单编号': info_res['taskOrderNo'],
            '委托书编号': orderText['data']['order']['clientLetterNo'],
            '任务单名称': info_res['taskOrderName'],
            '委托单位名称': orderText['data']['nastConsumerClient']['company'],
            '委托单位地址': orderText['data']['nastConsumerClient']['companyAddress'],
            '委托人联系电话': orderText['data']['nastConsumerClient']['nastConsumerTel'],
            '项目经理电话': phone_number1,
            '试验员': testerName,
            '开发平台': orderText['data']['order']['developPlatform'],
            'carInfo': carInfo,  # 使用carInfo字段与现有系统兼容
        }

        return table_data
 
    def device_system_search(self,keyword):
        # 计量系统
        url = "http://192.168.133.24:8081/api/dssAuthentication/shake"
        headers = {
            "Connection": "keep-alive",
            "Host": "192.168.133.24:8081",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        # 请求体的内容
        data = {
            "authentication": "MDAxOjEyMw=="
        }

        # 发送POST请求
        response = requests.post(url, headers=headers, json=data)

        # 打印响应内容
        response_data=json.loads(response.text)


        url = "http://192.168.133.24:8081/api/db_query"
        headers = {
            "Connection": "keep-alive",
            "Cookie": "diocp_sid=diocp_sid_24C9F39128064CC38F25155F4886E0CB;",
            "Host": "192.168.133.24:8081",
            "Content-Type": "application/msgpack",
            "Accept-Encoding": "zlib",
            "Accept": "application/msgpack",
            "apicode": response_data['apicode']
        }

        # 选中的SQL查询语句
        sql_query = "select  bzyqsyb_max_view.jdrq as jdsj1 ,bzyqsyb_max_view.jdzq,bzyqsyb_max_view.yxrq as yqrq ,bzyqsyb_max_view.zsbh as zsh1 ,bzyqsyb_max_view.jdjg as jdsj2,     isnull(ylyl ,0)-isnull(yqlqb_view.scnt,0)   as sysl,  yqlqb_view.scnt as lqzt,jddw1,yqbh, yqmc, yqmc1, qhgg, bqdd, bqdd1, zzc, glsj,  zsh2,   jddw2, zsh3, jdsj3, jddw3, dj, bgz, ksdm, yjts, by1, dyxz, zsh4, jdsj4,   jddw4, ccbh, fdz, clfw, dwbh,ylyl,syl1,syl2,syl3,syl4,syl5, bgsm, bzyqb.by2, bzyqb.by3,by4,by5,bzyqb.by6,bzyqb.by7,c.by2 as ycz1,c.by3 as ycz2, sid, docname, docname1, yqmcyw, bqddyw,bzlrrq,bzlrry ,dbo.[DateDifffto]('',case when jddw2='3' then bzyqb.yqrq else  bzyqsyb_max_view.yxrq end ) as gqts  from bzyqb left join (select * from (select yqid, ROW_NUMBER() over (partition by yqid order by jdrq desc ) as pxh ,by2 ,by3 from bzyqsyb ) b where b.pxh=1) c on c.yqid=bzyqb.sid left join yqlqb_view on yqlqb_view.wjid=bzyqb.sid left join bzyqsyb_max_view on bzyqsyb_max_view.yqid=bzyqb.sid where 1=1  and ( ((bzyqb.bgz like '%%" + keyword+"%%') or (bzyqb.bqdd like '%%"+keyword+"%%') or (bzyqb.bqdd1 like '%%"+keyword+"%%') or (bzyqb.bqddyw like '%%"+keyword+"%%') or (bzyqb.by1 like '%%"+keyword+"%%') or (bzyqb.by2 like '%%"+keyword+"%%') or (bzyqb.by3 like '%%"+keyword+"%%') or (bzyqb.by4 like '%%"+keyword+"%%') or (bzyqb.by5 like '%%"+keyword+"%%') or (bzyqb.by6 like '%%"+keyword+"%%') or (bzyqb.by7 like '%%"+keyword+"%%') or (bzyqb.bzlrrq like '%%" + \
            keyword+"%%') or (bzyqb.bzlrry like '%%"+keyword+"%%') or (bzyqb.ccbh like '%%"+keyword+"%%') or (bzyqb.clfw like '%%"+keyword+"%%') or (bzyqb.dj like '%%"+keyword+"%%') or (bzyqb.dwbh in (select sid from rjsydwb where dwmc like '%%"+keyword+"%%')) or (bzyqb.dyxz like '%%"+keyword+"%%') or (bzyqb.fdz like '%%"+keyword+"%%') or (bzyqb.glsj like '%%"+keyword+"%%') or (bzyqb.jddw1 like '%%"+keyword+"%%') or (bzyqb.jddw3 like '%%"+keyword+"%%') or (bzyqb.jddw4 like '%%"+keyword+"%%') or ((case when jddw2='3' then  bzyqb.jdsj1 else  bzyqsyb_max_view.jdrq end) like '%%"+keyword+"%%') or ((case when jddw2='3' then bzyqb.jdsj2 else  bzyqsyb_max_view.jdjg  end)   like '%%"+keyword+"%%') or (bzyqb.jdsj3 like '%%" + \
            keyword+"%%') or (bzyqb.ksdm like '%%"+keyword+"%%') or (bzyqb.qhgg like '%%"+keyword+"%%') or (bzyqb.yjts like '%%"+keyword+"%%') or (bzyqb.yqbh like '%%"+keyword+"%%') or (bzyqb.yqmc like '%%"+keyword+"%%') or (bzyqb.yqmc1 like '%%"+keyword+"%%') or (bzyqb.yqmcyw like '%%"+keyword+"%%') or ((case when jddw2='3' then bzyqb.yqrq else  bzyqsyb_max_view.yxrq end) like '%%" + \
            keyword+"%%') or ((case when jddw2='3' then bzyqb.zsh1 else  bzyqsyb_max_view.zsbh end)  like '%%"+keyword+"%%') or (bzyqb.zsh3 like '%%"+keyword+"%%') or (bzyqb.zzc like '%%" + \
            keyword + \
            "%%'))) and (isnull(zsh4,'') not in ('3','5','1')) and (isnull(bzyqb.jddw2,'')<>'3') and (isnull(bzyqb.jddw2,'')<>'4') order by bzyqb.yqbh asc"
        # 假设请求体是一个msgpack对象，你需要提供具体的msgpack数据
        data = {
            "datasource":"xdamis",
            "list": [{
                'id': 'main',
            'sql': {
                'script': sql_query,
            },
            }]}

        # 将数据打包成msgpack格式
        msgpack_data = msgpack.packb(data, use_bin_type=True)

        # 发送POST请求
        response = requests.post(url, headers=headers, data=msgpack_data)
        content = response.content
        # 检查是否需要解压
        if content.startswith(b'x\x9c'):  # zlib 压缩数据的常见前缀
            try:
                content = zlib.decompress(content)
                # print("解压后的数据：", content)
            except Exception as e:
                print("解压失败：", e)

        # 解码msgpack数据
        decoded_content = msgpack.unpackb(content, raw=False, use_list=False, strict_map_key=False)
        return decoded_content
    
