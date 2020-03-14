import javalang
import json
import re
import time
import nltk
#nltk.download('punkt')
import numpy as np
import pickle
import os
import tensorflow as tf
import matplotlib.pyplot as plt
import math
import seaborn as sns
from param import *
    
    
'''
Function: 
    Input the root of AST and the deep of the tree, 
    it will filter the null value and return the list of SBT (structural-based travesal) and print the tree structure
'''
def parse_tree(root, deep):
    seq = []
    seq.extend(['(', str(root).split('(')[0]])
    #print('\t'*(deep)+str(root).split('(')[0])    # show node name
    if not hasattr(root, 'attrs'):  # error-handling
        return []
    for attr in root.attrs:
        if eval('root.%s' % attr) in [None, [], "", set(), False]:    # filter the null attr
            continue
        elif isinstance(eval('root.%s' % attr), list):
            x = eval('root.%s' % attr)
            if not all(elem in x for elem in [None, [], "", set(), False]):    # if not all elements in list are null
                seq.extend(['(',attr])
                #print('\t'*(deep+1)+attr)
                #deep += 1
                for i in eval('root.%s' % attr):    # recursive the list
                    if i is None or isinstance(i, str):    # perhaps it has None value in the list
                        continue
                    #deep += 1
                    seq.extend(parse_tree(i, deep))
                    
                    #deep -= 1
                #deep -= 1
                seq.extend([')',attr])
        elif 'tree' in str(type(eval('root.%s' % attr))):    #if the attr is one kind of Node, recursive the Node
            seq.extend(['(',attr])
            #print('\t'*(deep+1)+attr)
            #deep += 2
            seq.extend(parse_tree(eval('root.%s' % attr), deep))
            #deep -= 2
            seq.extend([')',attr])
        else:
            seq.extend(['(','<'+str(attr)+'>_'+str(eval('root.%s' % attr)),')','<'+str(attr)+'>_'+str(eval('root.%s' % attr))])
            #exec("print('\t'*(deep+1)+attr+': '+str(root.%s))" % attr)    #it must be normal attribute
    seq.extend([')', str(root).split('(')[0]])
    return seq


'''
Usage:
    1. "camelCase" -> ["camel", "Case"]
    2. "snake_case" -> ["snake", "_", "case"]
    3. "normal" -> ["normal"]
'''
def split_identifier(id_token: str):
    if  "_" in id_token:
        return id_token.split("_")
    elif id_token != id_token.lower() and id_token != id_token.upper():
        matches = re.finditer('.+?(?:(?<=[a-z])(?=[A-Z])|(?<=[A-Z])(?=[A-Z][a-z])|$)', id_token)
        return [m.group(0) for m in matches]
    else:
        return [id_token]



'''
Usage:
    Transform the token to the index in vocabulary
    ['<START>', '<Modifier>', 'public', ..., '<Separator>', ';', '<Separator>', '}', '<END>']
    => [0, 7, 8, ..., 14, 29, 14, 30, 1]
'''
def token2index(lst: list, voc: list) -> list:
    for index, seq in enumerate(lst):
        seq_index = []
        for token in seq:
            seq_index.append(voc.index(token))
        lst[index] = seq_index
    return lst


def pad_sequences(lst: list, pad_data: int):
    maxlen = max(len(x) for x in lst)
    for index, seq in enumerate(lst):
        lst[index].extend([pad_data] * (maxlen-len(seq)))
    return np.array(lst)

'''
Return shape:
    [None, batch_sz, None]
Example:
    a = [1,2,3,4,5,6,7,8,9,10]
    a = getBatch(x=a, batch_sz=3)
    a
    ---output---
    [[1,2,3], [4,5,6], [7,8,9]]
'''
def getBatch(x: list, batch_sz: int):
    dataset = []
    while(len(x)>=batch_sz):
        dataset.append(x[:batch_sz])
        x = x[batch_sz:]
    if type(x) == np.ndarray:
        return np.array(dataset)
    elif type(x) == list:
        return dataset
    
def ngram(words, n):
    return list(zip(*(words[i:] for i in range(n))))


