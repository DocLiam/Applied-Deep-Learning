from audioop import rms
from statistics import median
from DeepLearningOptimized import Model_DL
from DeepLearningOptimized import Data_DL
from decimal import *
import matplotlib.pyplot as plt

data_name = input("Data name: ")
model_name = input("Model name: ")

Model = Model_DL.model()
Model.load(model_name)

Data = Data_DL.data()
Data.extract(data_name + "TEST")

Model.test(Data)

print(Model.output_values)

to_write = ""

for i in range(int(len(Model.output_values)/Model.output_count)):
    to_write += ",".join([str(j) for j in Model.output_values[i*Model.output_count:(i+1)*Model.output_count]]) + "\n"

filew = open("./" + model_name + "/OUTPUT.txt", "w")
filew.write(to_write[:-1])
filew.close()