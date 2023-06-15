from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import matplotlib.pyplot as plt
from numpy import complex128
from DeepLearningOptimized import Model_DL
from DeepLearningOptimized import Data_DL
from decimal import *
from time import *

getcontext().prec = 64

model_name = input("Model name: ")


Trade_Model = Model_DL.model()
Trade_Model.load(model_name, min_diff=0.00000001, learning_rate=0.00002, cycles=15)

Trade_Data_test = Data_DL.data()

Trade_Data_train = Data_DL.data()
Trade_Data_validate = Data_DL.data()



api_key = "xtJNJ5ye25ze6DbFrX9zlMrcl16IyDeSUdAKVBOTou5vEb7RDWlFRTzK2EvurcJD"
secret_key = "YU3boe3opckvNEwVvFpSEVm4JPjMheFOHIbtUDSEmQdlPn9OMhou2WWNPyQOg1yA"

client = Client(api_key, secret_key)



ticker = "BTCUSDT"

trade_fees = Decimal(0.000)

USDT_principal = Decimal(100)

C1_balance = Decimal(0)
C2_balance = Decimal(0)

fees_paid = Decimal(0)

average_size = 6

start_flag = True



last_input_values = []
last_target_values = []

action_values = []

i = 0


prep_flag = True


x_values = [i for i in range(Trade_Model.input_count)]

C1C2_klines = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_1MINUTE, "2 hours ago UTC")

while True:
    temp_C1C2_klines = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_1MINUTE, "1 minute ago UTC")
    
    try:
        if temp_C1C2_klines[-1][0] != C1C2_klines[-1][0]:
            C1C2_klines = C1C2_klines[1:]+temp_C1C2_klines
            
        if len(ticker[3:]) == 3:
            C1USDT_rate = Decimal(client.get_historical_klines(ticker[:3] + "USDT", Client.KLINE_INTERVAL_1MINUTE, "1 minute ago UTC")[0][4])
            C2USDT_rate = Decimal(client.get_historical_klines(ticker[3:] + "USDT", Client.KLINE_INTERVAL_1MINUTE, "1 minute ago UTC")[0][4])
        else:
            C1USDT_rate = Decimal(temp_C1C2_klines[-1][4])
            C2USDT_rate = Decimal(1)
    except:
        continue
    
    previous_rates = [Decimal(element[4]) for element in C1C2_klines]

    moving_average_previous_rates = [sum(previous_rates[i:i+average_size])/Decimal(average_size) for i in range(len(previous_rates)-average_size+1)]
    
    change_moving_average_rates = [moving_average_previous_rates[i+1]/moving_average_previous_rates[i] for i in range(len(moving_average_previous_rates)-1)]
    
    C1C2_rate = previous_rates[-1]
    
    if prep_flag:
        C2_balance = USDT_principal/C2USDT_rate
        
        last_C1_balance = C1_balance
        
        prep_flag = False

        
    
    Trade_Data_test.load(input_values=change_moving_average_rates[-Trade_Model.input_count:], target_values=[], stream=False, shift_count=Trade_Model.input_count)
    
    Trade_Model.test(Trade_Data_test)



    
    value_C1 = C1USDT_rate*C1_balance
    value_C2 = C2USDT_rate*C2_balance
    
    value_total = value_C1 + value_C2
    
    
    print(Trade_Model.output_values[-1])
    
    action_values += [Trade_Model.output_values[-1]]
    
    if last_C1_balance != C1_balance:
        last_input_values += prev_input_values
        
        if not start_flag:
            action = last_decision if prev_value_total > last_value_total else not last_decision
            last_target_values += [Decimal(1) if action else Decimal(0)]
        
        last_decision = prev_decision
        last_value_total = prev_value_total
        
        start_flag = False
        
    last_C1_balance = C1_balance
    
    prev_input_values = change_moving_average_rates[-Trade_Model.input_count:].copy()
    prev_decision = (Trade_Model.output_values[-1] >= 0.5)
    prev_value_total = value_total
    
    if not start_flag:
        action = last_decision if value_total > last_value_total else not last_decision
        print(action)
        
        temp_last_target_values = last_target_values + [Decimal(1) if action else Decimal(0)]
        
        halfway_index = len(temp_last_target_values)//2
        
        Trade_Data_train.load(input_values=last_input_values[halfway_index*Trade_Model.input_count:], target_values=temp_last_target_values[halfway_index:], stream=False, shift_count=Trade_Model.input_count)
        Trade_Data_validate.load(input_values=last_input_values[:halfway_index*Trade_Model.input_count], target_values=temp_last_target_values[:halfway_index], stream=False, shift_count=Trade_Model.input_count)
        
        Trade_Model.train(Trade_Data_train, Trade_Data_validate)
        
        if i%3 == 0:
            Trade_Model.save()
    
    i += 1
    
    
    
    if Trade_Model.output_values[-1] < 0.5 and C2_balance != Decimal(0):
        fees_paid += trade_fees*(C2_balance*C2USDT_rate)
        
        C1_balance = (Decimal(1)-trade_fees)*(C2_balance/C1C2_rate)
        C2_balance = Decimal(0)
    elif Trade_Model.output_values[-1] >= 0.5 and C1_balance != Decimal(0):
        fees_paid += trade_fees*(C1_balance*C1USDT_rate)
        
        C2_balance = (Decimal(1)-trade_fees)*(C1_balance*C1C2_rate)
        C1_balance = Decimal(0)
    
    
    
    C1USDT_value = C1_balance*C1USDT_rate
    C2USDT_value = C2_balance*C2USDT_rate
    USDT_value = C1USDT_value+C2USDT_value
    
    

    print(ticker[:3] + " value in USDT: " + str(float(C1_balance*C1USDT_rate)))
    print(ticker[3:] + " value in USDT: " + str(float(C2_balance*C2USDT_rate)))
    print("Total value in USDT: " + str(float(USDT_value)))
    print("Total fees paid in USDT: " + str(float(fees_paid)))
    print("Total value generated in USDT: " + str(float(USDT_value+fees_paid)))
    print("\n")
    
    
    
    plt.clf()
    plt.plot(x_values, previous_rates[-Trade_Model.input_count:])
    plt.pause(0.001)