def code_to_index(inputs, code_voc, max_length_inp):
    if MODE=="simple" or MODE=="normal":
        for index, token in enumerate(inputs):
            if token not in code_voc:
                inputs[index] = code_voc.index('<UNK>')
            else:
                inputs[index] = code_voc.index(token)
                
    elif MODE=="SBT":
        typename = ['<modifiers>', '<member>', '<value>', '<name>', '<operator>', '<qualifier>']
        for index, token in enumerate(inputs):
            if token not in code_voc:
                tmp = token.split('_')
                if len(tmp) > 1 and tmp[0] in typename:
                    inputs[index] = code_voc.index(tmp[0])
                else:
                    inputs[index] = code_voc.index("<UNK>")
            else:
                inputs[index] = code_voc.index(token)
                
    inputs += [code_voc.index('<PAD>')] * (max_length_inp - len(inputs))
    inputs = np.array(inputs)
    inputs = tf.expand_dims(inputs, 0)

    return inputs


def code_tokenize(code):
    inputs = []
    if MODE =="simple":
        tokens_parse = javalang.tokenizer.tokenize(code)
        for token in tokens_parse:    # iterate the tokens of the sentence
            token = str(token).split(' ')
            splitted_id = split_identifier(token[1].strip('"'))    # split the camelCase and snake_case
            inputs.extend(splitted_id)
    elif MODE == "normal":
        tokens_parse = javalang.tokenizer.tokenize(code)
        for token in tokens_parse:    # iterate the tokens of the sentence
            token = str(token).split(' ')
            splitted_id = split_identifier(token[1].strip('"'))    # split the camelCase and snake_case
            temp = ['<'+token[0]+'>']    # token[0] is token type, token[1] is token value
            temp.extend(splitted_id)
            inputs.extend(temp)
            
    elif MODE == "SBT":
        tree = javalang.parse.parse('class aa {'+code+'}')
        _, node = list(tree)[2]    # 前兩個用來篩掉class aa{ }的部分
        inputs = parse_tree(node, 0)
        if len(inputs) == 0:   # error-handling due to dirty data
            return []

    inputs.insert(0, '<START>')
    inputs.append('<END>')
    
    return inputs


'''
用途：把一個二維的array做機率正規化
例如：[[3,4,5],[1,2,3]] -> [[0.25, 0.33, 0.416], [0.167, 0.333, 0.5]]
'''
def distribution(arr):
    new_arr = []
    for i in arr:
        tmp = []
        total = sum(i)
        for x in i:
            tmp.append(x/total)
        new_arr.append(tmp)
    return np.array(new_arr)

def translate(code, encoder, decoder, code_voc, comment_voc, max_length_inp, max_length_targ):
    
    inputs = code_tokenize(code)
    inputs = code_to_index(inputs, code_voc, max_length_inp)
    
    result = ''
    
    hidden_h, hidden_c = tf.zeros((1, UNITS)), tf.zeros((1, UNITS))
    hidden = [hidden_h, hidden_c]
    enc_output, enc_hidden_h, enc_hidden_c = encoder(inputs, hidden)
    dec_hidden = [enc_hidden_h, enc_hidden_c]
    dec_input = tf.expand_dims([comment_voc.index('<START>')], 1)       
    
    for t in range(max_length_targ):
        predictions, dec_hidden_h, dec_hidden_c, attention_weights = decoder(dec_input, dec_hidden, enc_output)
        dec_hidden = [dec_hidden_h, dec_hidden_c]
        predicted_id = tf.argmax(predictions[0]).numpy()
        if comment_voc[predicted_id] == '<END>':
            return result
        result += comment_voc[predicted_id] + ' '
        # the predicted ID is fed back into the model
        dec_input = tf.expand_dims([predicted_id], 0)

    return result

def translate_bilstm(code, encoder, decoder, code_voc, comment_voc, max_length_inp, max_length_targ):
    inputs = code_tokenize(code)
    inputs = code_to_index(inputs, code_voc, max_length_inp)

    result = ''
    hidden = tf.zeros((1, UNITS))
    enc_output, enc_forward_h, enc_forward_c, enc_backward_h, enc_backward_c = encoder(inputs, hidden, hidden, hidden, hidden)
    dec_hidden = [enc_forward_h, enc_forward_c, enc_backward_h, enc_backward_c]
    dec_input = tf.expand_dims([comment_voc.index('<START>')], 1)

    for t in range(max_length_targ):
        predictions, dec_forward_h, dec_forward_c, dec_backward_h, dec_backward_c = decoder(dec_input, dec_hidden, enc_output)
        dec_hidden = [dec_forward_h, dec_forward_c, dec_backward_h, dec_backward_c]
        predicted_id = tf.argmax(predictions[0]).numpy()
        if comment_voc[predicted_id] == '<END>':
            return result
        result += comment_voc[predicted_id] + ' '
        # the predicted ID is fed back into the model
        dec_input = tf.expand_dims([predicted_id], 0)

    return result


