from configparser import ConfigParser
from scipy import stats
import numpy as np
import csv
import os

configvals = ConfigParser()
configvals.read('config_and_info.txt', encoding='utf-8')
ttestsamplenumbs_ = [int(i) - 1 for i in configvals['Config']['columns_for_t_test'].split(",")]

print(ttestsamplenumbs_)

datafile = configvals['Config']['data_file']

with open(datafile, 'r') as infile:
    # read the file as a dictionary for each row ({header : value})
    # tempname = infile.name
    datafilename = os.path.splitext(os.path.splitext(os.path.basename(infile.name))[0])[0]
    reader = csv.DictReader(infile, delimiter='\t')
    data_pre = {
        'xval': [],
        'yval': []
    }
    x_labl_pre = []
    for row in reader:
        for header, value in row.items():
            try:
                x_labl_pre.append(header)
                data_pre['yval'].append(float(value))
            # the except leaves out empty cells from data_pre
            except ValueError:
                continue
            data_pre['xval'].append(str(header))
x_labl = list(dict.fromkeys(x_labl_pre))

databygrp = {}
for i in x_labl:
    databygrp[i] = []
for idx, grp in enumerate(data_pre['xval']):
    databygrp[grp].append(data_pre['yval'][idx])

t_stat, p_value = stats.ttest_ind(databygrp[x_labl[(ttestsamplenumbs_[0])]], databygrp[x_labl[(ttestsamplenumbs_[1])]]) 

print(p_value)

if 0.05 > p_value > 0.01:
    pasterisk = '*'
elif 0.01 > p_value > 0.001:
    pasterisk = '**'
elif 0.001 > p_value:
    pasterisk = '***'
else:
    pasterisk = ''

print(pasterisk)