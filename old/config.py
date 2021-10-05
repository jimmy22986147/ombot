# -*- coding: utf-8 -*-
'''
data = {'prod': {'survey_url':'https://docs.google.com/spreadsheets/d/1jZ7XEhS0IYUI6mkf_YOQefgUiYTVZYRU-93my3cZJgs/edit#gid=0',
                 'table':'cs_detection.tasks',
                 'token':'1918831254:AAExIEvOAeEUzb6Xmx2GrTb6HfwwkBJD7p4'},
        'test': {'survey_url':'https://docs.google.com/spreadsheets/d/10dvYLkKzAW_6mJFGR2LB7Mx0WY_c_8GLtqhqen0q3hY/edit#gid=1481259803',
                 'table':'cs_detection.tasks_test',
                 'token':'1877618805:AAE_M1K6GVgCyiNnm0GEgWoZ3NFVRsaza6g'},
        'allow_list_dict':{'CS_Millie': '233459297',
                           'CS_Carol':'1461296420',
                           'CS_Edgar':'1076025437',
                           'CS_Sally':'1139058216',
                           'CS_Doris':'1853406042',
                           'RD':'1465290152',
                           'OM':'1798791836'},
        'googlesheetAPIJson':'C://Users//user//Desktop//project//OMBOT//aicool-csbot-0539c368976e.json'}
with open('config.json', 'w') as fp:
    json.dump(data, fp)
''' 
import json
import pygsheets
import os
import time
import pandas as pd
from urllib.request import ssl, socket
import mysql.connector
from telnetlib import Telnet
import datetime
pd.set_option('max_columns', None)
pd.set_option('max_rows', 100)
def variable_zone(env='test'):
    with open('config.json') as json_file: 
        config = json.load(json_file) 
    gc = pygsheets.authorize(service_account_file=config['googlesheetAPIJson'])
    survey_url = config[env]['survey_url']
    table = config[env]['table']
    token = config[env]['token']
        
    #allow list
    allow_list_dict = config['allow_list_dict']
    allow_list = list(allow_list_dict.values()) 
    sh = gc.open_by_url(survey_url)
    ws = sh.worksheet_by_title('CS維護表')
    
    return ws, table, token, allow_list

def ws_to_df(ws):
    df = ws.get_as_df(start='A1', 
                      index_colum=0, 
                      empty_value='',
                      include_tailing_empty=False) # index 從 1 開始算   
    df['商戶'] = df['商戶'].apply(lambda x: str(x).upper())
    df['type'] = df['type'].apply(lambda x: str(x).upper())
    df.columns = ['商戶', 'ip', 'domain', 'MYSQL', 'TOMCAT', 'SOCKET', 'type']
    return df

