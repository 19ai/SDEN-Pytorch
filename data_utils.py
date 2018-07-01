import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim
from torch.autograd import Variable
import numpy as np
from konlpy.tag import Mecab
from copy import deepcopy
import random
tagger = Mecab()
flatten = lambda l: [item for sublist in l for item in sublist]


def prepare_sequence(seq, to_index):
    idxs = list(map(lambda w: to_index[w] if to_index.get(w) is not None else to_index["<unk>"], seq))
    return torch.LongTensor(idxs)

def data_loader(train_data,batch_size,shuffle=False):
    if shuffle: random.shuffle(train_data)
    sindex = 0
    eindex = batch_size
    while eindex < len(train_data):
        batch = train_data[sindex: eindex]
        temp = eindex
        eindex = eindex + batch_size
        sindex = temp
        yield batch
    
    if eindex >= len(train_data):
        batch = train_data[sindex:]
        yield batch

def pad_to_batch(batch, w_to_ix,s_to_ix): # for bAbI dataset
    history,current,slot,intent = list(zip(*batch))
    max_history = max([len(h) for h in history])
    max_len = max([h.size(1) for h in flatten(history)])
    max_current = max([c.size(1) for c in current])
    max_slot = max([s.size(1) for s in slot])
    
    historys, currents, slots = [], [], []
    for i in range(len(batch)):
        history_p_t = []
        for j in range(len(history[i])):
            if history[i][j].size(1) < max_len:
                history_p_t.append(torch.cat([history[i][j], torch.LongTensor([w_to_ix['<pad>']] * (max_len - history[i][j].size(1))).view(1, -1)], 1))
            else:
                history_p_t.append(history[i][j])

        while len(history_p_t) < max_history:
            history_p_t.append(torch.LongTensor([w_to_ix['<pad>']] * max_len).view(1, -1))

        history_p_t = torch.cat(history_p_t)
        historys.append(history_p_t)

        if current[i].size(1) < max_current:
            currents.append(torch.cat([current[i], Variable(torch.LongTensor([w_to_ix['<pad>']] * (max_current - current[i].size(1)))).view(1, -1)], 1))
        else:
            currents.append(current[i])

        if slot[i].size(1) < max_slot:
            slots.append(torch.cat([slot[i], torch.LongTensor([s_to_ix['<pad>']] * (max_slot - slot[i].size(1))).view(1, -1)], 1))
        else:
            slots.append(slot[i])

    currents = torch.cat(currents)
    slots = torch.cat(slots)
    intents = torch.cat(intent)
    
    return historys, currents, slots, intents

def pad_to_history(history, x_to_ix): # this is for inference
    
    max_x = max([s.size(1) for s in history])
    x_p = []
    for i in range(len(history)):
        if history[i].size(1) < max_x:
            x_p.append(torch.cat([history[i],torch.LongTensor([x_to_ix['<pad>']] * (max_x - history[i].size(1))).view(1, -1)], 1))
        else:
            x_p.append(history[i])
        
    history = torch.cat(x_p)
    return [history]