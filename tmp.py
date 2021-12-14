# -*- coding: utf-8 -*-
import os

path = "./cluster_tables"
list_name = []
new = []

for file in os.listdir(path):
    file_path = os.path.join(path, file)
    if os.path.splitext(file_path)[1] == '.json':
        list_name.append(file_path)
for name in list_name:
    name = name.split('/')[2].split('_')[0]
    new.append(name)
# print(list_name)
print(new)