def om_bot(text, df):
    # execute command, and return the output
    def execCmd(cmd):
        r = os.popen(cmd)
        result = r.read()
        r.close()
        return result
    
    def get_request(req, cmd_first):#req = [IP, DOMAIN]
        s = time.time()
        if cmd_first == 'ping ':
            cmd_request = [cmd_first+ str(i)+ ' -w 1000' for i in req]
            result = [execCmd(i) for i in cmd_request]
        else:
            cmd_request = [cmd_first+ str(i) for i in req]
            result = [execCmd(i) for i in cmd_request]    
        print(time.time()-s)
        return result
    
    def get_telnet(req, port):
        try:
            with Telnet(req, port, timeout=0.5) as tn:
                tn.interact()
                result = '成功'
        except Exception as e:
            result = str(e)        
        return result  
    
    def get_ta_telnet(ta):
        result = []
        for i in range(len(ta)):
            req_split = ta.type[i].split(',')
            req = ta['ip'][i]
            for j in req_split:
                if j == '':
                    result_temp = "▶️Telnet {j} port结果: {result_temp}".format(j=j, result_temp='空白❌')
                else:
                    port = ta[j][i]
                    result_temp = get_telnet(req, port)
                    result_temp = '▶️Telnet {j} port结果: {result_temp}✅'.format(j=j, result_temp=result_temp)
                result.append(result_temp)
        return_text = '\n'.join(result)
        return return_text
    def get_check(tar, remove_list=['最短=', '最长=', '平均=', 'ms'], spli='，',threshold=200): 
        try:
            rs = tar
            for i in remove_list:
                rs = rs.replace(i, '')
            rs = [float(i) for i in rs.split(spli) ]
            if max(rs) >=200:
                icon = '❌'
            else:
                icon = '✅'
        except:
            icon = '❌'
        return icon
        
    def get_ping(IP, Domain, Domain_raw, cmd_first): 

        #IP
        return_text_IP =  get_request(IP, cmd_first=cmd_first) 
        return_text_IP =  [i.split('\n')[-2].replace(' ', '') for i in return_text_IP]
        get_ip_icon = [get_check(i) for i in return_text_IP]
        return_text_IP = '\n'.join([str(IP[i])+ ':{}\n'.format(get_ip_icon[i]) +return_text_IP[i] for i in range(len(return_text_IP))])
        #Domain
        return_text_Domain =  get_request(Domain, cmd_first=cmd_first)  
        return_text_Domain =  [i.split('\n')[-2].replace(' ', '') for i in return_text_Domain]
        get_domain_icon = [get_check(i) for i in return_text_Domain]
        return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i])+return_text_Domain[i] for i in range(len(return_text_Domain))])


        return_text = '▶️Ping IP的結果：\n{return_text_IP}\n▶️Ping Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                            return_text_Domain=return_text_Domain)                
        return return_text
    
    def get_tcping(IP, Domain, Domain_raw, cmd_first):
        return_text_IP =  get_request(IP, cmd_first=cmd_first) 
        return_text_IP =  [i.split('\n')[-2].replace(' ', '') for i in return_text_IP]
        get_ip_icon = [get_check(i, remove_list=['Minimum=', 'Maximum=', 'Average=', 'ms'], spli=',',threshold=200) for i in return_text_IP]
        return_text_IP = '\n'.join([str(IP[i])+ ':{}\n'.format(get_ip_icon[i]) +return_text_IP[i] for i in range(len(return_text_IP))])
        #Domain
        return_text_Domain =  get_request(Domain, cmd_first=cmd_first)  
        return_text_Domain =  [i.split('\n')[-2].replace(' ', '') for i in return_text_Domain]
        get_domain_icon = [get_check(i, remove_list=['Minimum=', 'Maximum=', 'Average=', 'ms'], spli=',',threshold=200) for i in return_text_Domain]
        return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i]) +return_text_Domain[i] for i in range(len(return_text_Domain))])

        return_text = '▶️TCPing IP的結果：\n{return_text_IP}\n▶️TCPing Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                                 return_text_Domain=return_text_Domain)   

        return return_text
    
    def get_route(IP, Domain, Domain_raw, cmd_first):
        return_text_IP =  get_request(IP, cmd_first=cmd_first) 
        return_text_IP =  ['Route成功' if 'Connection established' else 'Route失敗' in i for i in return_text_IP]
        get_ip_icon =  ['✅' if 'Connection established' else '❌' in i for i in return_text_IP]        
        return_text_IP = '\n'.join([str(IP[i])+ ':{}\n'.format(get_ip_icon[i])+return_text_IP[i] for i in range(len(return_text_IP))])
        #Domain
        return_text_Domain =  get_request(Domain, cmd_first=cmd_first)  
        return_text_Domain =  ['Route成功' if 'Connection established' else 'Route失敗' in i for i in return_text_Domain]
        get_domain_icon =  ['✅' if 'Connection established' else '❌' in i for i in return_text_Domain]        
        return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i])+return_text_Domain[i] for i in range(len(return_text_Domain))])


        return_text = '▶️ROUTE IP的結果：\n{return_text_IP}\n▶️ROUTE Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                                return_text_Domain=return_text_Domain)     

        return return_text        
    def get_ip(customer, IP):
        
        return_text =  '{chat}'.format(chat='{customer} {IP}'.format(customer=customer,
                                                                                IP=IP))
        return return_text
    
    def get_ssl(Domain, req='expire'):
        
        context = ssl.create_default_context()
        try:
            with socket.create_connection((Domain, '443')) as sock:
                with context.wrap_socket(sock, server_hostname=Domain) as ssock:
                    data = ssock.getpeercert()

            if req == 'expire':
                return_text =  'SSL到期日：\n'+ data['notAfter']
            elif req == 'DNS':
                return_text =  'DNS：\n'+ str(data['subjectAltName'])
                
        except:
            return_text =  '網頁無法瀏覽'
        return return_text
    
    def get_ta_ssl(IP, Domain, Domain_raw, req='expire'):
        return_text_IP =  [get_ssl(i, req='expire')  for i in IP]
        get_ip_icon =  ['❌' if '網頁無法瀏覽'  in i  else '✅'  for i in return_text_IP] 
        return_text_IP = '\n'.join([str(IP[i])+ ':{}\n'.format(get_ip_icon[i])+return_text_IP[i] for i in range(len(return_text_IP))])
        
        return_text_Domain =  [get_ssl(i, req='expire')  for i in Domain]
        get_domain_icon =  ['❌' if '網頁無法瀏覽' in i  else '✅'  for i in return_text_Domain] 
        return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i])+return_text_Domain[i] for i in range(len(return_text_Domain))])
        
        return_text = '▶️SSL到期日 IP的結果：\n{return_text_IP}\n▶️SSL到期日 Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                                    return_text_Domain=return_text_Domain)    
        return return_text
    
    def get_sqltable(IP):
        try:
            db = mysql.connector.connect(
                host=IP,
                user="root",
                password='GV88tuc2!',
                database="im"
            )          
            cursor = db.cursor()          
            cursor.execute("Show tables;")       
            table_list = cursor.fetchall()
            table_list = [i[0] for i in table_list]
            str_list = ["select count(1) from im.{t}".format(t=j) for j in table_list]
            table_df = pd.DataFrame({'table_name': table_list, 'str':str_list})
            
            nrow = []
            for i in table_df.str:
                cursor.execute(i)
                rs = cursor.fetchall()
                nrow.append(rs[0][0])
                
            table_df.loc[:, 'nrow'] = nrow
            table_df = table_df.sort_values(by='nrow', ascending=False).reset_index(drop=True)
            table_df = table_df[['table_name', 'nrow']]
            
            return_text =  'IM_DataBase table個數：{n}\n{table_df}'.format(n=str(table_df.shape[0]), table_df=table_df)
        except:
            return_text = '未設置IP'
        return return_text
          
    BadRequest_ans = 'request不在查詢範圍中 / 格式不對' 
    
    try:
        text = text.upper()
        customer, request = text.split(' ')
        ta = df[df['商戶'] == customer].reset_index(drop=True)
        if (ta.empty) & (request != 'LIST'):
            return_text =  BadRequest_ans
        else:
            IP = [i for i in ta[ta.ip != '']['ip']]
            Domain = [i.replace('(socket)', '') for i in ta[ta.domain != '']['domain']]
            Domain_raw = [i for i in ta[ta.domain != '']['domain']]
            #ping
            if request in ['PING']:   
                cmd_first = 'ping '
                return_text = get_ping(IP, Domain, Domain_raw, cmd_first)
            elif request in ['LIST']:
                df2 = df.copy()
                df2 = df2[df['商戶'] != ''].reset_index(drop=True)
                if customer != 'ALL':
                    condition = [True if customer in i else False for i in df2['商戶']]
                else:
                    condition = [True for i in df2['商戶']]                    
                    
                show = df2[condition]['商戶'].unique()    
                return_text = '######List結果######\n{show}'.format(show = str(list(show)))
                
            #tcping    
            elif request in ['CHECK']:               
                return_Ping = get_ping(IP, Domain, Domain_raw, 'ping ')  
                return_TCPing = get_tcping(IP, Domain, Domain_raw, 'tcping ')
                return_SSL = get_ta_ssl(IP, Domain, Domain_raw, req='expire')
                return_telnet = get_ta_telnet(ta)
                return_text = '######Ping######\n{return_Ping}\n######TCPing#####\n{return_TCPing}\n######SSL 到期日######\n{return_SSL}\n########Telnet#######\n{return_telnet}'.format(return_Ping=return_Ping, 
                                                                                                                                        return_TCPing=return_TCPing,
                                                                                                                                        return_SSL=return_SSL, return_telnet=return_telnet)
            #tcping    
            elif request in ['TCPING']:
                cmd_first = 'tcping '
                return_text = get_tcping(IP, Domain, Domain_raw, cmd_first)
                
            #tracetcp(TCP Traceroute)
            elif request in ['ROUTE']:            
                cmd_first = 'C://Windows//System32//tracetcp_v1.0.3//tracetcp.exe '
                return_text = get_route(IP, Domain, Domain_raw, cmd_first)  
                
            elif request == 'IP':             
                return_text =  '\n'.join(IP)             
            #ssl expire date
            elif request == 'SSL':              
                return_text_IP =  [get_ssl(i, req='expire')  for i in IP]
                get_ip_icon =  ['❌' if '網頁無法瀏覽' in i  else '✅'  for i in return_text_IP] 
                return_text_IP = '\n'.join([str(IP[i])+  ':{}\n'.format(get_ip_icon[i])+return_text_IP[i] for i in range(len(return_text_IP))])
                
                return_text_Domain =  [get_ssl(i, req='expire')  for i in Domain]
                get_domain_icon =  ['❌' if '網頁無法瀏覽' in i  else '✅'  for i in return_text_Domain] 
                return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i])+return_text_Domain[i] for i in range(len(return_text_Domain))])
                return_text = '#SSL到期日 IP的結果：\n{return_text_IP}\n#SSL到期日 Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                                            return_text_Domain=return_text_Domain)                 
                
            #ssl DNS
            elif request == 'DNS':              
                return_text_IP =  [get_ssl(i, req='DNS')  for i in IP]
                get_ip_icon =  ['❌' if '網頁無法瀏覽' in i else '✅' in i for i in return_text_IP]                 
                return_text_IP = '\n'.join([str(IP[i])+ ':\n'+return_text_IP[i] for i in range(len(return_text_IP))])
                
                return_text_Domain =  [get_ssl(i, req='DNS')  for i in Domain]
                get_domain_icon =  ['❌' if '網頁無法瀏覽' in i  else '✅' in i for i in return_text_Domain]                 
                return_text_Domain = '\n'.join([str(Domain_raw[i])+ ':{}\n'.format(get_domain_icon[i])+return_text_Domain[i] for i in range(len(return_text_Domain))])
                return_text = '#DNS IP的結果：\n{return_text_IP}\n#DNS Domain的結果：\n{return_text_Domain}'.format(return_text_IP=return_text_IP, 
                                                                                                                  return_text_Domain=return_text_Domain)                 
            #IM TABLE N
            elif request == 'NTABLE':              
                return_text = get_sqltable(IP)    
            #DBIM Database im 一致性
            elif request == 'DBIM':     
                port = ta.MYSQL.iloc[0]
                return_text_IP =  [get_telnet(i, port)  for i in IP]
                return_text_IP = '\n'.join([str(IP[i])+ ':\n'+return_text_IP[i] for i in range(len(return_text_IP))])
                
                return_text = '#Database im service IP的結果：\n{return_text_IP}'.format(return_text_IP=return_text_IP)                    
            #TOMCAT SERVICE    
            elif request == 'TOMCATSERVICE':     
                port = int(ta[ta.TOMCAT != ''].port_tomcat.iloc[0])
                return_text_IP =  [get_telnet(i, port)  for i in IP]
                return_text_IP = '\n'.join([str(IP[i])+ ':\n'+return_text_IP[i] for i in range(len(return_text_IP))])
                
                return_text = '#Tomcat service IP的結果：\n{return_text_IP}'.format(return_text_IP=return_text_IP)
            #TOMCAT SOCKET    
            elif request == 'TOMCATSOCKET':     
                port = int(ta[ta.SOCKET != ''].port_socket.iloc[0])
                return_text_IP =  [get_telnet(i, port)  for i in IP]
                return_text_IP = '\n'.join([str(IP[i])+ ':\n'+return_text_IP[i] for i in range(len(return_text_IP))])

                return_text = '#Tomcat SOCKET IP的結果：\n{return_text_IP}'.format(return_text_IP=return_text_IP)
            else:
                return_text = BadRequest_ans
    except:
        return_text =  BadRequest_ans        
    return return_text


def trans_text(raw):
    text = raw.upper()
    if text == 'LIST':
        text = 'ALL LIST'
    else:
        text = text    
    c, r = text.split(' ')
    return text, c, r


def InsertLog(table, user, c, r, return_text):
    mydb = mysql.connector.connect(host="172.16.150.100",
                                   user="csbotmgr",
                                   password="1q2w3e4r5t",
                                   database="cs_detection",charset='utf8')
    mycursor = mydb.cursor()
    now_time = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S.000')
    sql = "INSERT INTO {table} (USER, createtime, cust, request, response) VALUES (%s, %s, %s, %s, %s)".format(table=table)
    val = (user, now_time, c, r, return_text)
    mycursor.execute(sql, val)
    mydb.commit()
    mydb.close()
    mycursor.close()


