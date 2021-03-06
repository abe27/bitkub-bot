from dotenv import load_dotenv
import pandas as pd
import pandas_ta as ta
import hashlib
import hmac
import json
import requests
import datetime
import os
import sys

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# Initialize Environment
load_dotenv()

# Fetch the service account key JSON file contents
cred = credentials.Certificate('keys.json')

# Initialize the app with a service account, granting admin privileges
firebase_admin.initialize_app(cred, {
    'databaseURL': os.getenv('API_FIREBASE_URL')
})

# set plotting with plotly
pd.options.plotting.backend = "plotly"

# API info
API_HOST = os.getenv('API_BITKUB_HOST')
API_KEY = os.getenv('API_BITKUB_KEY')
API_SECRET = (os.getenv('API_BITKUB_SECRET')).encode('utf8')
API_CURRENCY = os.getenv('API_BITKUB_CURRENCY')
API_TIMEFRAME = (os.getenv('API_BITKUB_TIMEFRAME')).split(
    ',')
API_LIMIT = int(os.getenv('API_LIMIT'))
API_EMA_FAST = int(os.getenv('API_EMA_FAST'))
API_EMA_SLOW = int(os.getenv('API_EMA_SLOW'))

headers = {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    'X-BTK-APIKEY': API_KEY,
}


def json_encode(data):
    return json.dumps(data, separators=(',', ':'), sort_keys=True)


def sign(data):
    j = json_encode(data)
    # print('Signing payload: ' + j)
    h = hmac.new(API_SECRET, msg=j.encode(), digestmod=hashlib.sha256)
    return h.hexdigest()

# check server time


def timeserver():
    response = requests.get(API_HOST + '/api/servertime')
    ts = int(response.text)
    # print('Server time: ' + response.text)
    return ts


def get_assets():
    # ตรวจสอบ server time
    data = {
        'ts': timeserver(),
    }
    signature = sign(data)
    data['sig'] = signature

    # print('Payload with signature: ' + json_encode(data))
    response = requests.post(API_HOST + '/api/market/balances',
                             headers=headers, data=json_encode(data))
    obj = json.loads(response.text)

    data = [{
        'available': obj['result'][API_CURRENCY]['available'],
        'reserved': obj['result'][API_CURRENCY]['reserved'],
        'symbol': API_CURRENCY
    }]
    if obj['error'] == 0:
        currency = obj['result']
        for i in currency:
            if currency[i]['reserved'] > 0:
                currency[i]['symbol'] = i
                data.append(currency[i])

    return data


def get_symbols():
    response = requests.get(
        API_HOST + "/api/market/symbols", headers={}, data={})
    obj = json.loads(response.text)
    if obj['error'] == 0:
        i = 0
        while i < len(obj['result']):
            symbol = str(obj['result'][i]['symbol'])
            obj['result'][i]["global"] = symbol
            obj['result'][i]['symbol'] = symbol[4:]
            obj['result'][i]["currency"] = API_CURRENCY
            i += 1

        return obj['result']

    return obj['error']


# get last price


def get_last_price(symbol):
    try:
        rticker = requests.get(f'{API_HOST}/api/market/ticker?sym={symbol}')
        rticker = rticker.json()
        price = rticker[symbol]
        return price
    except Exception as e:
        print(f"Error: {e}")

    return False


