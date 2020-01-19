import json
import javalang
import nltk
import os
import random

# Usage:
# Read DeepCom's dataset, then filter the data through specific rules, and finally save the data as a smaller dataset

def is_invalid_method(code: str, nl: str):   
    tokens_parse = javalang.tokenizer.tokenize(code)
    token_len = len(list(tokens_parse))
    
    if token_len > 350 or len(code.split('\n')) > 40:
        return True
    if len(nl.split('.')) != 1 or len(nltk.word_tokenize(nl)) > 30:
        return True
    else :
        return False

path_list = ['./DeepCom_data/train.json', './DeepCom_data/test.json']
save_path = './simplified_dataset'

inputs = []
for path in path_list:
    input_file = open(path)
    inputs.extend(input_file.readlines())
    input_file.close()
outputs = []

if not os.path.exists(save_path):
    os.makedirs(save_path)
    
output_train_file = open(save_path+'/simplified_train.json', "w")
output_test_file = open(save_path+'/simplified_test.json', "w")

print('Original total: '+str(len(inputs)))
for pair in inputs:
    pair = json.loads(pair)
    if is_invalid_method(pair['code'], pair['nl']):
        continue
    outputs.append(json.dumps(pair))

random.shuffle(outputs)
print('Final total: '+str(len(outputs)))
print('Data shuffle complete')
train_index = int(len(outputs)*0.9)
test_index = int(len(outputs)-1)
train_output = outputs[:train_index]
test_output = outputs[train_index+1:test_index]

for row in train_output:
    output_train_file.write(row+'\n')
output_train_file.close()
print('simplified train data finish writing')
for row in test_output:
    output_test_file.write(row+'\n')
output_test_file.close()
print('simplified test data finish writing')
