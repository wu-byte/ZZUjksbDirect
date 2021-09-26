# jksbDirect
#
# By Clok Much
import sys
import json
import smtplib
from email.mime.text import MIMEText

import requests

# ###### 调试区，项目可稳定使用时，两者均应是 False
# 调试开关 正常使用请设定 False ，设定为 True 后会输出更多调试信息，且不再将真实姓名替换为 喵喵喵
debug_switch = False
# 总是认为上报失败的标记 正常使用请设定为 False ，设定为 True 后会每次都发送失败邮件，即使是上报成功
always_fail = False

# 开始时接收传入的 Secrets
user_id = sys.argv[1]
user_pd = sys.argv[2]
mail_id = sys.argv[3]
mail_pd = sys.argv[4]
mail_target = sys.argv[5]
city_code = sys.argv[6]
location = sys.argv[7]
real_name = sys.argv[8]

# 读取开放表单数据
with open("config.json", "rb") as file_obj:
    public_data = json.load(file_obj)
    file_obj.close()

# 创建所有变量方便维护
public_data['myvs_13a'] = city_code[:2]
public_data['myvs_13b'] = city_code
public_data['myvs_13c'] = location
step_1_calc = 0
step_1_output = False
step_1_state = False
step_2_calc = 0
step_2_output = False
step_2_state = False
step_3_calc = 0
step_3_output = False
step_3_state = False
result = 0
result_flag = 0
response = False
mixed_token = False
all_input = sys.argv


# 创建发送邮件的方法
def report_mail(full_info=debug_switch):
    if full_info:
        this_time_vars = {'result_flag': result_flag,
                          'mixed_token': mixed_token,
                          'public_data': public_data,
                          'step_1_output': step_1_output,
                          'step_1_calc': step_1_calc,
                          'step_1_state': step_1_state,
                          'step_2_output': step_2_output,
                          'step_2_calc': step_2_calc,
                          'step_2_state': step_2_state,
                          'step_3_output': step_3_output,
                          'step_3_calc': step_3_calc,
                          'step_3_state': step_3_state,
                          'secrets_inputted': sys.argv,
                          'step_1_post_data': post_data,
                          'result': result
                          }
    else:
        if type(result) == str:
            replaced_result = result.replace(real_name, "喵喵喵")
        else:
            replaced_result = result
        this_time_vars = {'result_flag': result_flag,
                          'step_1_output': step_1_output,
                          'step_1_calc': step_1_calc,
                          'step_1_state': step_1_state,
                          'step_2_output': step_2_output,
                          'step_2_calc': step_2_calc,
                          'step_2_state': step_2_state,
                          'step_3_calc': step_3_calc,
                          'step_3_state': step_3_state,
                          'step_1_post_data': post_data,
                          'result': replaced_result
                          }
    with open("mail_public_config.json", 'rb') as file_obj_inner:
        public_mail_config = json.load(file_obj_inner)
        file_obj_inner.close()
    # 配置邮件内容
    mail_message = MIMEText(str(this_time_vars), 'plain', 'utf-8')
    mail_message['Subject'] = public_mail_config['title']
    mail_message['From'] = mail_id
    mail_message['To'] = mail_target
    # 尝试发送邮件
    try:
        smtp_obj = smtplib.SMTP_SSL(public_mail_config['host'], public_mail_config['port'])
        smtp_obj.login(mail_id, mail_pd)
        smtp_obj.sendmail(mail_id, mail_target, mail_message.as_string())
        smtp_obj.quit()
        print('具体提示信息已发送到邮箱，内容包含个人敏感信息，请勿泄露邮件内容.')
        exit(0)
    except smtplib.SMTPException:
        print('发送结果的邮箱设置可能异常，请检查邮箱和密码配置，以及发信SMTP服务器配置.')
        raise smtplib.SMTPException


# 准备请求数据
session = requests.session()
info = {}
header = {"Origin": "https://jksb.v.zzu.edu.cn",
          "Referer": "https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/first0",
          "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.56",
          "Host": "jksb.v.zzu.edu.cn"
          }
post_data = {"uid": user_id,
             "upw": user_pd,
             "smbtn": "进入健康状况上报平台",
             "hh28": "722",
             }
step_2_data = {'day6': 'b',
               'did': '1',
               'men6': 'a'
               }

