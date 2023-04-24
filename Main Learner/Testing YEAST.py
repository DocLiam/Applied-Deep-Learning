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

Model.test(Data)

mean_error = 0
rms_error = 0

for i in range(len(Data.target_values)):
    mean_error += abs((Model.output_values[i]-Data.target_values[i]))
    rms_error += (Model.output_values[i]-Data.target_values[i])**2
    
mean_error /= len(Data.target_values)
rms_error = (rms_error/Decimal(len(Data.target_values)))**Decimal(0.5)

print(mean_error)
print(rms_error)

f = plt.figure()
f, axes = plt.subplots(nrows = 2, ncols = 2, sharex=False, sharey=False)

for i in range(len(Model.output_values)):
    axes[[0,1,0,1][i%4]][[0,0,1,1][i%4]].scatter(Data.target_values[i], Model.output_values[i], color=["blue", "red", "yellow", "green"][i%4])
    
plt.show()