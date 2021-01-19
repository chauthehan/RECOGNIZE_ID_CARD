from tools.utils import *

def find_name_text(list_text_box2, obj_id, birth_box):
    # if the box has more than 2 consecutive upper character, than it must be the box name
    
    dic_name = {}
    #bottom = 0
    print('OBJID', obj_id.key)
    
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
    print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
    else:
        #name appears on 2 lines
        name = lst_name[1] + ' ' + lst_name[0]

    name_no_mark = remove_accent(name)
    for j, i in enumerate(name_no_mark[1:]):
        if i>='A' and i<='Y':
            pos = j
            break 
    key_name = name[pos:]
    return key_name

def find_id_text(list_text_box2):
    bot = 9999
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
            dic_num[key] = obj.two_points

    if len(remove_char(key_so))>=4:
        key_id = key_so
    else:
        dis = 9999
        for key in dic_num:
            if abs(dic_num[key][1]-obj_id.two_points[1]) < dis:
                dis = abs(dic_num[key][1]-obj_id.two_points[1])
                key_id = key

    key_id = remove_char(key_id)
    
    return key_id, obj_id

def find_birth_text(list_text_box2, obj_id):
    birth_size = 0
    key_birth = ''

    for obj in list_text_box2:
        if obj != obj_id:
            key = obj.key
            #print(key)
            count = count_num_in_key(key)
            if count == 8 and key.find('-')!=-1: #and check:
                # get the birth box
                key_birth = process_birth(key)
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size

            if (key[:2]=='19' and count==4):
                k = remove_accent(key)
                k = remove_char_birth(k)
                key_birth = key
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size*2

            if count == 7 and key.find('-')!=-1:
                k = remove_accent(key)
                k = remove_char_birth(k)
                key_birth = k
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size
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
    
    print(list_obj_remove)
    
    set_remove = set(list_obj_remove)
    list_obj_remove = list(set_remove)
    
    #print('REMOVE', list_key_remove)
    for obj in list_obj_remove:
        if obj.key == '':
            continue
        else:
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
    #print('NGUYENQUAN', nguyenquan)
    #print(box_nguyenquan)

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
    
    print('LISTTESTBOX2')
    for i in list_text_box2:
        print(i.key)
    if len(list_text_box2) != 0:
        address2 = sort_key_left2right(list_text_box2)
        address = address + ' ' + address2
    print('Hometown', hometown)
    print('Address', address)
    hometown, address = mapping(hometown, address)
    
    return hometown, address

def find_box_Quoctich(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        score = score_Quoctich(obj.key)
        if score > maxx:
            maxx = score
            obj_Quoctich = obj 
    return obj_Quoctich

def find_birth_text_cc(list_text_box2, obj_quoctich):
    for obj in list_text_box2:
        if obj.two_points[1] < obj_quoctich.two_points[1]:
            key = obj.key
            count = count_num_in_key(key)

            if count == 8:
                key_birth = remove_char(key)
                key_birth = process_birth(key_birth)
                obj_birth = obj
    return key_birth, obj_birth

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
    print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
    else:
        #name appears on 2 lines
        name = lst_name[1] + ' ' + lst_name[0]

    name_no_mark = remove_accent(name)
    for j, i in enumerate(name_no_mark[1:]):
        if i>='A' and i<='Y':
            pos = j
            break 
    key_name = name[pos:]
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
    for obj in list_text_box2:
        key = obj.key
        if score_Gioitinh(key) > maxx:
            maxx = score_Gioitinh(key)
            obj_Gioitinh = obj
    
    key_no_accent = remove_accent(obj_Gioitinh.key)
    if key_no_accent.find('Nam') != -1:
        return 'Nam', obj_Gioitinh, obj_nam_or_nu
    elif key_no_accent.find('Nu') != -1:
        return 'Nữ', obj_Gioitinh, obj_nam_or_nu
    else:
        obj_nam_or_nu = box_nearest_cc(obj_Gioitinh, list_text_box2)
        key = obj_nam_or_nu.key
        key_no_accent = remove_accent(key)
        if key_no_accent == 'Nam':
            sex = 'Nam'
        elif key_no_accent == 'Nu':
            sex= 'Nữ'
        return sex, obj_Gioitinh, obj_nam_or_nu

def delete_box_processed_cc(list_text_box2, obj_Gioitinh, obj_nam_or_nu, obj_quoctich, obj_expired):
    
    obj_cogiatriden = find_cogiatriden(list_text_box2)
    
    if obj_nam_or_nu is not None:
        list_text_box2.remove(obj_nam_or_nu)
    list_text_box2.remove(obj_quoctich)
    list_text_box2.remove(obj_cogiatriden)
    if obj_expired in list_text_box2:
        list_text_box2.remove(obj_expired)
        
    list_obj_remove = []
    for obj in list_text_box2:
        if obj.two_points[1] <= obj_Gioitinh.two_points[1]:
            list_obj_remove.append(obj)
    
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        if key_no_accent == 'Viet Nam':
            list_obj_remove.append(obj)
    
    for obj in list_obj_remove:
        list_text_box2.remove(obj)
    
    return list_text_box2

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
    
        if score_Quequan(key_no_accent)>maxx:
            maxx = score_Quequan(key_no_accent)               
            quequan = key
            box_quequan = obj.two_points
            obj_quequan = obj
    #print('NGUYENQUAN', nguyenquan)
    #print(box_nguyenquan)

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

    for obj in list_text_box2:
        if obj.two_points[1]<obj_Noithuongtru.two_points[1] and obj.key != nearest_address_raw:
            keys_above_noithuongtru.append(obj)

    if len(keys_above_noithuongtru) != 0:
        hometown2 = sort_key_left2right(keys_above_noithuongtru)
        hometown = hometown + ' '+hometown2
            
    for obj in keys_above_noithuongtru:
        list_text_box2.remove(obj)
    list_text_box2.remove(obj_nearest_address_raw)

    if nearest_address_raw != noithuongtru:
        list_text_box2.remove(obj_Noithuongtru)

    print('-----------------------')
    #print('DIC', dic)

    if len(list_text_box2) != 0:
        address2 = sort_key_left2right(list_text_box2)
        address = address + ' ' + address2
    
    print('Hometown', hometown)
    print('Address', address)
    
    hometown, address = mapping(hometown, address)
    
    return hometown, address    
