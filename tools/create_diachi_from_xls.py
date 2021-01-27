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
str_tong = []

length = len(ls_tinh)

for i in range(length):
    tinh = ls_tinh[i]
    huyen = ls_huyen[i]
    xa = ls_xa[i]
    if not isinstance(tinh, str):
        tinh = ''
    if not isinstance(huyen, str):
        huyen = ''
    else:
        huyen = huyen.replace('Huyện ', '')
        huyen = huyen.replace('Quận ', '')
        huyen = huyen.replace('Thị xã ', '')
        huyen = huyen.replace('Thành phố ', '')
    if not isinstance(xa, str):
        xa = ''
    else:
        xa = xa.replace('Xã ', '')
        xa = xa.replace('Phường ', '')
        xa = xa.replace('Thị trấn ', '')
    #obj = tinhhuyenxa(tinh, huyen, xa)
    #objs.append(obj)
    str_xht = xa+','+ huyen+','+ tinh + '\n'
    str_ht = huyen + ',' + tinh + '\n'
    str_tong.append(str_xht)
    str_tong.append(str_ht)

file_name = 'dvhcvn.xlsx'
df = pd.read_excel(file_name, sheet_name=None)

ls_tinh_0 = df['Sheet1']['Tỉnh Thành Phố']
ls_huyen_0 = df['Sheet1']['Quận Huyện']
ls_xa_0 = df['Sheet1']['Phường Xã']

objs_0 = []

length = len(ls_tinh_0)
pre_huyen = ''
with open('diachi_diff.txt', 'w') as out2:
    for i in range(length):
        tinh = ls_tinh_0[i]
        huyen = ls_huyen_0[i]
        xa = ls_xa_0[i]
        
        if not isinstance(tinh, str):
            tinh = ''
        if not isinstance(huyen, str):
            huyen = '' 
        else:
            huyen1 = huyen.replace('Huyện ', '')
            huyen1 = huyen1.replace('Quận ', '')
            huyen1 = huyen1.replace('Thị xã ', '')
            huyen1 = huyen1.replace('Thành phố ', '')
        if not isinstance(xa, str):
            xa = ''
        else:
            xa1 = xa.replace('Xã ', '')
            xa1 = xa1.replace('Phường ', '')
            xa1 = xa1.replace('Thị trấn ', '')
        #obj = tinhhuyenxa(tinh, huyen, xa)
        str_xht1 = xa1+','+ huyen1+','+ tinh + '\n'
        str_xht = xa+','+ huyen+','+ tinh + '\n'
        str_ht1 = huyen1 + ',' + tinh + '\n'
        str_ht = huyen + ',' + tinh + '\n'
        if str_xht1 not in str_tong:
            out2.write(str_xht)
        
        if pre_huyen != huyen:
            if str_ht1 not in str_tong:
                out2.write(str_ht)

        pre_huyen = huyen
        pre_tinh = tinh
    #objs_0.append(obj)

# pre_huyen = ''
# pre_tinh = ''

# with open('diachi.txt', 'w') as out2:
#     for obj in objs:
#         if not isinstance(obj.tinh, str):
#             obj.tinh = ''
#         if not isinstance(obj.huyen, str):
#             obj.huyen = ''
#         if not isinstance(obj.xa, str):
#             obj.xa = ''

#         print(obj.xa, ' ', obj.huyen,' ',obj.tinh)
#         str1 = obj.xa+','+ obj.huyen+','+obj.tinh + '\n'
#         out.write(str1)
        
#         if obj.huyen != pre_huyen:
#             str2 = obj.huyen + ',' + obj.tinh + '\n'
#             out.write(str2)
#         if obj.tinh != pre_tinh:
#             str3 = obj.tinh + '\n'
#             out.write(str3)       
        
#         pre_huyen = obj.huyen
#         pre_tinh = obj.tinh
# out.close()


