from data_reader import DataReader
from co_graph import CoGraph
import numpy as np
import cluster_merge as cm
from log import output
from scipy.stats import entropy

# preprocess data, tune threshold parameter to adjust data size
rd = DataReader()
rd.pre_process_cell(threshold=1850, original=True)
rd.pre_process_gene(threshold=2600, original=False)

# build graph by using hypergeometry test. then use jaccard to filter the
# graph. pass parameter to adjust graph.
g = CoGraph(rd.get_gene_data())
output('data shape after preprocessing ', g.data.shape)
g.build_graph(threshold=0.001, jaccard=True, jaccard_threshold=0.5)

# find community by louvain algorithm
g.find_partition()

# get gene clusters and merge gene in same clusters
cm = cm.Cluster(g.data, g.parts)
cm.merge()

# cell type clustering. build graph by using euclidean distance measurement
g2 = CoGraph(cm.parts)
output('data shape after gene clustering ', g2.data.shape)
g2.build_graph(threshold=1.0, jaccard=True, jaccard_threshold=0.8, mode='euclidean')

# find cell type clusters
g2.find_partition(weight=True, mode='euclidean')
output('cell type clusters', g2.parts)

with open('../data/result.txt') as f:
    data = f.readlines()
    cluster = [(x.strip()).split()[1] for x in data]

# count # in a matrix format
count = 0
re = np.zeros((39, len(g2.parts)))
col = 0
for part in g2.parts:
    for num in part:
        index = rd.cell_lookup[num]
        if index > len(cluster):
            count += 1
            continue
        row = int(cluster[index])
        re[row - 1][col] += 1
    col += 1

output('cell type result', re)
output('unclustered data in original dataset', count)

avg_ent = 0
avg_ent_flip = 0

# discard clusters with less than 20 cells
result = []
for arr in re.transpose():
    if np.sum(arr) > 20:
        result.append(arr)

# print out clusters result
result_str = ''
for arr in result:
    for ele in arr:
        result_str += '{:^5}'.format(str(int(ele)))
    result_str += '\n'
output('after result', result_str)

# calculate generate cluster entropy
ent = []
for arr in result:
    ent.append(entropy(arr))

ent_str = ''
for val in ent:
    avg_ent += val
    ent_str += str(val) + '\n'
avg_ent /= len(ent)
output('entropy', ent_str)

# calculate sample data cluster entropy
flip = np.array(result).transpose()
result_str = ''
for arr in flip:
    for ele in arr:
        result_str += '{:^5}'.format(str(int(ele)))
    result_str += '\n'
output('after result', result_str)

ent = []
for arr in flip:
    ent.append(entropy(arr))

ent_str = ''
for val in ent:
    avg_ent_flip += val
    ent_str += str(val) + '\n'
output('flip entropy', ent_str)
avg_ent_flip /= len(ent)

ent_result = 'average: {}, average: {}'.format(avg_ent, avg_ent_flip)
output('entropy score', ent_result)
