from difflib import SequenceMatcher
maxx = 0
line = 'Huyện Thăng Bình, Quảng Nam'
with open('diachi.txt', 'r') as infile:
    for i in infile.readlines():
        ratio = SequenceMatcher(a=i,b=line).ratio()
        if ratio>maxx:
            maxx = ratio
            res = i
print(maxx)
print(res)