def beam_search_predict_word(lock, score, result, decoder, dec_input, dec_hidden, enc_output, comment_voc, width):
    can_lock = [0] * (width ** 2)
    can_input = [''] * (width ** 2)
    can_score = [1] * (width ** 2)
    can_result = [''] * (width ** 2)

    for i in range(width):
        for x in range(width):
            can_score[width*i+x] = score[i]
            can_result[width*i+x] = result[i]
        if lock[i] == 1:
            for x in range(width):
                can_lock[width*i+x] = 1
            continue
        
        if BIDIRECTIONAL == 0:
            predictions, dec_hidden_h, dec_hidden_c, attention_weights = decoder(dec_input[i], dec_hidden[i], enc_output)
            dec_hidden[i] = [dec_hidden_h, dec_hidden_c]
        elif BIDIRECTIONAL == 1:
            predictions, dec_forward_h, dec_forward_c, dec_backward_h, dec_backward_c = decoder(dec_input[i], dec_hidden[i], enc_output)
            dec_hidden[i] = [dec_forward_h, dec_forward_c, dec_backward_h, dec_backward_c]
            
        predictions = tf.nn.softmax(predictions)
        topk_score = tf.math.top_k(predictions[0], width)[0]
        topk_id = tf.math.top_k(predictions[0], width)[1]
        
        for x in range(width):
            can_score[width*i+x] *= topk_score[x].numpy()
            if comment_voc[topk_id[x].numpy()] == '<END>':
                can_lock[width*i+x] = 1
            else:
                can_result[width*i+x] += comment_voc[topk_id[x].numpy()] + ' '
                can_input[width*i+x] = topk_id[x].numpy()
    return can_lock, can_score, can_result, can_input, dec_hidden