def get_candle(pair, timeframe):

    # เรียก ข้อมูลราคา ของสินค้ามาไว้ในรูปแบบ ตาราง
    # กำหนดตัวแปร ที่ต้องใช้
    # timeframe = ช่วงเวลาของกราฟที่จะดึงข้อมูล 1, 5, 15, 60, 240, 1D
    timestramp = timeserver()
    form_time = datetime.datetime.fromtimestamp(
        timestramp) - datetime.timedelta(days=API_LIMIT)

    if (timeframe).find("D") < 0:
        form_time = datetime.datetime.fromtimestamp(
            timestramp) - datetime.timedelta(minutes=(int(timeframe) * API_LIMIT))

    to_date = datetime.datetime.fromtimestamp(timestramp)
    print(
        f"ดึงข้อมูลกราฟ {pair}_{API_CURRENCY} จากวันที่ {(form_time)} ถึง {to_date}")
    # # เรียก ข้อมูล จาก  exchange
    url = f"{API_HOST}/tradingview/history?symbol={pair}_{API_CURRENCY}&resolution={timeframe}&from={int((form_time).timestamp())}&to={int((to_date).timestamp())}"
    response = requests.get(url, headers={}, data={})
    candles = response.json()
    # # เรียงให้เป็น ตาราง + เอามาจัดเรียง ใส่หัวข้อ
    df = pd.DataFrame(
        candles, columns=['t', 'o', 'c', 'h', 'l', 'v'])

    # # แปลงรูปแบบ ของเวลา ด้วย Pandas
    df['t'] = pd.to_datetime(df['t'], unit='s')
    data = df.rename({'t': 'datetime', 'o': 'open',
                     'c': 'close', 'h': 'high', 'l': 'low', 'v': 'volume'}, axis=1)
    # print(f"\n{data}")
    if len(data) > 33:

        # เรียกโมดูลขึ้นมา
        EMA = data.ta.ema(API_EMA_FAST)

        # # รวมข้อมูลเก่า กับ ใหม่
        data = pd.concat([data, EMA], axis=1)

        # EMA_fast = data.ta.ema(EMA_fast_set)
        EMA_slow = data.ta.ema(API_EMA_SLOW)
        df_ohlcv = pd.concat([data, EMA_slow], axis=1)
        df_ohlcv.dropna(True)
        print(df_ohlcv.tail(6))
        
        ### export to excel
        file_excel = f"exports/excels/assets/{pair}/{datetime.datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(file_excel):
            os.makedirs(file_excel)
            
        df_ohlcv.to_excel(f"{file_excel}/{timeframe}_{datetime.datetime.now().strftime('%Y%m%d%H%M')}.xlsx")

        # EMA Cross
        count = (len(df_ohlcv) - 1)
        EMA_fast_A = df_ohlcv['EMA_' + str(API_EMA_FAST)][count]
        EMA_fast_B = df_ohlcv['EMA_' + str(API_EMA_FAST)][count-1]
        EMA_fast_C = df_ohlcv['EMA_' + str(API_EMA_FAST)][count-2]
        EMA_fast_D = df_ohlcv['EMA_' + str(API_EMA_FAST)][count-3]
        EMA_fast_E = df_ohlcv['EMA_' + str(API_EMA_FAST)][count-4]
        # print("EMA_fast_A = ", EMA_fast_A)
        # print("EMA_fast_B = ", EMA_fast_B)

        EMA_slow_A = df_ohlcv['EMA_' + str(API_EMA_SLOW)][count]
        EMA_slow_B = df_ohlcv['EMA_' + str(API_EMA_SLOW)][count-1]
        EMA_slow_C = df_ohlcv['EMA_' + str(API_EMA_SLOW)][count-2]
        EMA_slow_D = df_ohlcv['EMA_' + str(API_EMA_SLOW)][count-3]
        EMA_slow_E = df_ohlcv['EMA_' + str(API_EMA_SLOW)][count-4]
        
        # print("EMA_slow_A = ", EMA_slow_A)
        # print("EMA_slow_B = ", EMA_slow_B)
        
        print("EMA FAST :=> ", EMA_fast_A,EMA_fast_B,EMA_fast_C,EMA_fast_D,EMA_fast_E)
        print("EMA SLOW :=> ", EMA_slow_A,EMA_slow_B,EMA_slow_C,EMA_slow_D,EMA_slow_E)

        # Signal and Trend
        Signal = None
        Trend = None

        if EMA_fast_A > EMA_slow_A:
            Trend = "Up"

        elif EMA_fast_A < EMA_slow_A:
            Trend = "Down"

        if EMA_fast_A > EMA_slow_A and EMA_fast_B < EMA_slow_B:
            Signal = "Buy"

        elif EMA_fast_A < EMA_slow_A and EMA_fast_B > EMA_slow_B:
            Signal = "Sell"

        print(f"\n####### Signal and Trend {timeframe} #######")
        print(f"{pair} Trend  =  {Trend}  val: {(EMA_fast_A - EMA_slow_A)}")
        print(
            f"{pair} Signal = {Signal} val: {(EMA_fast_A - EMA_slow_A) - (EMA_fast_B - EMA_slow_B)}")

        # if Signal == "Buy":
        #     return {
        #         "currency": API_CURRENCY,
        #         "symbol": pair,
        #         "trend": Trend,
        #         "signal": Signal,
        #     }

        

        fig = df_ohlcv['close'].plot()
        # fig.show()
        img_path = f"exports/images/{pair}/{datetime.datetime.now().strftime('%Y%m%d')}"
        if not os.path.exists(img_path):
            os.makedirs(img_path)
            
        fig.write_image(f"{img_path}/{pair}_{timeframe}.png")
        
        return {
            "currency": API_CURRENCY,
            "symbol": pair,
            "trend": Trend,
            "signal": Signal,
        }


