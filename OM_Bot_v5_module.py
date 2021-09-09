# -*- coding: utf-8 -*-
import os
os.chdir('C:/Users/user/Desktop/project/OMBOT/')
import time
import telepot
from telepot.loop import MessageLoop
from pprint import pprint
import config
env = 'test'
ws, table, token, allow_list = config.variable_zone(env)
bot = telepot.Bot(token)

def handle(msg):
    pprint(msg)
    chat_id = msg['chat']['id']
    user = msg['from']['first_name']
    raw = msg['text']
    
    if str(chat_id) in allow_list:
        try:
            text, c, r = config.trans_text(raw)
            bot.sendMessage(chat_id, '執行中，請稍等1-2分鐘')
            df = config.ws_to_df(ws)
            return_text = config.om_bot(text, df)
            
            config.InsertLog(table, user, c, r, return_text)     
            
            bot.sendMessage(chat_id, return_text)  
        except:
            bot.sendMessage(chat_id, '格式不對')
    else:
        bot.sendMessage(chat_id, '需求不为您开放')
MessageLoop(bot, handle).run_as_thread()
print("I'm listening...")

while True:
    time.sleep(0.01)