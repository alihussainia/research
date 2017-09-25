from oandapyV20 import API
import oandapyV20.endpoints.pricing as pricing
import oandapyV20.endpoints.orders as orders
from datetime import datetime
import pandas as pd


class ForexSystem:
    def __init__(self, *args, **kwargs):
        self.account_id = None
        self.client = API(access_token=kwargs["access_token"])
        self.instrument = None
        self.qty = 0
        self.interval = None
        self.mean_period_short = 5
        self.mean_period_long = 20
        self.buy_threshold = 1.0
        self.sell_threshold = 1.0

        self.prices = pd.DataFrame()
        self.beta = 0
        self.is_position_opened = False
        self.opening_price = 0
        self.executed_price = 0
        self.unrealized_pnl = 0
        self.realized_pnl = 0
        self.position = 0
        self.dt_format = "%Y-%m-%dT%H:%M:%S.%fZ"

    def begin(self,**params):
        self.instrument = params["instruments"]
        self.account_id = params["account_id"]
        self.qty = params["qty"]
        self.interval = params["interval"]
        self.mean_period_short = params["mean_period_short"]
        self.mean_period_long = params["mean_period_long"]
        self.buy_threshold = params["buy_threshold"]
        self.sell_threshold = params["sell_threshold"]

        self.start(**params)  # Start streaming prices

    def parse_data(self,data):
        if(data['type']=='PRICE'):
            return data['time'],data['instrument'],data['closeoutBid'],data['closeoutAsk']

    def start(self,**params):
        r=pricing.PricingStream(self.account_id,params)
        rv=self.client.request(r)
        for tick in rv:
            if(tick['type']!='HEARTBEAT'):
                print(tick)
                self.on_success(tick)
    
    def on_success(self,tick):
        time,instrument,bid,ask = self.parse_data(tick)
        self.tick_event(time,instrument,float(bid),float(ask))

    def tick_event(self,time,instrument,bid,ask):
        time = pd.to_datetime(time)
        midprice = (ask+bid)/2.
        self.prices.loc[time, instrument] = midprice
        print(self.prices)
        resampled_prices = self.prices.resample(self.interval).last()

        mean_short = resampled_prices.tail(
            self.mean_period_short).mean()[0]
        mean_long = resampled_prices.tail(
            self.mean_period_long).mean()[0]
        self.beta = mean_short / mean_long

        self.perform_trade_logic(self.beta)

    def perform_trade_logic(self, beta):
        if beta > self.buy_threshold:
            if not self.is_position_opened \
                    or self.position < 0:
                self.check_and_send_order(True)

        elif beta < self.sell_threshold:
            if not self.is_position_opened \
                    or self.position > 0:
                self.check_and_send_order(False)

    def check_and_send_order(self,is_true):
        order = {
            "order": {
                "instrument": self.instrument,
                "units": self.qty,
                "type": "MARKET",
                "positionFill": "DEFAULT"                  
            }
        }

        req = orders.OrderCreate(self.account_id,order)
        self.client.request(req)
        print(req.response)


def main():
    key = '04e86c6b0c7bfe71bf7f98d2b1a6496d-dee13f6f97c4508b949c42deaf95925b'
    account_id = '101-001-6722193-001'
    system = ForexSystem(access_token=key)
    system.begin(account_id=account_id,
             instruments="EUR_USD",
             qty=1000,
             interval= '10s',
             mean_period_short=5,
             mean_period_long=20,
             buy_threshold=1.0,
             sell_threshold=1.0)    

if __name__ == '__main__':
    main()