def beam_search_generate_topk_candidate(can_score, can_result, can_lock, can_input, result, score, lock, dec_hidden, dec_input, width):
    sorted_index = sorted(range(len(can_score)), key=lambda k: can_score[k], reverse=True)[:width]
    for x in range(width):
        result[x] = can_result[sorted_index[x]]
        score[x] = can_score[sorted_index[x]]
        if can_lock[sorted_index[x]] == 1:
            lock[x] = 1
        else:
            dec_input[x] = tf.expand_dims([can_input[sorted_index[x]]], 0)
        dec_hidden[x] = dec_hidden[sorted_index[x]//width]
    return lock, result, score, dec_input, dec_hidden


def beam_search(code, encoder, decoder, code_voc, comment_voc, max_length_inp, max_length_targ, width):
    inputs = code_tokenize(code)
    inputs = code_to_index(inputs, code_voc, max_length_inp)
        
    hidden_h, hidden_c = tf.zeros((1, UNITS)), tf.zeros((1, UNITS))
    hidden = [hidden_h, hidden_c]
    enc_output, enc_hidden_h, enc_hidden_c = encoder(inputs, hidden)
    dec_hidden = [[enc_hidden_h, enc_hidden_c]] * width
    dec_input = [tf.expand_dims([comment_voc.index('<START>')], 1)] * width
    
    result = [''] * width
    score = [1] * width
    lock = [0] * width
    
    for t in range(max_length_targ):
        can_lock, can_score, can_result, can_input, dec_hidden = beam_search_predict_word(lock, score, result, decoder, dec_input, dec_hidden, enc_output, comment_voc, width)

        if t == 0:
            result[:width] = can_result[:width]
            score[:width] = can_score[:width]
            dec_input = [tf.expand_dims([can_input[x]], 0) for x in range(width)]
            continue
        
        lock, result, score, dec_input, dec_hidden = beam_search_generate_topk_candidate(can_score, can_result, can_lock, can_input, result, score, lock, dec_hidden, dec_input, width)
        if 0 not in lock:
            break
    return result[0]

def beam_search_bilstm(code, encoder, decoder, code_voc, comment_voc, max_length_inp, max_length_targ, width):
    inputs = code_tokenize(code)
    inputs = code_to_index(inputs, code_voc, max_length_inp)

    hidden = tf.zeros((1, UNITS))
    enc_output, enc_forward_h, enc_forward_c, enc_backward_h, enc_backward_c = encoder(inputs, hidden, hidden, hidden, hidden)
    dec_hidden = [[enc_forward_h, enc_forward_c, enc_backward_h, enc_backward_c]] * width
    dec_input = [tf.expand_dims([comment_voc.index('<START>')], 1)] * width

    result = [''] * width
    score = [1] * width
    lock = [0] * width

    for t in range(max_length_targ):
        can_lock, can_score, can_result, can_input, dec_hidden = beam_search_predict_word(lock, score, result, decoder, dec_input, dec_hidden, enc_output, comment_voc, width)
        
        if t == 0:
            result[:width] = can_result[:width]
            score[:width] = can_score[:width]
            dec_input = [tf.expand_dims([can_input[x]], 0) for x in range(width)]
            continue
        
        lock, result, score, dec_input, dec_hidden = beam_search_generate_topk_candidate(can_score, can_result, can_lock, can_input, result, score, lock, dec_hidden, dec_input, width)
        if 0 not in lock:
            break
    return result[0]

# Read the training data:
def read_pkl():
    if MODE=="normal":
        with open('./simplified_dataset/train_normal_data.pkl', 'rb') as f:
            code_train, comment_train, code_voc, comment_voc = pickle.load(f)
    elif MODE=="simple":
        with open('./simplified_dataset/train_simple_data.pkl', 'rb') as f:
            code_train, comment_train, code_voc, comment_voc = pickle.load(f)
    elif MODE=="SBT":
        with open('./simplified_dataset/train_SBT_data.pkl', 'rb') as f:
            code_train, comment_train, code_voc, comment_voc = pickle.load(f)
    
    return code_train, comment_train, code_voc, comment_voc

def read_testset(path: str):
    f = open(path)
    inputs = f.readlines()
    f.close()
    test_inputs = []
    test_outputs = []

    for pair in inputs:
        pair = json.loads(pair)
        test_inputs.append(pair['code'])
        test_outputs.append(pair['nl'])
    
    return test_inputs, test_outputs

#  bleu4 (n=4)
def bleu(true, pred, n):
    true = nltk.word_tokenize(true)
    pred = nltk.word_tokenize(pred)
    c = len(pred)
    r = len(true)
    bp = 1. if c > r else np.exp(1 - r / (c + 1e-10))
    score = 0
    
    for i in range(1, n+1):
        true_ngram = set(ngram(true, i))
        pred_ngram = ngram(pred, i)
        if len(true_ngram)==0 or len(true_ngram)==0:
            break
        length = float(len(pred_ngram)) + 1e-10
        count = sum([1. if t in true_ngram else 0. for t in pred_ngram])
        score += math.log(1e-10 + (count / length))
    score = math.exp(score / n)  #n就是公式的Wn
    bleu = bp * score
    return bleu

def getCheckpointDir():
    if MODE=="normal" and BIDIRECTIONAL==0 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-normal-256'
    elif MODE=="normal" and BIDIRECTIONAL==0 and DROPOUT==1:
        checkpoint_dir = './training_checkpoints/adam-normal-dropout-256'
    elif MODE=="simple" and BIDIRECTIONAL==0 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-simple-256'
    elif MODE=="simple" and BIDIRECTIONAL==0 and DROPOUT==1:
        checkpoint_dir = './training_checkpoints/adam-simple-dropout-256'
    elif MODE=="SBT" and BIDIRECTIONAL==0 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-SBT-256'
    elif MODE=="SBT" and BIDIRECTIONAL==0 and DROPOUT==1:
        checkpoint_dir = './training_checkpoints/adam-SBT-dropout-256'
    elif MODE=="normal" and BIDIRECTIONAL==1 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-normal-bilstm-256'
    elif MODE=="normal" and BIDIRECTIONAL==1 and DROPOUT==1:
        checkpoint_dir = './training_checkpoints/adam-normal-bilstm-dropout-256'
    elif MODE=="simple" and BIDIRECTIONAL==1 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-simple-bilstm-256'
    elif MODE=="simple" and BIDIRECTIONAL==1 and DROPOUT==1:
        checkpoint_dir = './training_checkpoints/adam-simple-bilstm-dropout-256'
    elif MODE=="SBT" and BIDIRECTIONAL==1 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-SBT-bilstm-256'
    elif MODE=="SBT" and BIDIRECTIONAL==1 and DROPOUT==0:
        checkpoint_dir = './training_checkpoints/adam-SBT-bilstm-dropout-256'
    return checkpoint_dir