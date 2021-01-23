from tools.utils import *
from difflib import SequenceMatcher

def find_name_text(list_text_box2, obj_id, birth_box):
    # if the box has more than 2 consecutive upper character, than it must be the box name
    
    dic_name = {}
    #bottom = 0
    #print('OBJID', obj_id.key)
    
    for obj in list_text_box2:

        if obj.two_points[1] < birth_box[1] and obj.two_points[1] > obj_id.two_points[1]:
            
            key_no_accent = remove_accent(obj.key)
            #print('name', obj.key)
            if key_no_accent == '':
                continue
            else:
                count = count_upper_consecutive(key_no_accent)
            if count >= 2:
                dic_name[obj.key] = obj.two_points
    #print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
    else:
        #name appears on 2 lines
        name = lst_name[1] + ' ' + lst_name[0]
    
    pos = -1
    name_no_accent = remove_accent(name)
    #print('NAME', name_no_accent)
    for j, i in enumerate(name_no_accent):
        if not ((i>='A' and i<='Y') or i == ' ' or i=='-'):
            pos = j
    
    key_name = name[pos+1:]
    
    #delete space at first position
    while True:
        if key_name.find(' ') == 0:
            key_name = key_name[1:]
        else:
            break
    #print(key_name)
    if key_name.find('-') != -1:
        pos1 = key_name.find('-')
    else:
        pos1 = key_name.find(' ')
    Ho = key_name[:pos1]
    Ho = remove_accent(Ho)
    #Ho = str.upper(Ho)
    #print('HO', Ho)
    with open('ho.txt', 'r') as f:
        maxx = 0
        for i in f.readlines():
            name = remove_accent(i)
            name = str.upper(name)
            ratio = SequenceMatcher(a=Ho, b=name).ratio()
            if ratio > maxx:
                maxx = ratio
                res = i
    f.close()

    res = str.upper(res)

    pos2 = key_name[pos1+1:].find(' ')
    #print(key_name[pos1+1:])
    #print(pos2)
    #print('LOT',key_name[pos1+1:][:pos2])
    if key_name[pos1+1:][:pos2] == 'THI':
        lot = 'THỊ'    
        key_name = res[:-1] + ' ' + lot + key_name[pos1+1:][pos2+1:]
    else:
        key_name = res[:-1] + ' ' + key_name[pos1+1:]
    
    key_name = key_name.replace('-', ' ')

    return key_name

def find_id_text(list_text_box2):
    bot = 9999
    key_so = ''
    key_id = ''
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
        if obj.two_points[1]<bot and key_no_accent.find('so') == 0:
            bot = obj.two_points[1]
            obj_id = obj
            key_so = key
  
    dic_num = {}
    for obj in list_text_box2:
        key = obj.key
        count = count_num_in_key(key)
        if count >=4:
            dic_num[key] = obj
    
    if key_so == '':
        for key in dic_num:
            count = count_num_in_key(key)
            if count >= 9:
                key_id = key
                obj_id = dic_num[key]

        key_id = remove_char(key_id)

        if len(key_id) >= 9:
            key_id = key_id[-9:]

    else:
        dis = 9999
        for key in dic_num:
            if abs(dic_num[key].two_points[1]-obj_id.two_points[1]) < dis:
                dis = abs(dic_num[key].two_points[1]-obj_id.two_points[1])
                key_id = key

    key_id = remove_char(key_id)
    if len(key_id)>9:
        key_id = key_id[-9:]
    
    return key_id, obj_id

def find_id_text_cc(list_text_box2):
    bot = 9999
    key_so = ''
    key_id = ''
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
        if obj.two_points[1]<bot and key_no_accent.find('so') == 0:
            bot = obj.two_points[1]
            obj_id = obj
            key_so = key
  
    dic_num = {}
    for obj in list_text_box2:
        key = obj.key
        count = count_num_in_key(key)
        if count >=4:
            dic_num[key] = obj

    if key_so == '':
        for key in dic_num:
            count = count_num_in_key(key)
            if count >= 12:
                key_id = key
                obj_id = dic_num[key]

        key_id = remove_char(key_id)

        if len(key_id) == 13:
            key_id = key_id[:-1]
        if len(key_id) == 14:
            key_id = key_id[2:]
        if len(key_id) == 15:
            key_id = key_id[2:][:-1] 
            
    else:
        if len(remove_char(key_so))>=4:
            key_id = key_so
        else:
            dis = 9999
            for key in dic_num:
                if abs(dic_num[key].two_points[1]-obj_id.two_points[1]) < dis:
                    dis = abs(dic_num[key].two_points[1]-obj_id.two_points[1])
                    key_id = key
        key_id = remove_char(key_id)
        if len(key_id)>12:
            key_id = key_id[:12]

 
    return key_id, obj_id