# 第一步 获取 token
while step_1_calc < 4:
    try:
        # 接收回应数据
        response = session.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login", data=post_data, headers=header,
                                verify=False)
        if type(response) == requests.models.Response:
            response.encoding = "utf-8"
            step_1_output = response.text
            if "验证码" in step_1_output:
                print("运行时返回需要验证码，将终止本次打卡，您需要在 Action 中合理配置运行时间.")
                report_mail(debug_switch)
            mixed_token = response.text[response.text.rfind('ptopid'):response.text.rfind('"}}\r''\n</script>')]
            if "hidden" in mixed_token:
                step_1_calc += 1
                continue
            elif not mixed_token:
                step_1_calc += 1
                continue
            else:
                token_ptopid = mixed_token[7:mixed_token.rfind('&sid=')]
                token_sid = mixed_token[mixed_token.rfind('&sid=') + 5:]
                step_1_state = True
                public_data['ptopid'] = token_ptopid
                step_2_data['ptopid'] = token_ptopid
                public_data['sid'] = token_sid
                step_2_data['sid'] = token_sid
                break
        else:
            if step_1_calc < 3:
                step_1_calc += 1
                print("获取 token 中" + str(step_1_calc)
                      + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                continue
            else:
                print("获取 token 中" + str(step_1_calc)
                      + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，次数达到预期，终止本次打卡，报告失败情况.")
                report_mail(debug_switch)
    except requests.exceptions.SSLError:
        if step_1_calc < 3:
            step_1_calc += 1
            print("获取 token 中" + str(step_1_calc)
                  + "次失败，服务器提示SSLError，可能与连接问题有关.")
            continue
        else:
            print("获取 token 中" + str(step_1_calc)
                  + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
            report_mail(debug_switch)

# 第二步 提交填报人
header["Referer"] = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'
# response = False
while step_2_calc < 4:
    try:
        response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header, data=step_2_data,
                                verify=False)
        if type(response) == requests.models.Response:
            response.encoding = "utf-8"
            step_2_output = response.text
            if "发热" in step_2_output:
                break
            elif "无权" in step_2_output:
                print("提交填报人" + str(step_2_calc)
                      + "次失败，可能是学号或密码有误，终止本次打卡，报告失败情况.")
                report_mail(debug_switch)
        else:
            if step_2_calc < 3:
                step_2_calc += 1
                print("提交填报人" + str(step_2_calc)
                      + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                continue
            else:
                print("提交填报人" + str(step_2_calc)
                      + "次失败，没有response，可能学校服务器故障，次数达到预期，终止本次打卡，报告失败情况.")
                report_mail(debug_switch)
    except requests.exceptions.SSLError:
        if step_2_calc < 3:
            step_2_calc += 1
            print("提交填报人" + str(step_2_calc)
                  + "次失败，服务器提示SSLError，可能与连接问题有关.")
            continue
        else:
            print("提交填报人" + str(step_2_calc)
                  + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
            report_mail(debug_switch)


# 第三步 提交表格
# response = False
while step_3_calc < 4:
    try:
        response = session.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header, data=public_data,
                                verify=False)
        if type(response) == requests.models.Response:
            response.encoding = "utf-8"
            step_3_output = response.text
            if "感谢你今日上报" in step_3_output:
                break
            elif "无权" in step_3_output:
                print("填报表格中" + str(step_3_calc)
                      + "次失败，次数达到预期，终止本次打卡，报告失败情况.")
                report_mail(debug_switch)
        else:
            if step_3_calc < 3:
                step_3_calc += 1
                print("填报表格中" + str(step_3_calc)
                      + "次失败，没有response，可能学校服务器故障，或者学号或密码有误，请检查返回邮件信息.")
                continue
            else:
                print("填报表格中" + str(step_3_calc)
                      + "次失败，没有response，可能学校服务器故障，次数达到预期，终止本次打卡，报告失败情况.")
                report_mail(debug_switch)
    except requests.exceptions.SSLError:
        if step_3_calc < 3:
            step_3_calc += 1
            print("填报表格中" + str(step_3_calc)
                  + "次失败，服务器提示SSLError，可能与连接问题有关.")
            continue
        else:
            print("填报表格中" + str(step_3_calc)
                  + "次失败，服务器提示SSLError，次数达到预期，终止本次打卡，报告失败情况.")
            report_mail(debug_switch)

# 分析上报结果
result = step_3_output
if "感谢你今日上报" in result:
    result_flag = True
    print("上报成功")
elif "由于如下原因" in result:
    result_flag = False
    print("注意：上报失败！！代码需要更新，返回提示有新增或不匹配项目，或是今日已被审核，而不能再上报.")
    report_mail(debug_switch)
elif "重新登录" in result:
    result_flag = False
    print("注意：上报失败！！可能是用户名或密码错误，或服务器响应超时.")
    report_mail(debug_switch)
else:
    result_flag = False
    print("注意：上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")
    report_mail(debug_switch)

# 总是发送邮件设定为 True 时，发送邮件
if always_fail:
    report_mail(debug_switch)
