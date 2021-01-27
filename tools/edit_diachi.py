
with open('diachi_diff.txt', 'r') as infile:
    with open('test_diachi.txt', 'w') as outfile:
        for i in infile.readlines():
            #outfile.write(i)
            #x = i
            y = i
            if i.find('Phường ') != -1:
                #x = x.replace('Phường ', 'P.')
                pos1 = i.find('Phường ')
                pos2 = i[pos1:].find(',')

                mark = False
                for j in range(10):
                    if i[pos1:pos2+1].find(str(j)) != -1:
                        mark =True
                if mark:
                    y = y.replace('Phường ', 'P.')
                else:
                    y = y.replace('Phường ', '')

            if i.find('Xã ') != -1:
                pos1 = i.find('Xã ')
                pos2 = i[pos1:].find(',')
                
                mark = False
                for j in range(10):
                    if i[pos1:pos2+1].find(str(j)) != -1:
                        mark =True
                if mark:
                    y = y.replace('Xã ', 'X.')
                else:
                #x = x.replace('Xã ', 'X.')
                    y = y.replace('Xã ', '')            
            #outfile.write(x)
            if i.find('Quận ') != -1:
                pos1 = i.find('Quận ')
                pos2 = i[pos1:].find(',')
                print(pos1,' ', pos2)
                print(i[pos1:pos2])
                mark = False
                for j in range(10):
                    if i[pos1:pos1+pos2+1].find(str(j)) != -1:
                        mark =True
                if mark:
                    y = y.replace('Quận ', 'Q.')
                else:
                    y = y.replace('Quận ', '')

            if i.find('Huyện ') != -1:
                pos1 = i.find('Huyện ')
                pos2 = i[pos1:].find(',')
                
                mark = False
                for j in range(10):
                    if i[pos1:pos1+pos2+1].find(str(j)) != -1:
                        mark =True
                if mark:
                    y = y.replace('Huyện ', 'H.')
                else:
                    y = y.replace('Huyện ', '')

            if i.find('Thành phố') != -1:
                y = y.replace('Thành phố', 'TP')
            if i.find('Thị trấn') != -1:
                outfile.write(y)
                y = y.replace('Thị trấn', 'TT')                
            if i.find('Thị Trấn') != -1:
                outfile.write(y)
                y = y.replace('Thị Trấn', 'TT')
            if i.find('Thị xã') != -1:
                outfile.write(y)
                y = y.replace('Thị xã', 'TX') 
            if i.find('Tỉnh') != -1:
                y = y.replace('Tỉnh', '')
                #y = y.replace('Tỉnh', '')        
            #outfile.write(x)
            outfile.write(y)

infile.close()
outfile.close()