def find_birth_text(list_text_box2, obj_id):
    birth_size = 0
    key_birth = ''
    #birth_box = []
    for obj in list_text_box2:
        if obj != obj_id:
            key = obj.key
            #print(key)
            count = count_num_in_key(key)
            if count == 8 and key.find('-')!=-1: #and check:
                # get the birth box
                obj_birth = obj
                key_birth = process_birth(key)
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size

            if (key[:2]=='19' and count==4):
                obj_birth = obj
                k = remove_accent(key)
                k = remove_char_birth(k)
                key_birth = key
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size*2

            if (count == 7 or count ==6) and key.find('-')!=-1:
                obj_birth = obj
                k = remove_accent(key)
                k = remove_char_birth(k)
                key_birth = k
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size
    
    key_no_accent = remove_accent(obj_birth.key)
    count = count_char_in_key(key_no_accent)                
    if count > 5:
        birth_size = birth_size*2/3
    return key_birth, birth_size, birth_box

def remove_wrong_box(list_text_box2, obj_id, birth_box, birth_size):
    #print('before ', len(list_text_box2))
    list_obj_remove = []
    for obj in list_text_box2:
        if obj.size < int(birth_size/2.15):
            #print('111111')
            list_obj_remove.append(obj)
        
        length_birthbox = birth_box[2]-birth_box[0]
        if obj.two_points[0] < obj_id.two_points[0] - length_birthbox and obj.two_points[2] - obj.two_points[0] < length_birthbox:
            #print('222222')
            list_obj_remove.append(obj)
    
    #print(list_obj_remove)
    
    set_remove = set(list_obj_remove)
    list_obj_remove = list(set_remove)
    
    #print('REMOVE', list_key_remove)
    for obj in list_obj_remove:
        if obj.key == '':
            continue
        else:
            score = score_nguyenquan(remove_accent(obj.key))
            if score < 15:
                print('ROMOVE ', obj.key)
                list_text_box2.remove(obj)
    
    #print('AFTER ', len(list_text_box2))
    print('-------------')
    return list_text_box2

def delete_box_processed(list_text_box2, birth_box):
    list_obj_remove = []

    for obj in list_text_box2:
        if obj.two_points[1] <= birth_box[1] or obj.key=='':
            list_obj_remove.append(obj)  

    for obj in list_obj_remove:
        list_text_box2.remove(obj)
    

    return list_text_box2

