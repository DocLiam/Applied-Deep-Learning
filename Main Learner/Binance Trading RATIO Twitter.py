from binance import Client, ThreadedWebsocketManager, ThreadedDepthCacheManager
import matplotlib.pyplot as plt
from numpy import complex128
from DeepLearningOptimized import Model_DL
from DeepLearningOptimized import Data_DL
from decimal import *
from time import *

getcontext().prec = 64

model_name = input("Model name: ")
model_count = int(input("Model count: "))

Trade_Models = []

for i in range(model_count):
    Trade_Models.append(Model_DL.model())
    Trade_Models[i].load(model_name+str(i), min_diff=0.00000004, learning_rate=0.00000004, cycles=4)

Trade_Data_test = Data_DL.data()

Trade_Data_uncertainty = Data_DL.data()

Trade_Data_train = Data_DL.data()
Trade_Data_validate = Data_DL.data()



api_key = ""
secret_key = ""

client = Client(api_key, secret_key)



ticker = "BTCEUR"

trade_fees = Decimal(0.0)

USDT_principal = Decimal(100)

C1_balance = Decimal(0)
C2_balance = Decimal(0)

fees_paid = Decimal(0)

predicted_count = 15

average_size = 10

start_flag = True



x_values = [i for i in range(Trade_Models[0].input_count+predicted_count)]

