import os
images = os.listdir('test')
with open('infor.txt', 'w') as out:
    for image in images:
        str_out = 'Anh: '+'\n'
        str_out += 'Ten:\nSo:\nNgay sinh:\nNguyen quan:\nDia chi:\nGioi tinh:\nHet han:\n\n'
        out.write(str_out)
out.close()
