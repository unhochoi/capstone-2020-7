#!/usr/bin/env python
# -*- coding: utf-8 -*-

import time
import csv

header = ['_id', 'accidentType', 'analyResult', 'atdate', 'attackType',
       'autoEmailSendFlag', 'autoFlag', 'batchID', 'destinationIP',
       'destinationPort', 'detailResult', 'detectEnd', 'detectName',
       'detectStart', 'directionType', 'doubtFlag', 'etcInfo', 'eventCount',
       'eventType', 'jumboPayloadFlag', 'metaType', 'orgIDX', 'packetSize',
       'payload', 'protocol', 'sourceIP', 'sourcePort', 'stdrPort', 'uid',
       'vfnStatus', 'vfnUpdate', 'accidentProcessFlag']


def data_loader(LOG_DATA_PATH = "./20181201000000.pkl"):
    import pandas as pd
    data = pd.read_pickle(LOG_DATA_PATH)
    return data


def grouped_data(
    data, GROUPED_KEY = 'orgIDX', SORT_KEY = "atdate", 
    UNIQUE_ID = '_id'
):    # data type is pandas' DataFrame
    g = data.groupby(GROUPED_KEY)
    g_keys = list(data[GROUPED_KEY].unique())
    output = {"payload":[], "id":[]}
    for key in g_keys:
        temp = g.get_group(key)
        temp = temp.sort_values(SORT_KEY)
        output['payload'].append(list(temp['payload']))
        output['id'].append(list(temp[UNIQUE_ID]))
    return output


def get_model(WEIGHT_PATH="./model_weight.h5"):
    from now_pre_model import now_pre_RedDNN
    model = now_pre_RedDNN()
    model.load_weights(WEIGHT_PATH)
    model.compile(loss='binary_crossentropy', optimizer='adam')
    return model


def preprocessing(data):
    from now_pre_model import preprocessing_payload
    output = {'pre':[], 'now':[], 'id':[]}
    for payloads, ids in zip(data['payload'], data['id']):
        pre, now = preprocessing_payload(payloads)
        output['pre'].extend(pre)
        output['now'].extend(now)
        output['id'].extend(ids)
    return output


def concatenate_pred_table(pred, table):
    for _id in pred.keys():
        table[_id]['label'] = pred[_id]


def labeling(data, predicts, THRESH_HOLD = 0.5):
    output = {}
    for predict, _id in zip(predicts, data['id']):
        if predict > THRESH_HOLD:
            output[_id] = 1
        else:
            output[_id] = 0
    return output


def make_id_table(data):
    _id_table = {}
    _type = type(data)
    if  _type == list:
        for d in data:
            temp = {}
            _id = d["_id"]
            for key in d.keys():
                if key != "_id":
                    temp[key] = d[key]
            _id_table[_id] = temp
    return _id_table



def head_table(table, n=5):
    for key in list(table)[:n]:
        print(table[key])


def run(
    LOG_DATA_PATH = "./20181201000000.pkl", GROUPED_KEY = 'orgIDX', 
    SORT_KEY = "atdate", UNIQUE_ID = '_id', THRESH_HOLD = 0.5
):
    """
    input : data type of input is pandas's DataFrame
    output : data type of output is dict
    params : 
    - GROUPED_KEY : organize index, type is str, int
    - SORT_KEY    : datetime
    - UNIQUE_ID   : unique_value of logs
    """
    import numpy as np
    import pandas as pd
    data = data_loader(LOG_DATA_PATH=LOG_DATA_PATH)
    _id_table = make_id_table(data)
    data = pd.DataFrame(data)
    data = grouped_data(data=data)
    data = preprocessing(data=data)
    model = get_model()
    pred = model.predict({"pre_pay": np.array(data['pre']),
                          "now_pay": np.array(data['now'])}, verbose=True)
    pred = labeling(data, pred)
    concatenate_pred_table(pred, _id_table)
    
    return _id_table


def first_process():
    import numpy as np
    import pandas as pd
    data = data_loader(LOG_DATA_PATH=LOG_DATA_PATH)
    _id_table = make_id_table(data)
    data = pd.DataFrame(data)


def fixing(data):
  output = {}
  if len(data) == 32:
    for h, d in zip(header, data):
      output[h] = d
  return output



# 핸들러
def process_line(data):
  import pandas as pd
  import numpy as np

  _id_table = make_id_table(data)
  data = pd.DataFrame(data)
  data = grouped_data(data=data)
  data = preprocessing(data=data)
  global model
  pred = model.predict({"pre_pay": np.array(data['pre']),
                      "now_pay": np.array(data['now'])}, verbose=True)
  pred = labeling(data, pred)
  concatenate_pred_table(pred, _id_table)
  output = pd.DataFrame(_id_table).T
  output.to_csv("./livetest222.csv", mode="a", index=False, header=False)  



model = get_model()




with open('./logdata.log', 'r') as fr:
  data = []
  while True:
    line = fr.readline()
    if not line:
      time.sleep(10)
      continue
    if line != "":
      if line[-1] == '\n':
        line = line[:-1]
      temp = line.split("`")
      if len(temp) > 32:
        continue
      temp = fixing(temp)
      if temp['payload'] not in ("", None, "nan"):
        data.append(temp)
    if len(data) > 10:
      process_line(data)
      data = []