C1C2_klines = client.get_historical_klines(ticker, Client.KLINE_INTERVAL_1MINUTE, "24 hours ago UTC")

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
    
    if start_flag:
        C2_balance += USDT_principal/C2USDT_rate
    
    
    
    input_values_test = []
    target_values_test = []
    
    for i in range(len(change_moving_average_rates)-Trade_Models[0].input_count+1):
        input_values_test += change_moving_average_rates[i:i+Trade_Models[0].input_count]
    
    for i in range(len(change_moving_average_rates)-Trade_Models[0].input_count-Trade_Models[0].output_count+1):
        target_values_test += change_moving_average_rates[i+Trade_Models[0].input_count:i+Trade_Models[0].input_count+Trade_Models[0].output_count]
    
    Trade_Data_test.load(input_values_test, target_values_test)
    
    recursive_output_values = [Decimal(0) for i in range(predicted_count)]
    
    for i in range(model_count):
        Trade_Models[i].recursive_test(Trade_Data_test, loop_count=predicted_count, feedback_count=5, pivot_value=1, auto_adjust=False)
        
        for j in range(predicted_count):
            recursive_output_values[j] += Trade_Models[i].recursive_output_values[-predicted_count+j]/Decimal(model_count)



    compounded_multiplier = Decimal(1)
    compounded_moving_change = []
    
    for multiplier in recursive_output_values:
        compounded_multiplier *= multiplier

        compounded_moving_change.append(compounded_multiplier-Decimal(1))
        
    compounded_actual_change = []

    for change in compounded_moving_change:
        compounded_actual_change.append((moving_average_previous_rates[-1]*(change+Decimal(1)))/C1C2_rate-Decimal(1))



    uncertainty_values_lower = [Decimal(0) for i in range(predicted_count)]
    uncertainty_values_upper = [Decimal(0) for i in range(predicted_count)]
    
    step = 5

    for h in range(0, len(change_moving_average_rates)-Trade_Models[0].input_count+1-predicted_count, step):
        input_values_uncertainty = input_values_test[h*Trade_Models[0].input_count:h*Trade_Models[0].input_count+Trade_Models[0].input_count]
        target_values_uncertainty = target_values_test[h*Trade_Models[0].output_count:h*Trade_Models[0].output_count+Trade_Models[0].output_count]
        
        Trade_Data_uncertainty.load(input_values_uncertainty, target_values_uncertainty)
        
        recursive_output_values_uncertainty = [Decimal(0) for i in range(predicted_count)]
        
        for i in range(model_count):
            Trade_Models[i].recursive_test(Trade_Data_uncertainty, loop_count=predicted_count, feedback_count=1, pivot_value=1, auto_adjust=False)
            
            for j in range(predicted_count):
                recursive_output_values_uncertainty[j] += Trade_Models[i].recursive_output_values[-predicted_count+j]/Decimal(model_count)
        
        
        
        compounded_multiplier_real = Decimal(1)
        compounded_multiplier_uncertainty = Decimal(1)
        
        for i in range(predicted_count):
            compounded_multiplier_real *= change_moving_average_rates[Trade_Models[0].input_count+h+i]
            compounded_multiplier_uncertainty *= recursive_output_values_uncertainty[i]
            
            uncertainty_level = compounded_multiplier_real-compounded_multiplier_uncertainty
            
            if uncertainty_level < 0:
                uncertainty_values_lower[i] += uncertainty_level/Decimal((len(change_moving_average_rates)-Trade_Models[0].input_count+1-predicted_count)/step)
            if uncertainty_level > 0:
                uncertainty_values_upper[i] += uncertainty_level/Decimal((len(change_moving_average_rates)-Trade_Models[0].input_count+1-predicted_count)/step)
    
    
    
    compounded_moving_change_lower = [compounded_moving_change[i]+uncertainty_values_lower[i] for i in range(predicted_count)]
    compounded_moving_change_upper = [compounded_moving_change[i]+uncertainty_values_upper[i] for i in range(predicted_count)]
    
    compounded_actual_change_lower = [compounded_actual_change[i]+uncertainty_values_lower[i] for i in range(predicted_count)]
    compounded_actual_change_upper = [compounded_actual_change[i]+uncertainty_values_upper[i] for i in range(predicted_count)]
    
    
    
    y_values_average = moving_average_previous_rates[-Trade_Models[0].input_count:]
    y_values_lower = []
    y_values_upper = []
    
    for i in range(predicted_count):
        y_values_average.append(moving_average_previous_rates[-1]*(compounded_moving_change[i]+Decimal(1)))
        y_values_lower.append(moving_average_previous_rates[-1]*(compounded_moving_change_lower[i]+Decimal(1)))
        y_values_upper.append(moving_average_previous_rates[-1]*(compounded_moving_change_upper[i]+Decimal(1)))
            
            

    C1_target_proportion = Decimal(0)
    C2_target_proportion = Decimal(0)
    
    for i in range(predicted_count):
        temp_C1_proportion = compounded_actual_change_upper[i]/(compounded_actual_change_upper[i]-compounded_actual_change_lower[i])
        temp_C2_proportion = compounded_actual_change_lower[i]/(compounded_actual_change_upper[i]-compounded_actual_change_lower[i])
        
        if temp_C1_proportion > 1 or temp_C2_proportion > 0:
            temp_C1_proportion = Decimal(1)
            temp_C2_proportion = Decimal(0)
        if temp_C2_proportion < -1 or temp_C1_proportion < 0:
            temp_C1_proportion = Decimal(0)
            temp_C2_proportion = Decimal(1)
        
        C1_target_proportion += abs(temp_C1_proportion)/Decimal(predicted_count)
        C2_target_proportion += abs(temp_C2_proportion)/Decimal(predicted_count)
        
    C1USDT_value = C1_balance*C1USDT_rate
    C2USDT_value = C2_balance*C2USDT_rate
    USDT_value = C1USDT_value+C2USDT_value
    
    C1_actual_proportion = C1USDT_value/USDT_value
    C2_actual_proportion = C2USDT_value/USDT_value
    
    if C1_actual_proportion == 0:
        C1_proportion_change = Decimal(0)
    else:
        C1_proportion_change = Decimal(1)-C1_target_proportion/C1_actual_proportion
    if C2_actual_proportion == 0:
        C2_proportion_change = Decimal(0)
    else:
        C2_proportion_change = Decimal(1)-C2_target_proportion/C2_actual_proportion
    

    
    if C1_proportion_change <= 0:
        fees_paid += trade_fees*((C2_proportion_change*C2_balance)*C2USDT_rate)
        
        C1_balance += (Decimal(1)-trade_fees)*((C2_proportion_change*C2_balance)/C1C2_rate)
        C2_balance *= (Decimal(1)-C2_proportion_change)
    if C2_proportion_change <= 0:
        fees_paid += trade_fees*((C1_proportion_change*C1_balance)*C1USDT_rate)
        
        C2_balance += (Decimal(1)-trade_fees)*((C1_proportion_change*C1_balance)*C1C2_rate)
        C1_balance *= (Decimal(1)-C1_proportion_change)
    
    
    
    C1USDT_value = C1_balance*C1USDT_rate
    C2USDT_value = C2_balance*C2USDT_rate
    USDT_value = C1USDT_value+C2USDT_value
    
    

    print(ticker[:3] + " target proportion in USDT: " + str(float(C1_target_proportion)))
    print(ticker[3:] + " target proportion in USDT: " + str(float(C2_target_proportion)))
    print(ticker[:3] + " value in USDT: " + str(float(C1_balance*C1USDT_rate)))
    print(ticker[3:] + " value in USDT: " + str(float(C2_balance*C2USDT_rate)))
    print("Total value in USDT: " + str(float(USDT_value)))
    print("Total fees paid in USDT: " + str(float(fees_paid)))
    print("Total value generated in USDT: " + str(float(USDT_value+fees_paid)))
    print("\n")
    
    
    
    plt.clf()
    plt.plot(x_values, y_values_average)
    plt.plot(x_values[-predicted_count:], y_values_lower)
    plt.plot(x_values[-predicted_count:], y_values_upper)
    plt.plot(x_values[:-predicted_count], previous_rates[-Trade_Models[0].input_count:])
    plt.pause(0.001)
    
    
    
    input_values_train = input_values_test[:-Trade_Models[0].input_count*Trade_Models[0].output_count]
    target_values_train = target_values_test
    
    Trade_Data_train.load(input_values_train[int(len(input_values_train)/2):], target_values_train[int(len(target_values_train)/2):])
    Trade_Data_validate.load(input_values_train[:int(len(input_values_train)/2)], target_values_train[:int(len(target_values_train)/2)])
    
    for i in range(model_count):
        Trade_Models[i].train(Trade_Data_train, Trade_Data_validate)
        Trade_Models[i].save()
    
    
    
    start_flag = False