def line_notification(msg):
    url = "https://notify-api.line.me/api/notify"
    payload = f"message={msg}"
    headers = {
        'Authorization': f"Bearer {os.getenv('API_LINE_NOTIFICATION')}",
        'Content-Type': 'application/x-www-form-urlencoded'
    }

    # BugDWScwhYvjVc5EyRi5sa28LmJxE2G5NIJsrs6vEV7
    print(payload.encode('utf-8'))
    print(payload)
    response = requests.request(
        "POST", url, headers=headers, data=payload.encode('utf-8'))

    print(f"line status => {response}")
    if response.status_code == 200:
        return True

    return False


def main():
    list_symbol = []
    balance = get_assets()
    # if float(balance[0]['available']) < 50:
    #     print(f"😬 ====> จำนวนเงินในบัญชีของคุณ({balance})น้อยกว่า 50 บาท 😭")
    #     return

    print(
        f"🤗 ====> ยอดเงินในบัญชีคงเหลือ: {float(balance[0]['available'])} 💓\n")
    symbols = get_symbols()
    i = 0
    while i < len(symbols):
        symbol = symbols[i]
        print(f"----------------- {symbol['symbol']} ------------------\n")
        last_price = get_last_price(symbol['global'])

        if last_price != False:
            print(
                f"ราคา {symbol['symbol']} ล่าสุด: {last_price['last']:,} {API_CURRENCY} {last_price['percentChange']}")
            time_frame = "1D"
            s = get_candle(symbol['symbol'], time_frame)
            if s != None and s != False:
                s['percent'] = f"{last_price['percentChange']}%"
                s['lastprice'] = f"{last_price['last']:,}"
                s['lastupdate'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                list_symbol.append(s)

        print(f"----------------- end ------------------\n")
        i += 1

    # df = pd.DataFrame(list_symbol)
    # print(df)
    
    i = 0
    while i < len(list_symbol):
        x = 0
        while x < len(API_TIMEFRAME):
            timeframe = API_TIMEFRAME[x]
            
            d = get_candle(list_symbol[i]['symbol'], timeframe)

            colname = f"{timeframe}Minute"
            if (timeframe).find("D") >= 0:
                colname = f"{timeframe}ay"

            list_symbol[i][colname] = False
            if d != None:
                if d['signal'] != None:
                    list_symbol[i][colname] = True
            x += 1
        i += 1

    print(f"*************************************")
    df = pd.DataFrame(list_symbol)
    export_filename = datetime.datetime.now().strftime("%Y%m%d")
    file_path = f"exports/excels/price/{export_filename}"
    if not os.path.exists(file_path):
        os.makedirs(file_path)

    file_name = f"{file_path}/{export_filename}.xlsx"
    # if os.path.isfile(file_name):
    #     os.remove(file_name)
        
    df.to_excel(file_name)
    print(f"\n{df}\n")
    print(f"******************************************\n")
    x = 0
    while x < len(list_symbol):
        trend_list = []
        is_interesting = False
        r = list_symbol[x]
        
        # บันทึกข้อมูล lastprice ใน firebase
        fire_db_link = f"crypto/bitkub/signals/{r['symbol']}"
        ref = db.reference(fire_db_link)
        __30m = "-"
        if r['30Minute']:
            __30m = "OK"
            is_interesting = True
            trend_list.append("30Min")

        __60m = "-"
        if r['60Minute']:
            __60m = "OK"
            is_interesting = True
            trend_list.append("60Min")

        __240m = "-"
        if r['240Minute']:
            __240m = "OK"
            is_interesting = True
            trend_list.append("4H")

        __1day = "-"
        if r['1Day']:
            __1day = "OK"
            is_interesting = True
            trend_list.append("1D")
        
        r['interest'] = is_interesting
        r['trend_on'] = trend_list
        ref.set(r)
        msg = f"\nSYMBOL: {r['symbol']}\n30m:  {__30m}\n1h:  {__60m}\n4h:  {__240m}\n1Day:  {__1day}"
        # msg = f"SYMBOL: {r['symbol']}"
        print(msg)
        # line_notification(msg)
        
        #### ถ้าน่าสนใจให้ทำการบันทึกข้อมูลเพื่อทำการตรวจสอบ
        if is_interesting:
            if r['signal'] != None:
                # บันทึกข้อมูลใน firebase
                interest_db = db.reference(f"crypto/bitkub/subscribes/{r['symbol']}/{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}")
                last_price = get_last_price(f'{r["currency"]}_{r["symbol"]}')
                interest_db.set({
                    "lastprice": float(last_price['last']),
                    "lastupdate": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "percent": float(last_price['percentChange']),
                    "signal": r["signal"],
                    "symbol": r["symbol"],
                    "trend": r["trend"],
                })
                print(f"{r['symbol']}")
                # line_notification(msg)
                
        x += 1
    return


if __name__ == '__main__':
    main()
    sys.exit(0)
