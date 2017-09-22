import oandapyV20
from oandapyV20 import API
import oandapyV20.endpoints.pricing as pricing
import json
accountID = "101-001-6722193-001"
api = API(access_token="04e86c6b0c7bfe71bf7f98d2b1a6496d-dee13f6f97c4508b949c42deaf95925b")
params ={"instruments": "EUR_USD,EUR_JPY"}
r = pricing.PricingStream(accountID,params=params)
rv = api.request(r)
maxrecs = 2
for ticks in rv:
    print(json.dumps(ticks,indent=4),",") 
    if maxrecs == 0:
        r.terminate("maxrecs records received")