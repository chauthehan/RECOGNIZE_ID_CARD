from io import StringIO
from os import lstat
from pandas import read_csv
import pandas as pd 

class tinhhuyenxa:
    def __init__(self, tinh, huyen, xa):
        self.tinh = tinh 
        self.huyen = huyen
        self.xa = xa

file_name = 'danhsachtinhhuyenxa.xlsx'
df = pd.read_excel(file_name, sheet_name=None)

ls_tinh = df['Sheet1']['Tỉnh Thành Phố']
ls_huyen = df['Sheet1']['Quận Huyện']
ls_xa = df['Sheet1']['Phường Xã']

objs = []

length = len(ls_tinh)


for i in range(length):
    tinh = ls_tinh[i]
    huyen = ls_huyen[i]
    xa = ls_xa[i]
    obj = tinhhuyenxa(tinh, huyen, xa)
    objs.append(obj)

pre_huyen = ''
pre_tinh = ''
with open('diachi.txt', 'w') as out:
    for obj in objs:
        if not isinstance(obj.tinh, str):
            obj.tinh = ''
        if not isinstance(obj.huyen, str):
            obj.huyen = ''
        if not isinstance(obj.xa, str):
            obj.xa = ''

        print(obj.xa, ' ', obj.huyen,' ',obj.tinh)
        str1 = obj.xa+','+ obj.huyen+','+obj.tinh + '\n'
        out.write(str1)
        
        if obj.huyen != pre_huyen:
            str2 = obj.huyen + ',' + obj.tinh + '\n'
            out.write(str2)
        if obj.tinh != pre_tinh:
            str3 = obj.tinh + '\n'
            out.write(str3)
        
        pre_huyen = obj.huyen
        pre_tinh = obj.tinh
out.close()


