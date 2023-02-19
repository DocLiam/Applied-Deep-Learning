from DeepLearningOptimized import Model_DL
from DeepLearningOptimized import Data_DL
import matplotlib.pyplot as plt

data_name = input("Data name: ")
model_name = input("Model name: ")

Model = Model_DL.model()
Model.load(model_name)

Data = Data_DL.data()
Data.extract(data_name + "TEST")

Model.test(Data)

print(Model.output_values)