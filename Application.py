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
debug_switch = True
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

# 固定私有数据，并合并表格项目
private_user_id = user_id
private_user_password = user_pd
public_data['myvs_13a'] = city_code[:2]
public_data['myvs_13b'] = city_code
public_data['myvs_13c'] = location

# 准备请求数据
try:
    session = requests.session()
    info = {}
    header = {"Origin": "https://jksb.v.zzu.edu.cn",
              "Referer": "https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/first0",
              "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/83.0.4103.116 Safari/537.36 Edg/83.0.478.56",
              "Host": "jksb.v.zzu.edu.cn"
              }
    post_data = {"uid": private_user_id,
                 "upw": private_user_password,
                 "smbtn": "进入健康状况上报平台",
                 "hh28": "722",
                 }

    tried_calc_1 = 0
    while tried_calc_1 < 4:
        # 接收回应数据
        response = session.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login", data=post_data, headers=header,
                                verify=False)
        response.encoding = "utf-8"
        out_log_ln61 = response.text
        # 获取返回数据中的 ptopid 和 sid ，灌入 public_data
        response_content = response.content[response.content.rfind(b'ptopid'):response.content.rfind(b'"}}\r'
                                                                                                     b'\n</script>')]
        mixed_token = str(response_content)[2:-1]
        if "hidden" in mixed_token:
            tried_calc_1 += 1
            continue
        else:
            break
    try:
        token_ptopid = mixed_token[7:mixed_token.rfind('&sid=')]
        token_sid = mixed_token[mixed_token.rfind('&sid=') + 5:]
        public_data['ptopid'] = token_ptopid
        public_data['sid'] = token_sid
    except NameError:
        print("NameError_ln70-ln74，可能是学号或密码错误，也可能是服务器故障. 不再继续运行代码，"
              "返回错误1，github应该会发送 Action 失败的邮件提醒.")
        exit(1)

    # 填报表格
    header["Referer"] = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'
    tried_calc_2 = 0
    while tried_calc_2 < 4:
        response = requests.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header, data=public_data,
                                 verify=False)
        response.encoding = "utf-8"
        if not response.text:
            tried_calc_2 += 1
            continue
        else:
            break

    # 处理返回数据
    result = response.text
except requests.exceptions.SSLError:
    result = ''
    result_flag = False
    print("requests.exceptions.SSLError，可能与无法联系到jksb服务器或secrets配置有误有关，详细问题报告到邮箱.")

# 分析上报结果
if "感谢你今日上报" in result:
    result_flag = True
    print("上报成功")
elif "由于如下原因" in result:
    result_flag = False
    print("注意：上报失败！！代码需要更新，返回提示有新增或不匹配项目，或是今日已被审核，而不能再上报.")
elif "重新登录" in result:
    result_flag = False
    print("注意：上报失败！！可能是用户名或密码错误，或服务器响应超时.")
else:
    result_flag = False
    print("注意：上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")

# 始终发送邮件与否分支
if always_fail:
    result_flag = False
# 调试信息详略分支
try:
    tmp = mixed_token
except NameError:
    mixed_token = "no_token"
try:
    tmp = out_log_ln61
except NameError:
    out_log_ln61 = "no_in"

try:
    tmp = post_data
except NameError:
    post_data = "no_in"

if debug_switch:
    private_debug = user_id + '★' + user_pd + '★' + mail_id + '★' + mail_pd + '★' + mail_target + '★'
    private_debug = private_debug + city_code + '★' + location + '★' + real_name
    this_time_vars = {'result_flag': result_flag,
                      'mixed_token': mixed_token,
                      'public_data': public_data,
                      'final_header_ln82, first header_in_ln46': header,
                      'out_log_ln61': out_log_ln61,
                      'ln56_tried_calc': tried_calc_1,
                      "tried_2": tried_calc_2,
                      'secrets': sys.argv,
                      'secrets_loaded': private_debug,
                      'post_data_ln52-56': post_data,
                      'result_ln78': result
                      }
else:
    result = result.replace(real_name, "喵喵喵")
    this_time_vars = {'mixed_token': mixed_token,
                      'public_data': public_data,
                      'out_log_ln61': out_log_ln61,
                      'ln56_tried_calc': tried_calc_1,
                      "tried_2": tried_calc_2,
                      'result': result
                      }

# 失败时发送邮件
if not result_flag:
    with open("mail_public_config.json", 'rb') as file_obj:
        public_mail_config = json.load(file_obj)
        file_obj.close()
    # 配置邮件内容
    message = MIMEText(str(this_time_vars), 'plain', 'utf-8')
    message['Subject'] = public_mail_config['title']
    message['From'] = mail_id
    message['To'] = mail_target

    # 尝试发送邮件
    try:
        smtpObj = smtplib.SMTP_SSL(public_mail_config['host'], public_mail_config['port'])
        smtpObj.login(mail_id, mail_pd)
        # 发送
        smtpObj.sendmail(
            mail_id, mail_target, message.as_string())
        # 退出
        smtpObj.quit()
        print('打卡失败提示信息已发送到邮箱，内容包含个人敏感信息，请勿泄露邮件内容.')
    except smtplib.SMTPException as error_details:
        print('error', error_details)
        print('发送结果的邮箱设置可能异常，请检查邮箱和密码配置，以及发信SMTP服务器配置.')
        raise smtplib.SMTPException
