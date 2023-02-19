from DeepLearningOptimized import Model_DL
from DeepLearningOptimized import Data_DL
import matplotlib.pyplot as plt
from decimal import *

data_name = input("Data name: ")
model_name = input("Model name: ")

Model = Model_DL.model()
Model.load(model_name)

Data = Data_DL.data()
Data.extract(data_name + "TEST")

header_count = 1

Model.recursive_test(Data, 200, header_count)

header_values = [[Model.recursive_output_values[j*header_count+i] for j in range(int(len(Model.recursive_output_values)/header_count))] for i in range(header_count)]

x_values = [i for i in range(int(len(Model.recursive_output_values)/header_count))]

for i in range(header_count):
    y_values = []
    cumulative_change = Decimal(0)
    
    for value in header_values[i]:
        y_values.append(value)
        cumulative_change += value
    
    plt.plot(x_values, y_values)

plt.show()