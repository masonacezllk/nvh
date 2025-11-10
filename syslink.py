import pandas as pd
import requests
import json
import base64
import os
from datetime import datetime

# 系统URL配置 - 使用环境变量，默认为内网地址
SYS_BASE_URL = os.environ.get('SYS_BASE_URL', 'http://192.168.133.34:8181')
TASK_BASE_URL = os.environ.get('TASK_BASE_URL', 'http://192.168.133.34:7070')


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
            captchIamgeUrl = f'{SYS_BASE_URL}/ssiboot/admin/captchaImage'
            captchHost = SYS_BASE_URL.replace('http://', '')
            captchReferer = f'{SYS_BASE_URL}/'
            captchIamgeHead = self.sysHeadGen(None, None, captchHost, captchReferer, 'undefined', '/login',
                                              f'{SYS_BASE_URL}/#/login')
            captchIamgeRes = requests.get(
                captchIamgeUrl, headers=captchIamgeHead, timeout=10)
            captchIamgeText = json.loads(captchIamgeRes.text)

            # 登录任务单系统
            loginUrl = f'{SYS_BASE_URL}/ssiboot/admin/login'

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
        url = f"{SYS_BASE_URL}/ssiboot/admin/getInfo"
        headers = {
            "accept": "application/json, text/plain, */*",
            "accept-encoding": "gzip, deflate",
            "accept-language": "zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6",
            "authorization": loginAuthorization,
            "cache-control": "no-cache",
            "connection": "keep-alive",
            "cookie": "Authorization="+loginAuthorization,
            "pragma": "no-cache",
            "referer": f"{SYS_BASE_URL}/",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/137.0.0.0 Safari/537.36 Edg/137.0.0.0",
            "version": "v0.3.0",
            "windowhash": "/login",
            "windowhref": f"{SYS_BASE_URL}/#/login"
        }
        response = requests.get(url, headers=headers)
        user_info = json.loads(response.text)
        return user_info

    def get_task_list(self, loginAuthorization, username):
        searchTaskUrl = f'{TASK_BASE_URL}/ssiboot/admin/nast/test/result/list'
        searchTaskHost = TASK_BASE_URL.replace('http://', '')
        searchTaskReferer = f'{TASK_BASE_URL}/'
        searchTaskHash = '/checkAndTest/triallResManage'
        searchTaskHerf = f'{TASK_BASE_URL}/#/checkAndTest/triallResManage'
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

        searchTaskText = task_result
        # 获取报告号列表
        searchTaskHost = TASK_BASE_URL.replace('http://', '')
        searchTaskReferer = f'{TASK_BASE_URL}/'
        searchTaskCookie = 'Authorization=' + loginAuthorization

        taskOrderId = searchTaskText['rows'][idx]['taskOrderId']
        taskDepartmentId = searchTaskText['rows'][idx]['taskDepartmentId']
        taskDepartmentSub = searchTaskText['rows'][idx]['departmentTaskOrderSub']
        checkTypeId = searchTaskText['rows'][idx]['checkTypeId']
        projectTypeId = searchTaskText['rows'][idx]['projectTypeId']
        taskOrderName = searchTaskText['rows'][idx]['taskOrderName'].encode(
            'utf-8').decode('latin-1')
        reportUrl = f'{TASK_BASE_URL}/ssiboot/admin/reportcode/querymakereport?taskOrderId=' + \
            taskOrderId + '&taskDepartmentId=' + taskDepartmentId
        reportHash = '/checkAndTest/triallResManage/report'
        reportHerf = f'{TASK_BASE_URL}/#/checkAndTest/triallResManage/report?taskOrderId=' + \
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
            infoUrl = f'{TASK_BASE_URL}/ssiboot/admin/nast/test/schedule/taskOrderInfo/' + \
                taskDepartmentId + '/' + taskOrderId
            infoHash = '/taskManagement/detail'
            infoHerf = f'{TASK_BASE_URL}/#/taskManagement/detail?departmentId=' + taskDepartmentId + \
                '&taskOrderId=' + taskOrderId + '&from=/checkAndTest/trialExcution'
            infoHead = self.sysHeadGen(loginAuthorization, searchTaskCookie, searchTaskHost, searchTaskReferer,
                                        username, infoHash, infoHerf)
            infoRes = requests.get(infoUrl, headers=infoHead, timeout=10)
            infoText = json.loads(infoRes.text)

            # 查询订单信息
            orderUrl = f'{TASK_BASE_URL}/ssiboot/admin/nast/order/' + str(infoText['data']['orderId'])
            orderHash = '/taskManagement/detail'
            orderHerf = f'{TASK_BASE_URL}/#/taskManagement/detail?departmentId=' + taskDepartmentId + \
                '&taskOrderId=' + taskOrderId + '&from=/taskManagement/taskTracking'
            orderHead = self.sysHeadGen(loginAuthorization, searchTaskCookie, searchTaskHost, searchTaskReferer,
                                        username, orderHash, orderHerf)
            orderRes = requests.get(orderUrl, headers=orderHead, timeout=10)
            orderText = json.loads(orderRes.text)

            # 查询试验员
            testerUrl = f'{TASK_BASE_URL}/ssiboot/admin/task/tracking/detail/' + taskDepartmentId
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
