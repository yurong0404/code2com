# code2com

這是一個將程式碼透過深度學習，自動翻譯成註解的研究，目標程式碼以function為單位，而註解會說明該段function的程式邏輯

This is a study that automatically translates the code into comments through deep learning. The target code is in units of functions, and the comments will explain the program logic of the function.

TensorFlow version: 2.1.0
TensorFlow.keras version: 2.2.4-tf
***

## filter_dataset.py

本研究的dataset源自於DeepCom，這個script會將DeepCom的dataset經過自己設立的規則做篩選，並存成較精簡的dataset（simplified_train.json和simplified_test.json）

The dataset in this study is derived from DeepCom. This script will filter the DeepCom dataset through its own rules and save it as a smaller dataset (simplified_train.json and simplified_test.json).
***
## readdata.py
由於當程式讀取dataset後，dataset需要經過預處理(變數切割等等)才能丟入深度學習模型做訓練。但這過程程式需要大量時間做處理，為了節省日後的處理時間，這個script會把深度學習模型需要的資訊，從dataset經過預處理後，存成pickle檔，之後若需要讀取dataset只需要讀pickle檔並還原成模型所需的變數格式，這將大量節省日後研究所花的時間成本。

After the dataset is read by the program, the dataset needs to be pre-processed (variable splitting, etc.) to be thrown into the deep learning model for training. However, this process requires a lot of time to process. In order to save processing time in the future, this script will save the information required by the deep learning model from the dataset after preprocessing and save it as a pkl file. If you need to read the dataset, you only need to read the pkl file and restore it to the variable format required by the model, which will save a lot of time and costs for future research.
***
## train_lstm.py
This script trains the lstm version of seq2seq model

## train_bilstm.py
This script trains the bi-lstm version of seq2seq model
***
## param.py
這個檔案的功能是設定其他script所需的全域變數(如欲選取的模型)，以及模型訓練的參數等

The function of this file is to set the global variables (such as the model to be selected) required by other scripts, and the hyper-parameters of model foo training
***
## predict.py
這檔案讀取已訓練好的模型，並且選取特定程式碼，使用該模型翻譯註解

This script restores the pre-trained model and translate specific codes to comment via the model.
***
## evaluate.py
這檔案讀取已訓練好的模型，並且使用bleu3、bleu4評測該模型

This script restores the trained model and evaluates the model with bleu3, bleu4