def find_hometown_address_text(list_text_box2):
    hometown = ''
    nguyenquan = ''
    address = ''
    keys_above_dkhk = []

    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
    
        if score_nguyenquan(key_no_accent)>maxx:
            maxx = score_nguyenquan(key_no_accent)               
            nguyenquan = key
            box_nguyenquan = obj.two_points
            obj_nguyenquan = obj

    # delete box left of nguyenquan
    remove_obj = []
    for obj in list_text_box2:
        #print(obj.key,' ',obj.two_points)
        if obj.two_points[2] < box_nguyenquan[0]:
            
            remove_obj.append(obj)   

    if remove_obj != []:
        for obj in remove_obj:
            list_text_box2.remove(obj)      

    # remove box 'sinh ngay'
    sinhngay = None
    for obj in list_text_box2:
        key = obj.key
        if obj.two_points[2] > box_nguyenquan[0] and obj.two_points[2]<box_nguyenquan[2] and obj.two_points[1]<box_nguyenquan[1]:
            sinhngay = obj
    
    if sinhngay is not None:
        #print('SINHNGAY', sinhngay.key)
        list_text_box2.remove(sinhngay)

    maxx = 0

    for obj in list_text_box2:
        key = obj.key
        # if box has at least 3 word in Noi DKHK thuong tru, 
        # than it must be address box
        key_no_accent = remove_accent(key)            
        if score_dkhk(key_no_accent)>maxx:                
            maxx = score_dkhk(key_no_accent)
            obj_dkhk = obj

    obj_nearest_hometown = None

    nguyenquan2 = ''
    if len(nguyenquan[12:]) > 3: 
        nguyenquan2 = nguyenquan[12:]
        #nearest_hometown = nguyenquan
    else:
        obj_nearest_hometown = box_nearest(obj_nguyenquan, list_text_box2)
        nguyenquan2 = obj_nearest_hometown.key
    
    #print('nearesthometown', nearest_hometown)
    #print('nguyeqnan', obj_nguyenquan.key)
    #print('nearest', nguyenquan2)

    hometown = hometown + nguyenquan2
    #print('HOMETONW', hometown)
    if obj_nearest_hometown is not None:
        list_text_box2.remove(obj_nearest_hometown)
    if nguyenquan2 != obj_nguyenquan.key:
        list_text_box2.remove(obj_nguyenquan)
    
    #print('20: ', dkhk[20:])
    dkhk = obj_dkhk.key
    nearest_address_raw = ''
    if len(dkhk[20:]) > 2:
        
        nearest_address = dkhk[20:]
        nearest_address_raw = dkhk
        obj_nearest_address_raw = obj_dkhk
    else:
        obj_nearest_address_raw = box_nearest(obj_dkhk, list_text_box2)
        nearest_address = obj_nearest_address_raw.key
        nearest_address_raw = nearest_address
    
    address = address + nearest_address


    #print('nearest address raw', nearest_address_raw)
    for obj in list_text_box2:
        if obj.two_points[1]<obj_dkhk.two_points[1] and obj.key != nearest_address_raw:
            keys_above_dkhk.append(obj)

    if len(keys_above_dkhk) != 0:
        hometown2 = sort_key_left2right(keys_above_dkhk)

        #print('After sort', hometown2)
        hometown = hometown + ' '+hometown2
            
    for obj in keys_above_dkhk:
        list_text_box2.remove(obj)
    list_text_box2.remove(obj_nearest_address_raw)

    if nearest_address_raw != dkhk:
        list_text_box2.remove(obj_dkhk)

    print('-----------------------')
    
    #print('LISTTESTBOX2')
    #for i in list_text_box2:
        #print(i.key)
    if len(list_text_box2) != 0:
        address2 = sort_key_left2right(list_text_box2)
        address = address + ' ' + address2

    hometown = change_PhuongQuan_to_PQ(hometown)
    address = change_PhuongQuan_to_PQ(address)

    print('Hometown', hometown)
    print('Address', address)

    hometown1 = mapping(hometown)
    address1 = mapping(address)

    # check whether it's Ho Chi Minh region
    pos = 0
    if hometown1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(hometown)-1):
            if (hometown[i]=='P' and hometown[i+1] in '0123456789') or (hometown[i]=='P' and hometown[i+2] in '0123456789'):
                pos = i
                #print(pos)
        hometown = hometown[pos:]
    if pos != 0:
        hometown1 = mapping(hometown)    
    pos = 0
    if address1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(address)-1):
            if (address[i]=='P' and address[i+1] in '0123456789') or (address[i]=='P' and address[i+2] in '0123456789'):
                pos = i
                #print(pos)
        address = address[pos:]
    
    if pos != 0:
        address1 = mapping(address)

    #print('homewon1', hometown)
    #print('address1', address)  

    return hometown1, address1

