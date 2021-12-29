#!/usr/bin/env python3

import pandas as pd
import pandas_ta as ta
import hashlib
import hmac
import json
import requests
import datetime
import os
import sys
import cowsay
from termcolor import colored

import firebase_admin
from firebase_admin import credentials
from firebase_admin import db

# set plotting with plotly
pd.options.plotting.backend = "plotly"


class Bitkub:
    def __init__(self):
        cowsay.cow("""Bitkub Lib v.1\n\nCreate By: F San\nE-Mail: krumii.it@gmail.com\nGitHub: https://github.com/abe27""")
        # Fetch the service account key JSON file contents
        cred = credentials.Certificate('keys.json')
        # Initialize the app with a service account, granting admin privileges
        firebase_admin.initialize_app(cred, {
            'databaseURL': os.getenv('API_FIREBASE_URL')
        })

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
        
    @property
    def api_key(self):
        return self.API_KEY

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
            'available': obj['result'][self.API_CURRENCY]['available'],
            'reserved': obj['result'][self.API_CURRENCY]['reserved'],
            'symbol': self.API_CURRENCY
        }]
        if obj['error'] == 0:
            currency = obj['result']
            for i in currency:
                if currency[i]['reserved'] > 0:
                    currency[i]['symbol'] = i
                    data.append(currency[i])

        return data

    def get_symbols(self):
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
            print(f"Error: {e}")

        return False
