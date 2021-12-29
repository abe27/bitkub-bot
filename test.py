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
    # i = 0
    # while i < len(assets):
    #     r = assets[i]
    #     id          = r['id']
    #     info        = r['info']
    #     symbol      = r['symbol']
    #     gbal        = r['global']
    #     currency    = r['currency']
        
    #     # print(id,info,symbol,gbal,currency)
    #     get_price = bitkub.get_last_price(gbal)
    #     current = 0
    #     if get_price:
    #         current = float(get_price['last'])

    #     print(f"""Check Assets({colored(symbol, 'blue')})\nValue: {colored(f'{current:,}', 'yellow')} per {colored(currency, 'blue')}\n{colored(''.rjust(60, '#'), 'yellow')}""")
    #     obj = bitkub.get_candle(symbol, '1D')
        
    #     ### end
    #     print(f"\n{''.rjust(60, '-')}")
    #     i += 1
    
    symbol = "ETH"
    obj = bitkub.get_candle(symbol, '1D')
    trends = bitkub.trand_ema(symbol ,obj, fast_length=7, slow_length=45)
    
    
if __name__ == '__main__':
    main()
    sys.exit(0)
    