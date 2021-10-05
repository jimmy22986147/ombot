# -*- coding: utf-8 -*-
"""
Created on Thu Sep 23 09:05:16 2021

@author: user
"""

import threading
from queue import Queue
import os
# 將要傳回的值存入 Queue
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
    q.put(result)


def thread_job(data, q):
    for i in range(len(data)):
          data[i] = data[i]*2
    q.put(data)
 
def multithread():
    #data = [[1, 2, 3], [4, 5, 6]]
    q = Queue()
    all_thread = []
    cmds = ['ping 8.210.97.53',
             'ping imreserveai.com',
             'ping imtryaican.com',
             'ping imsokcet.com',
             'tcping 8.210.97.53',
             'tcping imreserveai.com',
             'tcping imtryaican.com',
             'tcping imsokcet.com']
    reqs = ['PING',
             'PING',
             'PING',
             'PING',
             'TCPING',
             'TCPING',
             'TCPING',
             'TCPING']
    # 使用 multi-thread
    s = time.time()
    for i in range(len(cmds)):
          #thread = threading.Thread(target=thread_job, args=(data[i], q))
          thread = threading.Thread(target=execCmd, args=(cmds[i], reqs[i], q))
          thread.start()
          all_thread.append(thread)
 
    # 等待全部 Thread 執行完畢
    for t in all_thread:
          t.join()
    # 使用 q.get() 取出要傳回的值
    result = []
    for _ in range(len(all_thread)):
          result.append(q.get())
    print(time.time()-s)
    return result
 
x = multithread()


import pandas as pd
dx = pd.DataFrame({'req': 'PING',
                   'cmd': cmds})







