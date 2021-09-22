# jksbDirect
#
# By Clok Much

import sys
import json
import smtplib
from email.mime.text import MIMEText
import ssl

import requests

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
tried_calc = 0
while tried_calc < 4:
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

    # 接收回应数据
    response = session.post("https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/login", data=post_data, headers=header, verify=False)
    response.encoding = "utf-8"
    out_log_ln56 = response.text
    # 获取返回数据中的 ptopid 和 sid ，灌入 public_data
    response_content = response.content[response.content.rfind(b'ptopid'):response.content.rfind(b'"}}\r\n</script>')]
    mixed_token = str(response_content)[2:-1]
    if "hidden" in mixed_token:
        tried_calc += 1
        continue
    else:
        break

token_ptopid = mixed_token[7:mixed_token.rfind('&sid=')]
token_sid = mixed_token[mixed_token.rfind('&sid=')+5:]

public_data['ptopid'] = token_ptopid
public_data['sid'] = token_sid

# 填报表格
header["Referer"] = 'https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb'
response = requests.post('https://jksb.v.zzu.edu.cn/vls6sss/zzujksb.dll/jksb', headers=header, data=public_data, verify=False)

# 处理返回数据
response.encoding = "utf-8"
result = response.text

# 分析上报结果
if "感谢你今日上报" in result:
    result_flag = True
    print("上报成功")
elif "由于如下原因" in result:
    result_flag = False
    print("注意：上报失败！！代码需要更新，返回提示有新增或不匹配项目.")
elif "重新登录" in result:
    result_flag = False
    print("注意：上报失败！！可能是用户名或密码错误，或服务器响应超时.")
else:
    result_flag = False
    print("注意：上报失败！！原因未知，请自行检查返回结果和邮件中的变量输出.")

# 调试区域，首次修改始终认为打卡失败，当确认运行有效后，删除对 result_flag 的重新赋值即可.
result_flag = False

# 失败时发送邮件
if not result_flag:
    with open("mail_public_config.json", 'rb') as file_obj:
        public_mail_config = json.load(file_obj)
        file_obj.close()
    # 整理局部变量，结果如果包含真实姓名，将之替换为 喵喵喵
    this_time_vars = {'result_flag': result_flag,
                      'mixed_token': mixed_token,
                      'public_data': public_data,
                      'final_header': header,
                      'out_log_ln56': out_log_ln56,
                      'real_name': real_name
                      }
    # result = result.replace(real_name, "喵喵喵")
    # 配置邮件内容
    message = MIMEText(str(this_time_vars) + result, 'plain', 'utf-8')
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
