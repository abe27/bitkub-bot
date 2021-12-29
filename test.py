import sys
from crytoex.bitkub import Bitkub

from dotenv import load_dotenv
# Initialize Environment
load_dotenv()

bitkub = Bitkub()

def main():
    balance = bitkub.get_balance_assets()
    print(list(balance))
    
if __name__ == '__main__':
    main()
    sys.exit(0)
    