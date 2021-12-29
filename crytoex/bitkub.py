#!/usr/bin/env python3

import pandas as pd
import pandas_ta as ta
import hashlib
import hmac
import json
import requests
import datetime
import os
import cowsay
from termcolor import colored

# import firebase_admin
# from firebase_admin import credentials
# from firebase_admin import db

# set plotting with plotly
pd.options.plotting.backend = "plotly"

char_length = 60


class Bitkub:
    def __init__(self):
        """
        Library นี้สร้างขึ้นมาเพื่อความต้องการส่วนตัว
        """
        print(u"{}[2J{}[;H".format(chr(27), chr(27)))
        print(f"\n{colored(''.rjust(char_length, '*'), 'red')}")
        cowsay.cow(colored("""
                           😚 F-San Bitkub Lib v.1 🥰
                           CreateBy 👻: F San
                           E-Mail 💌: krumii.it@gmail.com
                           GitHub 🌤: https://github.com/abe27
                           License: MIT
                           """, "blue"))
        print(f"\n{colored(''.rjust(char_length, '*'), 'red')}")
        # # Fetch the service account key JSON file contents
        # cred = credentials.Certificate('keys.json')
        # # Initialize the app with a service account, granting admin privileges
        # firebase_admin.initialize_app(cred, {
        #     'databaseURL': os.getenv('API_FIREBASE_URL')
        # })

        # API info
        self.API_HOST = os.getenv('API_BITKUB_HOST')
        self.API_KEY = os.getenv('API_BITKUB_KEY')
        self.API_SECRET = (os.getenv('API_BITKUB_SECRET')).encode('utf8')
        self.API_CURRENCY = os.getenv('API_BITKUB_CURRENCY')
        self.API_TIMEFRAME = (os.getenv('API_BITKUB_TIMEFRAME')).split(',')
        self.API_LIMIT = int(os.getenv('API_LIMIT'))
        self.API_EMA_FAST = int(os.getenv('API_EMA_FAST'))
        self.API_EMA_SLOW = int(os.getenv('API_EMA_SLOW'))

        self.API_HEADER = {
            'Accept': 'application/json',
            'Content-Type': 'application/json',
            'X-BTK-APIKEY': self.API_KEY,
        }
        
    # @property
    # def api_key(self):
    #     return self.API_KEY

    @staticmethod
    def __json_encode(data):
        return json.dumps(data, separators=(',', ':'), sort_keys=True)


    def sign(self, data):
        j = self.__json_encode(data)
        # print('Signing payload: ' + j)
        h = hmac.new(self.API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
        return h.hexdigest()

    # # check server time
    def timeserver(self):
        response = requests.get(self.API_HOST + '/api/servertime')
        ts = int(response.text)
        # print('Server time: ' + response.text)
        return ts

    def get_balance_assets(self):
        # ตรวจสอบ server time
        data = {
            'ts': self.timeserver(),
        }
        signature = self.sign(data)
        data['sig'] = signature

        # print('Payload with signature: ' + json_encode(data))
        response = requests.post(self.API_HOST + '/api/market/balances',
                                 headers=self.API_HEADER, data=self.__json_encode(data))
        obj = json.loads(response.text)

        data = [{
            'available': float(obj['result'][self.API_CURRENCY]['available']),
            'reserved': obj['result'][self.API_CURRENCY]['reserved'],
            'symbol': self.API_CURRENCY
        }]
        
        if obj['error'] == 0:
            currency = obj['result']
            for i in currency:
                if currency[i]['reserved'] > 0:
                    currency[i]['symbol'] = i
                    data.append(currency[i])
                    
        msg = f"""\n
        Available: {obj['result'][self.API_CURRENCY]['available']}
        Reserved: {obj['result'][self.API_CURRENCY]['reserved']}
        Symbol: {self.API_CURRENCY}
        """
        # print(u"{}[2J{}[;H".format(chr(27), chr(27)))
        print(colored(msg, 'green'))
        print(''.rjust(char_length, '-') + "\n")

        return data

    def get_assets(self):
        response = requests.get(
            self.API_HOST + "/api/market/symbols", headers={}, data={})
        obj = json.loads(response.text)
        if obj['error'] == 0:
            i = 0
            while i < len(obj['result']):
                symbol = str(obj['result'][i]['symbol'])
                obj['result'][i]["global"] = symbol
                obj['result'][i]['symbol'] = symbol[4:]
                obj['result'][i]["currency"] = self.API_CURRENCY
                i += 1

            return obj['result']

        return obj['error']

    # get last price

    def get_last_price(self, symbol):
        try:
            rticker = requests.get(
                f'{self.API_HOST}/api/market/ticker?sym={symbol}')
            rticker = rticker.json()
            price = rticker[symbol]
            return price
        except Exception as e:
            print(colored(f"Error: {e}", 'red'))

        return False
    
    def get_candle(self, symbol, timeframe):
        # เรียก ข้อมูลราคา ของสินค้ามาไว้ในรูปแบบ ตาราง
        # กำหนดตัวแปร ที่ต้องใช้
        # timeframe = ช่วงเวลาของกราฟที่จะดึงข้อมูล 1, 5, 15, 60, 240, 1D
        timestramp = self.timeserver()
        form_time = datetime.datetime.fromtimestamp(
            timestramp) - datetime.timedelta(days=self.API_LIMIT)

        if (timeframe).find("D") < 0:
            form_time = datetime.datetime.fromtimestamp(
                timestramp) - datetime.timedelta(minutes=(int(timeframe) * self.API_LIMIT))

        to_date = datetime.datetime.fromtimestamp(timestramp)
        msg = f"ดึงข้อมูลกราฟ {colored(symbol +'-'+self.API_CURRENCY, 'blue')} จากวันที่ {(colored(form_time, 'blue'))} ถึง {colored(to_date, 'blue')}"
        print(msg)
        # # เรียก ข้อมูล จาก  exchange
        url = f"{self.API_HOST}/tradingview/history?symbol={symbol}_{self.API_CURRENCY}&resolution={timeframe}&from={int((form_time).timestamp())}&to={int((to_date).timestamp())}"
        response = requests.get(url, headers={}, data={})
        candles = response.json()
        # # เรียงให้เป็น ตาราง + เอามาจัดเรียง ใส่หัวข้อ
        df = pd.DataFrame(
            candles, columns=['t', 'o', 'c', 'h', 'l', 'v'])

        # # แปลงรูปแบบ ของเวลา ด้วย Pandas
        df['t'] = pd.to_datetime(df['t'], unit='s')
        data = df.rename({'t': 'datetime', 'o': 'open',
                        'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume'}, axis=1)
        
        ### บันทึกข้อมูลเป็น excel
        export_path = f"exports/excels/assets/{symbol}"
        if not os.path.exists(export_path):
            os.makedirs(export_path)
            
        filename = f"{export_path}/{timeframe}.{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        data.to_excel(filename)
        ##  ------>
        
        print(data.tail())
        return data
    
    def trand_ema(self, symbol, df, fast_length=9, slow_length=26, export_limit=7, export_full=False):
        print(f"trend up {fast_length} {slow_length}")
        # เรียกโมดูล EMS
        EMA_FAST = df.ta.ema(fast_length)
        EMA_SLOW = df.ta.ema(slow_length)
        
        ## เพิ่มคอลั่ม EMA
        data = pd.concat([df, EMA_FAST], axis=1)
        df_ohlcv = pd.concat([data, EMA_SLOW], axis=1)
        
        df_length = (len(df_ohlcv) - 1)
        EMS_FAST_A = df_ohlcv['EMA_' + str(fast_length)][df_length]
        EMS_FAST_B = df_ohlcv['EMA_' + str(fast_length)][df_length - 1]
        
        EMS_SLOW_A = df_ohlcv['EMA_' + str(slow_length)][df_length]
        EMS_SLOW_B = df_ohlcv['EMA_' + str(slow_length)][df_length - 1]
        
        export_path = f"exports/excels/trends"
        if not os.path.exists(export_path):
            os.makedirs(export_path)
            
        filename = f"{export_path}/EMA.{fast_length}.{slow_length}.{symbol}.{datetime.datetime.now().strftime('%Y%m%d')}.xlsx"
        if export_full:
            df_ohlcv.to_excel(filename)
            
        else:
            obj = df_ohlcv.tail(export_limit)
            obj.to_excel(filename)
