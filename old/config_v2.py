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
import threading
import json
import pygsheets
import os
import time
import pandas as pd
from urllib.request import ssl, socket
import mysql.connector
from telnetlib import Telnet
import datetime
from queue import Queue

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
    '''
    # execute command, and return the output
    def execCmd(cmd, request):
        cmd_raw = cmd
        cmd_ta = cmd_raw.replace('(socket)', '')
        r = os.popen(cmd_ta)
        result = r.read()
        r.close()
        #print(result)
        if request == 'PING':
            result = result.split('\n')[-2].replace(' ', '')
            get_ip_icon = get_check(result)
            result = cmd_raw+ '結果：\n'+ result+ get_ip_icon
        elif request == 'TCPING':
            result = result.split('\n')[-2].replace(' ', '')
            get_ip_icon = get_check(result, 
                                    remove_list=['Minimum=', 'Maximum=', 'Average=', 'ms'], 
                                    spli=',',
                                    threshold=200)
            result = cmd_raw+ '結果：\n'+ result+ get_ip_icon        
        bot.sendMessage(chat_id, str(result))
        return result
'''
    def execCmd(cmd, request, q):
        def get_check(tar, remove_list=['最小值=', '最大值=', '平均=', 'ms'], spli='，',threshold=200): 
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
        cmd_raw = cmd
        cmd_ta = cmd_raw.replace('(socket)', '')
        r = os.popen(cmd_ta)
        result = r.read()
        r.close()
        #print(result)
        if request == 'PING':
            result = result.split('\n')[-2].replace(' ', '')
            get_ip_icon = get_check(result)
            result = cmd_raw+ '結果：\n'+ result+ get_ip_icon
        elif request == 'TCPING':
            result = result.split('\n')[-2].replace(' ', '')
            get_ip_icon = get_check(result, 
                                    remove_list=['Minimum=', 'Maximum=', 'Average=', 'ms'], 
                                    spli=',',
                                    threshold=200)
            result = cmd_raw+ '結果：\n'+ result+ get_ip_icon     
        #q.put(cmd_raw)        
        q.put(result)
        
    def multithread(dx):
        q = Queue()
        all_thread = []
        for i in range(len(dx)):
              thread = threading.Thread(target=execCmd, args=(dx.cmd[i], 
                                                              dx.req[i], 
                                                              q))
              thread.start()
              all_thread.append(thread)
        for t in all_thread:
              t.join()
        # 使用 q.get() 取出要傳回的值
        result = []
        for _ in range(len(all_thread)):
              result.append(q.get())
        return result  

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
                cmds = IP.copy()
                cmds.extend(Domain_raw)
                cmds = [cmd_first+ i for i in cmds]
                dx = pd.DataFrame({'req': 'PING',
                                   'cmd': cmds})
                return_text = multithread(dx)
                return_text = '\n'.join([str(return_text[i]) for i in range(len(return_text))])

            elif request in ['LIST']:
                df2 = df.copy()
                df2 = df2[df['商戶'] != ''].reset_index(drop=True)
                if customer != 'ALL':
                    condition = [True if customer in i else False for i in df2['商戶']]
                else:
                    condition = [True for i in df2['商戶']]                    
                    
                show = df2[condition]['商戶'].unique()    
                return_text = '######List結果######\n{show}'.format(show = str(list(show)))
                #bot.sendMessage(chat_id, return_text)
            #tcping    
            elif request in ['TCPING']:
                cmd_first = 'tcping '
                cmds = Domain_raw
                cmds = [cmd_first+ i+ ' 443' for i in cmds]
                cmds_final = []
                for x in cmds:
                    if '(socket)' in  x:
                        cmds_final.extend([x, x.replace('443', '80'),  x.replace('443', '9081')])
                    else:
                        cmds_final.extend([x, x.replace('443', '80')])
                dx = pd.DataFrame({'req': 'TCPING',
                                   'cmd': cmds_final})
                return_text = multithread(dx)
                return_text = '\n'.join([str(return_text[i]) for i in range(len(return_text))])
                
            elif request == 'IP':             
                return_text =  '\n'.join(IP) 
                #bot.sendMessage(chat_id, return_text)
            else:
                return_text = BadRequest_ans
                #bot.sendMessage(chat_id, return_text)
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


