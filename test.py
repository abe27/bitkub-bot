import sys
from crytoex.bitkub import Bitkub
from termcolor import colored

from dotenv import load_dotenv
# Initialize Environment
load_dotenv()

bitkub = Bitkub()

def main():
    bal = bitkub.get_balance_assets()
    if bal[0]['available'] > 10:
        print('ok')
        
    assets = bitkub.get_assets()
    i = 0
    while i < len(assets):
        r = assets[i]
        id          = r['id']
        info        = r['info']
        asset      = r['symbol']
        gbal        = r['global']
        currency    = r['currency']
        
        # print(id,info,symbol,gbal,currency)
        get_price = bitkub.get_last_price(gbal)
        current = 0
        if get_price:
            current = float(get_price['last'])

        print(f"""Check Assets({colored(asset, 'blue')})\nValue: {colored(f'{current:,}', 'yellow')} per {colored(currency, 'blue')}\n{colored(''.rjust(60, '#'), 'yellow')}""")
        obj = bitkub.get_candle(asset, timeframe='1D')
        trends = bitkub.trand_ema(asset ,obj, fast_length=7, slow_length=45)
        print(trends)
        
        ### end
        print(f"\n{''.rjust(60, '-')}")
        i += 1
    
    # asset = "KUB"
    # # timeframe = ช่วงเวลาของกราฟที่จะดึงข้อมูล 1, 5, 15, 60, 240, 1D
    # obj = bitkub.get_candle(symbol=asset, timeframe="240")
    # trends = bitkub.trand_ema(asset ,obj, fast_length=7, slow_length=45)
    # print(trends)
    
    
if __name__ == '__main__':
    main()
    sys.exit(0)
    