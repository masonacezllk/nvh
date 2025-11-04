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
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
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

    def search_weather(self, test_time_str):
        search_flag = False
        result = []
        try:
            locale.setlocale(locale.LC_CTYPE, 'Chinese')
            time_format = '%Y-%m-%d %H:%M:%S'
            test_time = datetime.strptime(test_time_str, time_format)
            end_time = test_time+timedelta(hours=1)
            start_time_str = test_time.strftime('%Y年%m月%d日 %H:%M:%S')
            end_time_str = end_time.strftime('%Y年%m月%d日 %H:%M:%S')

            # 公钥
            public_key = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCPtdA0WIaLsALHq7eIdHShGolrtakyzACY/m9zNU+qFTAbjWX3iIFGqtOwAkTEUaEvjU97Kv4m3g71wM6zeLCcED0WUdYBS7XHr4SDagOJByJxcMs44iboDd2avw/bn4eQlAcR35qV389Xrm+FSmQRqmqY4ygX61THOTRxtjGu4wIDAQAB"

            # 将公钥转换为RSA对象
            rsa_key = RSA.import_key(base64.b64decode(public_key))

            # 创建加密对象
            cipher = PKCS1_v1_5.new(rsa_key)

            # 用户名和密码
            user_name = "nastuser"
            pwd = "NAST@0710"

            # 加密用户名和密码
            send_name = base64.b64encode(
                cipher.encrypt(user_name.encode())).decode()
            send_pwd = base64.b64encode(cipher.encrypt(pwd.encode())).decode()

            loginHead = self.sysHeadGen(Authorization='',
                                        cookie='',
                                        host='www.xy12121.cn:10087',
                                        referer='http://www.xy12121.cn:10087/Login.aspx',
                                        userName='',
                                        windowHash='',
                                        windowHref=''
                                        )
            loginUrl = "http://www.xy12121.cn:10087/Login.aspx/CheckUser"
            loginJson = {"userName": send_name, "pwd": send_pwd}
            loginRes = requests.post(
                loginUrl, headers=loginHead, json=loginJson, timeout=10)

            sessionId = loginRes.cookies._cookies['www.xy12121.cn']['/']['ASP.NET_SessionId'].value

            searchHead = self.sysHeadGen(Authorization='',
                                         cookie='ASP.NET_SessionId='+sessionId,
                                         host='www.xy12121.cn:10087',
                                         referer='http://www.xy12121.cn:10087/Live/NASTQuery.aspx',
                                         userName='',
                                         windowHash='',
                                         windowHref=''
                                         )
            searchUrl = 'http://www.xy12121.cn:10087/Live/NAST.aspx/QueryData'
            searchJson = {
                'dataType': 'minute',
                'start': start_time_str,
                'end': end_time_str,
                'page': 1,
                'statId': 'F3004'
            }
            searchRes = requests.post(
                searchUrl, headers=searchHead, json=searchJson, timeout=10)
            results = json.loads(searchRes.text)
            weather = results['d']['RecordList'][0]
            result = []
            # 时间
            test_time_obj = datetime.fromtimestamp(
                int(weather['ObservTime'][6:-2])/1000)
            sTime = test_time_obj.strftime('%H:%M')
            result.append(sTime)
            # 温度
            sTemperature = float(weather['TMP'])/10
            sTemperature = str(np.round(sTemperature, 1))
            result.append(sTemperature)
            # 湿度
            shumidity = float(weather['RHU'])
            shumidity = str(np.round(shumidity, 1))
            result.append(shumidity)
            # 气压 hPa->kPa
            sPressure = float(weather['PRS'])/100
            sPressure = str(np.round(sPressure, 1))
            result.append(sPressure)
            # 风向
            sd = float(weather['WIN_D_Avg_2mi_160cm'])
            if sd > 337.5 or sd < 22.25:
                sDirection = '北风'

            if sd > 22.25 and sd < 67.5:
                sDirection = '东北风'

            if sd > 67.5 and sd < 112.5:
                sDirection = '东风'

            if sd > 112.5 and sd < 157.5:
                sDirection = '东南风'

            if sd > 157.5 and sd < 202.5:
                sDirection = '南风'

            if sd > 202.5 and sd < 247.5:
                sDirection = '西南风'

            if sd > 247.5 and sd < 292.5:
                sDirection = '西风'

            if sd > 292.5 and sd < 337.5:
                sDirection = '西北风'

            result.append(sDirection)
            # 风速
            sSpeed = float(weather['WIN_S_Avg_2mi_160cm'])/10
            sSpeed = str(np.round(sSpeed, 1))
            result.append(sSpeed)
            search_flag = True
        except Exception as e:
            result = []
            search_flag = False
        return result, search_flag

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
    
    def download_pdf(self, server_ip, server_port, file_path, output_file):
        # 创建TCP socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        try:
            # 设置连接超时
            s.settimeout(10)
            
            # 连接到服务器
            print(f"正在尝试连接到服务器 {server_ip}:{server_port}...")
            start_time = time.time()
            s.connect((server_ip, server_port))
            connect_time = time.time() - start_time
            print(f"连接成功! 耗时: {connect_time:.2f}秒")
            
            # 设置接收超时
            s.settimeout(5)
            # 尝试多种协议握手方式
            protocols = [
                b"\r\n",  # 空行
                b"HELO\r\n",  # SMTP协议
                b"USER anonymous\r\n",  # FTP协议
                b"GET / HTTP/1.0\r\n\r\n"  # HTTP协议
            ]
            
            for i, protocol in enumerate(protocols):
                print(f"尝试协议 {i+1}/{len(protocols)}...")
                s.settimeout(3)
                try:
                    s.sendall(protocol)
                    response = s.recv(1024)
                    if response:
                        break
                except socket.timeout:
                    print(f"协议 {i+1} 超时")
            else:
                raise Exception("所有尝试的协议均未获得服务器响应")
                    
            # 发送AUTH命令
            auth_command = b"AUTH 001:xierenxixi\r\n"
            s.sendall(auth_command)
            
            # 等待响应
            response = s.recv(1024)
            
            # 发送RETR命令
            retr_command = f"RETR 0 {file_path}\r\n".encode('ascii')
            s.sendall(retr_command)
            
            # 等待准备传输响应
            response = s.recv(1024)
            
            # 接收文件数据
            pdf_data = response  # 可能已经包含部分PDF数据
            total_bytes = 0
            start_time = time.time()
            
            # 尝试从响应中获取文件大小
            if b'213' in response[:4]:  # FTP成功响应码
                try:
                    file_size = int(response.split(b'\r\n')[0].split()[1])+8  # 加8是为了去掉最后的空行和%%EOF
                except:
                    file_size = None
            
            # 设置更大的接收缓冲区和超时
            s.settimeout(60)  # 延长超时时间
            buffer_size = 65536  # 64KB
            last_received = time.time()
            
            while True:
                try:
                    chunk = s.recv(buffer_size)
                    if not chunk:
                        if file_size and total_bytes < file_size * 0.9:
                            raise Exception(f"连接意外关闭，仅收到{total_bytes}字节")
                        break
                        
                    pdf_data += chunk
                    total_bytes += len(chunk)
                    last_received = time.time()
                    
                    # 进度报告
                    if file_size:
                        percent = (total_bytes / file_size) * 100
                        print(f"已接收: {total_bytes}/{file_size}字节 ({percent:.1f}%)", end='\r')
                    
                    # 检查PDF文件头和结尾
                    if len(pdf_data) >= 4:
                        if len(pdf_data) >= file_size:
                            print("\n收到完整PDF文件")
                            break
                        if time.time() - last_received > 2:
                            raise Exception("30秒内未收到新数据")
                        
                except socket.timeout:
                    if b'%PDF' in pdf_data:
                        if pdf_data.endswith(b'%%EOF\n'):
                            print("\n收到完整PDF文件结尾标记")
                            break
                        elif file_size and abs(len(pdf_data) - file_size) <= 8:
                            print("\n收到接近完整的PDF文件(差异小于8字节)")
                            break
                        elif file_size and len(pdf_data) > file_size * 0.99:
                            print(f"\n收到99%以上的文件内容({len(pdf_data)}字节)")
                            break
                    print(f"警告: 接收数据超时，已接收{total_bytes}字节")
                    if b'%PDF' in pdf_data:
                        break
                    raise Exception("未能接收到有效的PDF文件头")
                
            # 保存文件
            with open(output_file, 'wb') as f:
                f.write(pdf_data)
                
            print(f"PDF文件已成功保存到 {output_file}")
            
        except socket.timeout:
            print("错误: 连接超时，请检查网络或服务器状态")
        except ConnectionRefusedError:
            print("错误: 连接被拒绝，服务器可能未运行或端口错误")
        except UnicodeDecodeError:
            print("注意: 服务器返回了二进制数据，跳过ASCII解码")
        except Exception as e:
            print(f"发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            s.close()

    def get_pdf_msid(self, uuid):
        # 配置请求参数
        url = "http://192.168.133.24:8081/api/db_query"
        headers = {
            "Connection": "keep-alive",
            "Host": "192.168.133.24:8081",
            "Content-Type": "application/msgpack",
            "Accept": "application/msgpack",
            "Accept-Encoding": "zlib",
            "Cookie": "diocp_sid=diocp_sid_CECD4F7351B746A9819CA8477D56354C"
        }
        
        sql_query = f"SELECT bzyqsyb.*, bzyqb.yqbh, bzyqb.yqmc, bzyqb.ccbh FROM bzyqsyb, bzyqb WHERE bzyqsyb.yqid = bzyqb.sid AND bzyqsyb.yqid = '{uuid}' ORDER BY bzyqb.yqmc ASC, bzyqsyb.jdrq DESC;"
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
        msid=[]
        fname=[]
        for row in decoded_content['main']['rows']:
            wholename=row['docname'].split('\r\n')
            for name in wholename:
                if len(name)>1:
                    temp=name.split(';')
                    sid=temp[0]
                    msid.append(sid)
                    fname.append(temp[1])

        return msid,fname