def find_box_Quoctich_Dantoc(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key = remove_accent(key)
        score = score_Quoctich_Dantoc(key)
        #print(obj.key, ' ',score)
        if score > maxx:
            maxx = score
            obj_Quoctich = obj 

    return obj_Quoctich

def find_birth_text_cc(list_text_box2, obj_quoctich):
    key_birth = ''
    obj_birth = None
    for obj in list_text_box2:
        if obj.two_points[1] < obj_quoctich.two_points[1]:
            key = obj.key
            count = count_num_in_key(key)

            if count == 8:
                key_birth = remove_char(key)
                key_birth = process_birth(key_birth)
                obj_birth = obj
    return key_birth, obj_birth

def find_cogiatriden(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        text = obj.key
        text_no_accent = remove_accent(text)
        score = score_expired(text_no_accent)
        if score>maxx:
            maxx = score
            obj_ex = obj
    return obj_ex

def find_name_text_cc(list_text_box2, obj_quoctich, obj_id):
    # if the box has more than 2 consecutive upper character, than it must be the box name
    
    dic_name = {}
    #bottom = 0
    for obj in list_text_box2:
        if obj.two_points[1] < obj_quoctich.two_points[1] and obj.two_points[1] > obj_id.two_points[1]:
            
            key_no_accent = remove_accent(obj.key)
            #print('name', obj.key)
            if key_no_accent == '':
                continue
            else:
                count = count_upper_consecutive(key_no_accent)
            if count >= 2:
                dic_name[obj.key] = obj.two_points
    #print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
    else:
        #name appears on 2 lines
        name = lst_name[1] + ' ' + lst_name[0]

    pos = -1
    name_no_accent = remove_accent(name)
    #print('NAME', name_no_accent)
    for j, i in enumerate(name_no_accent):
        if i>='a' and i<='y':
            pos = j
            
    key_name = name[pos+1:]

    pos1 = key_name.find(' ')
    Ho = key_name[:pos1]
    Ho = remove_accent(Ho)
    #Ho = str.upper(Ho)

    with open('ho.txt', 'r') as f:
        maxx = 0
        for i in f.readlines():
            name = remove_accent(i)
            name = str.upper(name)
            ratio = SequenceMatcher(a=Ho, b=name).ratio()
            if ratio > maxx:
                maxx = ratio
                res = i
    f.close()
    
    res = str.upper(res)
    key_name = res[:-1] + key_name[pos1:]
    
    return key_name 
        
def find_key_expired(list_text_box2, obj_birth):
    for obj in list_text_box2:
        if obj.two_points[1] > obj_birth.two_points[1]:
            key = obj.key
            count = count_num_in_key(key)

            if count == 8:
                key_ex = remove_char(key)
                key_ex = process_birth(key_ex)
                obj_ex = obj
    return key_ex, obj_ex

def find_sex(list_text_box2):
    maxx = 0
    obj_nam_or_nu = None
    obj_Gioitinh = None
    sex = ''
    for obj in list_text_box2:
        key = obj.key
        #print(key,' ', score_Gioitinh(key))
        key = remove_accent(key)
        if score_Gioitinh(key) > maxx:
            maxx = score_Gioitinh(key)
            obj_Gioitinh = obj

    #print('GIOI TINH', obj_Gioitinh.key)    
    key_no_accent = remove_accent(obj_Gioitinh.key)
    
    if key_no_accent.find('Nam') != -1:
        return 'Nam', obj_Gioitinh, obj_nam_or_nu
    elif key_no_accent.find('Nu') != -1:
        return 'Nữ', obj_Gioitinh, obj_nam_or_nu
    elif box_nearest_gioitinh_cc(obj_Gioitinh, list_text_box2) is not None:
        obj_nam_or_nu = box_nearest_gioitinh_cc(obj_Gioitinh, list_text_box2)
        key = obj_nam_or_nu.key
        key_no_accent = remove_accent(key)
        if key_no_accent == 'Nam':
            sex = 'Nam'
        elif key_no_accent == 'Nu':
            sex= 'Nữ'
        return sex, obj_Gioitinh, obj_nam_or_nu
    else:
        for obj in list_text_box2:
            key = obj.key
            key = remove_accent(key)
            if key.find('Nam') != -1 and key.find('Viet Nam') == -1:
                sex = 'Nam'
        if sex == '':
            sex = 'Nữ'      
            
        return sex, obj_Gioitinh, obj_nam_or_nu

def delete_box_processed_cc(list_text_box2, obj_Gioitinh, obj_nam_or_nu, obj_quoctich_dantoc, obj_expired, obj_birth, type_cut):
    if type_cut != 2:
        obj_cogiatriden = find_cogiatriden(list_text_box2)
        list_text_box2.remove(obj_cogiatriden)
        if obj_expired in list_text_box2:
            list_text_box2.remove(obj_expired)
    else:
        if obj_expired in list_text_box2:
            list_text_box2.remove(obj_expired)
    maxx = 0
    
    if obj_nam_or_nu is not None:
        list_text_box2.remove(obj_nam_or_nu)
    
    #print('QUOCTICH', obj_quoctich_dantoc)
    VietNamdantoc = find_VietNam_dantoc(list_text_box2, obj_quoctich_dantoc)
    
    if VietNamdantoc is not None:
        list_text_box2.remove(VietNamdantoc)
    
    if obj_quoctich_dantoc in list_text_box2:
        list_text_box2.remove(obj_quoctich_dantoc)
    
    if obj_Gioitinh in list_text_box2:
        list_text_box2.remove(obj_Gioitinh)

    list_obj_remove = []
    for obj in list_text_box2:        
        if obj.two_points[1] <= obj_birth.two_points[3]:
            
            list_obj_remove.append(obj)

    for obj in list_obj_remove:
        #print('listremove', obj.key)
        if obj in list_text_box2:
            list_text_box2.remove(obj)
    
    return list_text_box2

def find_VietNam_dantoc(list_text_box2, obj_quoctich_dantoc):
    key = obj_quoctich_dantoc.key

    ratio1 = SequenceMatcher(a=key, b='Quốc tịch').ratio()
    ratio2 = SequenceMatcher(a=key, b='Dân tộc').ratio()

    if ratio1>ratio2:
        if len(key) < 12:
            for obj in list_text_box2:
                if obj.two_points[0] > obj_quoctich_dantoc.two_points[2]:
                    return obj
        else:
            return None
    else:
        if len(key) < 10:
            for obj in list_text_box2:
                if obj.two_points[0] > obj_quoctich_dantoc.two_points[2]:
                    return obj
        else:
            return None

            
    
def find_hometown_address_text_cc(list_text_box2):
    hometown = ''
    quequan = ''
    address = ''
    keys_above_noithuongtru = []

    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)

        print(key,' ', score_Quequan(key_no_accent))
    
        if score_Quequan(key_no_accent)>maxx:
            maxx = score_Quequan(key_no_accent) 
                      
            quequan = key
            box_quequan = obj.two_points
            obj_quequan = obj
    #print('NGUYENQUAN', nguyenquan)
    #print('KEY QYE QUAN', obj_quequan.key)

    # delete box left of nguyenquan
    remove_obj = []
    for obj in list_text_box2:
        #print(obj.key,' ',obj.two_points)
        if obj.two_points[2] < box_quequan[0]:
            
            remove_obj.append(obj)   

    if remove_obj != []:
        for obj in remove_obj:
            list_text_box2.remove(obj)      

    maxx = 0

    for obj in list_text_box2:
        key = obj.key
        # if box has at least 3 word in Noi DKHK thuong tru, 
        # than it must be address box
        key_no_accent = remove_accent(key)            
        if score_Noithuongtru(key_no_accent)>maxx:                
            maxx = score_Noithuongtru(key_no_accent)
            obj_Noithuongtru = obj

    obj_nearest_hometown = None

    quequan2 = ''
    if len(quequan[12:]) > 3: 
        quequan2 = quequan[9:]
        #nearest_hometown = quequan
    else:
        obj_nearest_hometown = box_nearest(obj_quequan, list_text_box2)
        quequan2 = obj_nearest_hometown.key
    
    #print('nearesthometown', nearest_hometown)
    #print('nguyeqnan', obj_quequan.key)

    hometown = hometown + quequan2
    #print('HOMETONW', hometown)
    if obj_nearest_hometown is not None:
        list_text_box2.remove(obj_nearest_hometown)
    if quequan2 != obj_quequan.key:
        list_text_box2.remove(obj_quequan)
    
    #print('20: ', dkhk[20:])
    noithuongtru = obj_Noithuongtru.key
    nearest_address_raw = ''
    if len(noithuongtru[15:]) > 2:
        
        nearest_address = noithuongtru[15:]
        nearest_address_raw = noithuongtru
        obj_nearest_address_raw = obj_Noithuongtru
    else:
        obj_nearest_address_raw = box_nearest(obj_Noithuongtru, list_text_box2)
        nearest_address = obj_nearest_address_raw.key
        nearest_address_raw = nearest_address
    
    address = address + nearest_address
    print('nearest', nearest_address_raw)
    for obj in list_text_box2:
        if obj.two_points[1]<obj_Noithuongtru.two_points[1] and obj.key != nearest_address_raw:
            keys_above_noithuongtru.append(obj)

    if len(keys_above_noithuongtru) != 0:
        hometown2 = sort_key_left2right(keys_above_noithuongtru)
        hometown = hometown + ' '+hometown2
            
    for obj in keys_above_noithuongtru:
        list_text_box2.remove(obj)

    if obj_nearest_address_raw in list_text_box2:
        list_text_box2.remove(obj_nearest_address_raw)

    if nearest_address_raw != noithuongtru:
        list_text_box2.remove(obj_Noithuongtru)

    print('-----------------------')
    #print('DIC', dic)

    if len(list_text_box2) != 0:
        address2 = sort_key_left2right(list_text_box2)
        address = address + ' ' + address2
    
    # doi Phuong thanh P. va Quan thanh Q.
    hometown = change_PhuongQuan_to_PQ(hometown)
    address = change_PhuongQuan_to_PQ(address)

    print('Hometown', hometown)
    print('Address', address)

    hometown1 = mapping(hometown)
    address1 = mapping(address)

    # check whether it's Ho Chi Minh region
    pos = 0
    if hometown1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(hometown)-1):
            if (hometown[i]=='P' and hometown[i+1] in '0123456789') or (hometown[i]=='P' and hometown[i+2] in '0123456789'):
                pos = i
                #print(pos)
        hometown = hometown[pos:]
    if pos != 0:
        hometown1 = mapping(hometown)    
    pos = 0
    if address1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(address)-1):
            if (address[i]=='P' and address[i+1] in '0123456789') or (address[i]=='P' and address[i+2] in '0123456789'):
                pos = i
                #print(pos)
        address = address[pos:]
    
    if pos != 0:
        address1 = mapping(address)

    #print('homewon1', hometown)
    #print('address1', address)  

    return hometown1, address1
