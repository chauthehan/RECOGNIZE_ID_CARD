from tools.utils import *
from difflib import SequenceMatcher

def find_name_text(list_text_box2, obj_id, obj_birth,obj_cmnd, detector, copy_img):
    # if the box has more than 2 consecutive upper character, than it must be the box name
    
    birth_box = obj_birth.two_points
    dic_name = {}
    obj_name = None
    #print('OBJID', obj_id.key)
    if obj_id is not None:
        thresh = obj_id.two_points[1]
    else:
        thresh = obj_cmnd.two_points[1]
    for obj in list_text_box2:

        if obj.two_points[1] < birth_box[1] and obj.two_points[1] > thresh:
            
            key_no_accent = remove_accent(obj.key)
            #print('name', obj.key)
            if key_no_accent == '':
                continue
            else:
                count = count_upper_consecutive(key_no_accent)
            if count >= 2:
                #print(obj.key, ' ', count)
                dic_name[obj.key] = obj
    #print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
        obj_name = dic_name[name]
    else:
        #name appears on 2 lines
        name = lst_name[1] + ' ' + lst_name[0]
        obj_name = dic_name[lst_name[1]]
    
    # if name box couldn't be detected, we'll draw a box text around name region
    if name.find(' ') == -1 and name.find('-') == -1:
        w = birth_box[2]-birth_box[0]
        point1 = [int(obj_id.four_points[3][0][0]+w*1/7), obj_id.four_points[3][0][1]]
        point2 = [int(obj_id.four_points[2][0][0]+w*2/3), int(obj_id.four_points[2][0][1])]
        point3 = [int(obj_id.four_points[2][0][0]+w*2/3), int(obj_birth.four_points[1][0][1]-w/4)]
        point4 = [int(obj_id.four_points[3][0][0]+w*1/5), int(obj_birth.four_points[0][0][1]-w/4)]

        box = [[point1], [point2], [point3], [point4]]
        img = four_point_transform(copy_img, box)
        pil_img = Image.fromarray(img)
   
        name = detector.predict(pil_img)

    # Case: <name> ho ten
    pos = -1
    name = finalize(name)
    name_no_accent = remove_accent(name)
    if str.lower(name_no_accent).find('ho ten') >2:
        pos = str.lower(name_no_accent).find('ho ten')

        c = count_upper_consecutive(name[:pos])
        if c > 3:
            name = name[:pos]

    # Case: ho ten <name>
    pos = -1
    #name_no_accent = finalize(name_no_accent)
    name_no_accent = remove_accent(name)
    for j, i in enumerate(name_no_accent):
        if not ((i>='A' and i<='Y') or i == ' ' or i=='-'):
            pos = j
    
    #print('Name1: ', name)

    key_name = name[pos+1:]
    #print('key name', str.lower(remove_accent(key_name)))
    if str.lower(remove_accent(key_name))[:2] == 'ho':
        print('INNNNN')
        if obj_name.two_points[0] < obj_id.two_points[0]-(obj_id.two_points[3]-obj_id.two_points[1]):
            img = cv2.imread(obj_name.name_img)
            h = img.shape[0]
            w = img.shape[1]
            t = obj_cmnd.two_points[2]-obj_cmnd.two_points[0]
            img1 = img[0:h, int(t/9):w]
            pil_img = Image.fromarray(img1)
   
            key_name = detector.predict(pil_img)
            print('key name', key_name) 
            
            pos = -1
    #name_no_accent = finalize(name_no_accent)
            name_no_accent = remove_accent(key_name)
            for j, i in enumerate(name_no_accent):
                if not ((i>='A' and i<='Y') or i == ' ' or i=='-'):
                    pos = j
            
            key_name = key_name[pos+1:]      
        
    key_name = normalize_name(key_name)
    key_name = finalize(key_name)
    #print('Name2: ', key_name)
    return key_name, obj_name

def find_id_text(list_text_box2, detector):
    bot = 9999
    key_so = ''
    key_id = ''
    obj_id1 = None
    obj_id = None 
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
        print('find id: ', obj.key)
        if obj.two_points[1]<bot and key_no_accent.find('so') == 0:
            bot = obj.two_points[1]
            obj_id = obj
            key_so = key
    #print('ID', obj_id.key)
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

        if len(key_id) >= 9:
            key_id = key_id[-9:]

    else:
        dis = 9999
        for key in dic_num:
            if abs(dic_num[key].two_points[1]-obj_id.two_points[1]) < dis:
                dis = abs(dic_num[key].two_points[1]-obj_id.two_points[1])
                key_id = key
                obj_id1 = dic_num[key]
   
    key_id = remove_accent(key_id)
    key_id = str.lower(key_id)

    if key_id.find('so') == 0:
        if obj_id1 is not None:
            img = cv2.imread(obj_id1.name_img)
        else:
            img = cv2.imread(obj_id.name_img)
        h = img.shape[0]
        w = img.shape[1]

        img = img[0:h, int(w/6):w]
    #img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    #kernel = np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]])
    #img = cv2.filter2D(img, -1, kernel)
    
        img = cv2.GaussianBlur(img,(5,5),0)
    #cv2.imshow('', img)
    #cv2.waitKey(0)
        pil_img = Image.fromarray(img)

        key_id = detector.predict(pil_img)

    if len(key_id)==9 and key_id.find('/') != -1:
        key_id = key_id.replace('/', '7')

    print('after key id found: ', key_id)    
    key_id = remove_char(key_id)   

    key_id = key_id[-9:]
    #if obj_id1 is not None:

    key_id = finalize(key_id)

    return key_id, obj_id

def find_id_text_cc(list_text_box2, detector):
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

    img = cv2.imread(obj_id.name_img)
    h = img.shape[0]
    w = img.shape[1]
    img1 = img[0:h, int(w/8):w]
    pil_img = Image.fromarray(img1)
   
    key_id = detector.predict(pil_img)
    key_id = remove_char(key_id)

    if len(key_id) < 12:
        img1 = img[0:h, int(w/10):w]
        pil_img = Image.fromarray(img1)
        key_id = detector.predict(pil_img)
        key_id = remove_char(key_id)

        if len(key_id) < 12:
            pil_img = Image.fromarray(img)
            key_id = detector.predict(pil_img)
            key_id = remove_char(key_id)
    key_id = finalize(key_id)
    return key_id, obj_id

def find_birth_text(list_text_box2, obj_id):
    
    birth_size = 0
    key_birth = ''
    obj_birth = None 
    #birth_box = []
    print('obj_id', obj_id.key)
    for obj in list_text_box2:
        if obj != obj_id:
            key = obj.key
            #print(key)
            count = count_num_in_key(key)
            if (count == 8 and key.find('-')!=-1) or (count==8 and key.count(' ')==2) or (count==8 and key.count('/')==2): #and check:
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
                if k.find('/') != -1:
                    k = k.replace('/', '7')
                key_birth = k
                birth_box = obj.two_points
                # get the size of birth box
                birth_size = obj.size
    if obj_birth is not None:
        key_no_accent = remove_accent(obj_birth.key)
        count = count_char_in_key(key_no_accent)                
        if count > 5:
            birth_size = birth_size*2/3
    
    key_birth = finalize(key_birth)
    return key_birth, birth_size, obj_birth

def remove_wrong_box(list_text_box2, obj_id, obj_birth, birth_size, obj_cmnd):
    #print('before ', len(list_text_box2))
    if obj_birth is not None:
        birth_box = obj_birth.two_points
        list_obj_remove = []
        for obj in list_text_box2:
            if obj.size < int(birth_size/2.15):
                #print('111111')
                list_obj_remove.append(obj)
            
            length_birthbox = birth_box[2]-birth_box[0]

            if obj_id is not None:
                thresh = obj_id.two_points[0]
            else:
                thresh = obj_cmnd.two_points[0] + length_birthbox/3
            
            if obj.two_points[0] < thresh - length_birthbox and obj.two_points[2] - obj.two_points[0] < length_birthbox:
                #print('222222')
                list_obj_remove.append(obj)
            
            mark = False
            key = obj.key
            key = remove_accent(key)
            key = str.lower(key)
            for i in {'a', 'e', 'i', 'o', 'u', 'y'}:
                if key.find(i) != -1:
                    mark = True
                    break
            if not mark:
                list_obj_remove.append(obj)

            if len(obj.key)<=1:
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
                    #print('ROMOVE ', obj.key)
                    list_text_box2.remove(obj)
    
    #print('AFTER ', len(list_text_box2))
    #print('-------------')
    return list_text_box2

def remove_wrong_box_cc(list_text_box2, obj_id):
    list_obj_remove = []
    
    for obj in list_text_box2:
        print(obj.key, ' ', obj.size)
        if obj.size < obj_id.size/14:
            #print('111111')
            list_obj_remove.append(obj)
        
        leng = len(obj.key)
        num = count_num_in_key(obj.key)
        if (num == leng or num ==leng-1) and leng<=5:
            list_obj_remove.append(obj)
    
    for obj in list_obj_remove:
        if obj in list_text_box2:
            list_text_box2.remove(obj)
    
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
    nguyenquan = ''
    dkhk = ''

    # remove wrong box if has more than 4 consecutive upper characters 
    list_obj_remove = []
    for obj in list_text_box2:
        #print('LEFT', obj.key)
        c_upper = count_upper_consecutive(remove_accent(obj.key))
        c_lower = count_lower(remove_accent(obj.key))

        #print('UPPER', obj.key,' ', c_upper)
        #print('LOWER', c_lower)
        if c_upper>4 and c_lower==0:
            list_obj_remove.append(obj)
    
    for obj in list_text_box2:
        c = 0
        key = obj.key
        key = remove_accent(key)
        for i in key:
            if i>='A' and i <= 'Y':
                c += 1
        if c == 0 and obj not in list_obj_remove:
            list_obj_remove.append(obj)

    for obj in list_obj_remove:
        #print('remove upper: ', obj.key)
        list_text_box2.remove(obj)        

    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
    
        if score_nguyenquan(key_no_accent)>maxx:
            maxx = score_nguyenquan(key_no_accent)               
            obj_nguyenquan = obj
    
    #print(obj_nguyenquan.key,' ' ,maxx)
    if maxx < 30:
        obj_nguyenquan = None
        print('CANNOT find box nguyen quan')

    if obj_nguyenquan is not None:
        # delete box left of nguyenquan
        remove_obj = []
        for obj in list_text_box2:
            #print(obj.key,' ',obj.two_points)
            if obj.two_points[2] < obj_nguyenquan.two_points[0]:
                
                remove_obj.append(obj)   

        if remove_obj != []:
            for obj in remove_obj:
                print('REMOVVE', obj.key)
                list_text_box2.remove(obj)
        # remove box 'sinh ngay'
        sinhngay = None
        for obj in list_text_box2:
            key = obj.key
            if obj.two_points[2] > obj_nguyenquan.two_points[0] and obj.two_points[2]<obj_nguyenquan.two_points[2] and obj.two_points[1]<obj_nguyenquan.two_points[1]:
                sinhngay = obj
        
        if sinhngay is not None:
            print('delete SINHNGAY', sinhngay.key)
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
    
    if maxx < 50:
        obj_dkhk = None
        #print('Cannot find obj dkhk')
    #if obj_dkhk is not None:
        #print(obj_dkhk.key, ' ', maxx )  
    if obj_nguyenquan is not None:
        print('OBJ NGUYEN QUAN: ',obj_nguyenquan.key)
    if obj_dkhk is not None:
        print('OBJ DKHK: ', obj_dkhk.key)

    obj_top = None
    if obj_nguyenquan is not None and len(obj_nguyenquan.key[12:])>3:
        nguyenquan = obj_nguyenquan.key[12:]
        obj_top = obj_nguyenquan
    
    if obj_nguyenquan is not None and len(obj_nguyenquan.key[12:])<3:
        list_text_box2.remove(obj_nguyenquan)    
        obj_nguyenquan = None    
    min_pos = 10000
    max_pos = 0    

    if obj_nguyenquan is None:
        for obj in list_text_box2:
            print('llleft', obj.key)
            if obj.two_points[1] < min_pos:
                min_pos = obj.two_points[1]
                obj_top = obj  
        nguyenquan = nguyenquan + obj_top.key
    
    for obj in list_text_box2:
        if obj.two_points[1] > max_pos:
            max_pos = obj.two_points[1]
            obj_bot = obj
    
    if obj_bot == obj_dkhk:
        dkhk = dkhk + obj_bot.key[20:]
        obj_dkhk = None
    else:
        dkhk = dkhk + obj_bot.key
    
    if obj_dkhk is not None and len(obj_dkhk.key[20:])>2:
        dkhk = obj_dkhk.key[20:] + ' ' + dkhk
        for obj in list_text_box2:
            if obj != obj_dkhk and obj!= obj_bot and obj!=obj_top and obj!= obj_nguyenquan:
                nguyenquan = nguyenquan + ' ' +obj.key
        
        print('Nguyen quan: ', nguyenquan)
        print('DKHK: ', dkhk)
        nguyenquan1, dkhk1 = normalize_hometown_address(nguyenquan, dkhk)
        nguyenquan1 = finalize(nguyenquan1)
        dkhk1 = finalize(dkhk1)
        return nguyenquan1, dkhk1

    box_top = obj_top.two_points
    box_bot = obj_bot.two_points
    
    if obj_top in list_text_box2:
        list_text_box2.remove(obj_top)
    if obj_bot in list_text_box2:
        list_text_box2.remove(obj_bot)

    if obj_dkhk is not None and len(obj_dkhk.key[20:])<3:
        list_text_box2.remove(obj_dkhk)
        obj_dkhk = None

    for obj in list_text_box2:
        print('LEFT', obj.key)

    if len(list_text_box2) == 2:
        if list_text_box2[0].two_points[1]< list_text_box2[1].two_points[1]:
            nguyenquan = nguyenquan + ' ' + list_text_box2[0].key
            dkhk = list_text_box2[1].key + ' ' + dkhk
        else:
            nguyenquan = nguyenquan + ' ' + list_text_box2[1].key 
            dkhk = list_text_box2[0].key + ' ' + dkhk 
    
    if len(list_text_box2) == 1:
        if abs(list_text_box2[0].two_points[1]-box_top[1])<abs(list_text_box2[0].two_points[1]-box_bot[1]):
            nguyenquan = nguyenquan + ' '+list_text_box2[0].key 
        else:
            dkhk = list_text_box2[0].key + ' ' + dkhk   

    if len(list_text_box2) == 3:
        minn = min(list_text_box2[0].two_points[1], list_text_box2[1].two_points[1], list_text_box2[2].two_points[1])
        for obj in list_text_box2:
            if obj.two_points[1] == minn:
                nguyenquan = nguyenquan + ' ' + obj.key
                obj_of_nguyenquan = obj 

        list_text_box2.remove(obj_of_nguyenquan)
        
        if list_text_box2[0].two_points[0]>list_text_box2[1].two_points[0]:
            dkhk = list_text_box2[0].key + ' ' + dkhk
        else:
            dkhk = list_text_box2[1].key + ' ' + dkhk
    #if len(list_text_box2) == 3:
    
    print('Nguyen quan: ', nguyenquan)
    print('DKHK: ', dkhk)    
    nguyenquan1, dkhk1 = normalize_hometown_address(nguyenquan, dkhk)
    nguyenquan = finalize(nguyenquan1)
    dkhk = finalize(dkhk1)  
    return nguyenquan, dkhk

def find_box_Quoctich_Dantoc(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key = remove_accent(key)
        #key =  key[:10]
        score = score_Quoctich_Dantoc(key)
        #print(obj.key, ' ',score)
        if score > maxx:
            maxx = score
            obj_quoctich_dantoc = obj
    #print('Score quoctich_dantoc: ', obj_quoctich_dantoc.key, ' ',maxx)
    if maxx <20:
        obj_quoctich_dantoc = None
        #print('Cannot find quoctic_dantoc')
    
    return obj_quoctich_dantoc

def find_birth_text_cc(list_text_box2, obj_quoctich, img):
    key_birth = ''
    obj_birth = None
    for obj in list_text_box2:
        if obj_quoctich is not None:
            thresh = obj_quoctich.two_points[1]
        else:
            thresh = img.shape[0]*3/4

        if obj.two_points[1] < thresh:
            key = obj.key
            key_num = remove_char(key)
            
            if len(key_num)== 8:                                
                obj_birth = obj
                key_birth = key_num
            elif len(key_num) in [9, 10]:
                obj_birth = obj
                key_birth = key_num[-8:]             
    
    #print('KEYBIRTH', key_birth)
    key_birth = process_birth(key_birth)
    key_birth = finalize(key_birth)
    return key_birth, obj_birth

def find_cogiatriden(list_text_box2):
    maxx = 0
    obj_ex = None
    for obj in list_text_box2:
        text = obj.key
        text_no_accent = remove_accent(text)
        score = score_expired(text_no_accent)
        if score>maxx:
            maxx = score
            obj_ex = obj
    return obj_ex

def find_name_text_cc(list_text_box2, obj_quoctich, VietNamdantoc, obj_id, img):
    # if the box has more than 2 consecutive upper character, than it must be the box name
    #obj_name = None
    if VietNamdantoc is not None:
        thresh = VietNamdantoc.two_points[1]
    elif obj_quoctich is not None:
        thresh = obj_quoctich.two_points[1]
    else:
        thresh = img.shape[0]*3/4
    dic_name = {}
    #bottom = 0
    for obj in list_text_box2:
        #print('finding Name ', obj.key)
        if obj.two_points[1] < thresh and obj.two_points[1] > obj_id.two_points[1]:            
            key_no_accent = remove_accent(obj.key)
            #print('name', obj.key)
            if key_no_accent == '':
                continue
            else:
                count = count_upper_consecutive(key_no_accent)
            if count >= 2:
                dic_name[obj.key] = obj
    print('name', dic_name)
    lst_name = []
    for key in dic_name:
        lst_name.append(key)
    if len(lst_name)==1:
        name = lst_name[0]
        obj_name = dic_name[key]
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
    key_name = normalize_name(key_name)
    key_name = finalize(key_name)
    return key_name#, obj_name
        
def find_key_expired(list_text_box2, obj_birth):
    key_ex = ''
    obj_ex = None 
    for obj in list_text_box2:
        if obj.two_points[1] > obj_birth.two_points[1]:
            key = obj.key
            count = count_num_in_key(key)

            if count == 8:
                key_ex = remove_char(key)
                key_ex = process_birth(key_ex)
                obj_ex = obj

    key_ex = finalize(key_ex)
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

    if maxx < 18:
        print('Cannot found box gioi tinh')        
        obj_Gioitinh = None
    #print('Score gioi tinh: ', maxx)
    #print('Obj gioi tinh found: ', obj_Gioitinh.key)
    else:
  
        key_no_accent = remove_accent(obj_Gioitinh.key)
        
        if key_no_accent.find('Nam') != -1:
            return 'Nam', obj_Gioitinh, obj_nam_or_nu

        elif key_no_accent.find('Nu') != -1:
            return 'Nữ', obj_Gioitinh, obj_nam_or_nu
        elif key_no_accent.find('a') != -1:
            return 'Nam', obj_Gioitinh, obj_nam_or_nu
        elif key_no_accent.find('u') != -1:
            return 'Nữ', obj_Gioitinh, obj_nam_or_nu
        
        elif box_nearest_gioitinh_cc(obj_Gioitinh, list_text_box2) is not None:
            obj_nam_or_nu = box_nearest_gioitinh_cc(obj_Gioitinh, list_text_box2)
            key = obj_nam_or_nu.key
            key_no_accent = remove_accent(key)
            if key_no_accent == 'Nam':
                sex = 'Nam'
            elif key_no_accent == 'Nu':
                sex= 'Nữ'
            
            if sex != '':
                return sex, obj_Gioitinh, obj_nam_or_nu
        
    return sex, obj_Gioitinh, obj_nam_or_nu

def delete_box_processed_cc(list_text_box2, obj_Gioitinh, obj_nam_or_nu, obj_quoctich_dantoc, obj_expired, obj_birth, VietNamdantoc, type_cut):
    return_address = ''
    if type_cut != 2:
        obj_cogiatriden = find_cogiatriden(list_text_box2)

        # Xu ly truong hop 2 box co gia tri den va box dia chi cua noi thuong tru dinh nhau
        if obj_cogiatriden is not None and len(obj_cogiatriden.key)>30:
            return_address = obj_cogiatriden.key[26:]
        elif obj_expired is not None and obj_expired != obj_cogiatriden and len(obj_expired.key)>13:
            return_address = obj_expired.key[10:]

        print('[INFO_1] remove {}'.format(obj_cogiatriden.key))
        if obj_cogiatriden in list_text_box2:
            list_text_box2.remove(obj_cogiatriden)
        
        if obj_expired in list_text_box2:
            print('[INFO_2] remove {}'.format(obj_expired.key))
            list_text_box2.remove(obj_expired)
    else:
        if obj_expired in list_text_box2:
            print('[INFO_3] remove {}'.format(obj_expired.key))
            list_text_box2.remove(obj_expired)
    maxx = 0
    
    if obj_nam_or_nu is not None:
        print('[INFO_4] remove {}'.format(obj_nam_or_nu.key))
        list_text_box2.remove(obj_nam_or_nu)
    
    if VietNamdantoc is not None:
        print('KEY vietnam', VietNamdantoc.key)

    obj_ngaythangnamsinh = find_ngaythangnamsinh(list_text_box2)
    if VietNamdantoc is not None:
        print('[INFO_5] remove {}'.format(VietNamdantoc.key))
        list_text_box2.remove(VietNamdantoc)
    
    if obj_quoctich_dantoc in list_text_box2:
        print('[INFO_6] remove {}'.format(obj_quoctich_dantoc.key))
        list_text_box2.remove(obj_quoctich_dantoc)
    
    if obj_Gioitinh in list_text_box2:
        print('[INFO_7] remove {}'.format(obj_Gioitinh.key))
        list_text_box2.remove(obj_Gioitinh)

    list_obj_remove = []
                  
    center_birth = (obj_birth.two_points[1]+obj_birth.two_points[3])/2
    for obj in list_text_box2:
        center = (obj.two_points[1] + obj.two_points[3])/2
        if center <= center_birth:
            
            list_obj_remove.append(obj)

    for obj in list_obj_remove:
        print('listremove', obj.key)
        if obj in list_text_box2:
            list_text_box2.remove(obj)

    if obj_ngaythangnamsinh in list_text_box2:
        list_text_box2.remove(obj_ngaythangnamsinh)
    
    return list_text_box2, return_address

def find_VietNam_dantoc(list_text_box2, obj_quoctich_dantoc):
    #if obj_quoctich_dantoc is None:
    for obj in list_text_box2:        
        if remove_accent(obj.key).find('Viet Nam')  != -1:
            return obj
        if remove_accent(obj.key) == 'Kinh':
            return obj
    #else:
    if obj_quoctich_dantoc is not None:
        key = obj_quoctich_dantoc.key
        key1 = key[:10]

        ratio1 = SequenceMatcher(a=key1, b='Quốc tịch').ratio()
        ratio2 = SequenceMatcher(a=key1, b='Dân tộc').ratio()

        if ratio1>ratio2:
            if len(key) < 12:
                for obj in list_text_box2:
                    #print('find vietnam', obj.key)
                    if obj.two_points[0] > obj_quoctich_dantoc.two_points[2] and len(key)<10:
                        return obj
            else:
                return None
        else:
            if len(key) < 10:
                for obj in list_text_box2:
                    if obj.two_points[0] > obj_quoctich_dantoc.two_points[2] and len(key)<10:
                        return obj
            else:
                return None

    return None       

def find_hometown_address_text_cc(list_text_box2, cogiatriden):

    quequan = ''
    ntt = ''

    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        key_no_accent = remove_accent(key)
        key_no_accent = str.lower(key_no_accent)
    
        if score_Quequan(key_no_accent)>maxx:
            maxx = score_Quequan(key_no_accent)               
            obj_quequan = obj
    if maxx < 15:
        obj_quequan = None
        print('CANNOT find box Que quan')

    if obj_quequan is not None:
        # delete box left of quequan
        remove_obj = []
        for obj in list_text_box2:
            #print(obj.key,' ',obj.two_points)
            if obj.two_points[2] < obj_quequan.two_points[0]:
                
                remove_obj.append(obj)   

        if remove_obj != []:
            for obj in remove_obj:
                #print('REMOVVE', obj.key)
                list_text_box2.remove(obj)
        # remove box 'sinh ngay'
        sinhngay = None
        for obj in list_text_box2:
            key = obj.key
            if obj.two_points[2] > obj_quequan.two_points[0] and obj.two_points[2]<obj_quequan.two_points[2] and obj.two_points[1]<obj_quequan.two_points[1]:
                sinhngay = obj
        
        if sinhngay is not None:
            #print('SINHNGAY', sinhngay.key)
            list_text_box2.remove(sinhngay)      

    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        # if box has at least 3 word in Noi ntt thuong tru, 
        # than it must be address box
        key_no_accent = remove_accent(key)            
        if score_Noithuongtru(key_no_accent)>maxx:                
            maxx = score_Noithuongtru(key_no_accent)
            obj_ntt = obj
    
    if maxx < 30:
        obj_ntt = None
        print('Cannot find obj ntt')
    if obj_ntt is not None:
        print('OBJ NTT: ', obj_ntt.key, ' ', maxx )  
    if obj_quequan is not None:
        print('OBJ QUE QUUAN: ', obj_quequan.key)

    obj_top = None
    if obj_quequan is not None and len(obj_quequan.key[9:])>3:
        quequan = obj_quequan.key[8:]
        obj_top = obj_quequan
        #obj_quequan = None
    #print('QUEQUAN00', quequan)
    if obj_quequan is not None and len(obj_quequan.key[9:])<3:
        list_text_box2.remove(obj_quequan)    
        obj_quequan = None
    min_pos = 10000
    max_pos = 0    

    if obj_quequan is None:
        for obj in list_text_box2:
            if obj.two_points[1] < min_pos:
                min_pos = obj.two_points[1]
                obj_top = obj  
        quequan = quequan + obj_top.key
    #print('QUEQUAN0', quequan)
    for obj in list_text_box2:
        if obj.two_points[1] > max_pos:
            max_pos = obj.two_points[1]
            obj_bot = obj    

    # truong hop box expired dinh voi box ntt
    if cogiatriden != '':
        ntt = ntt + cogiatriden
    elif obj_bot == obj_ntt:
        ntt = ntt + obj_bot.key[14:]
        obj_ntt = None
    else:
        ntt = ntt + obj_bot.key
    #print('BOT', obj_bot.key)
    #print('QUEQUAN1', quequan)
    if obj_ntt is not None and len(obj_ntt.key[15:])>2:
        #print('IN')
        ntt = obj_ntt.key[14:] + ' ' + ntt
        for obj in list_text_box2:
            if obj != obj_ntt and obj!= obj_bot and obj!=obj_top and obj!= obj_quequan:
                quequan = quequan + ' ' +obj.key
       # print('QUEQUAN2', quequan)
        print('Que quan: ', quequan)
        print('Noi thuong tru: ', ntt)
        quequan1, ntt1 = normalize_hometown_address(quequan, ntt)
        quequan1 = finalize(quequan1)
        ntt1 = finalize(ntt1)

        return quequan1, ntt1

    box_top = obj_top.two_points
    box_bot = obj_bot.two_points
    
    if obj_top in list_text_box2:
        list_text_box2.remove(obj_top)
    if obj_bot in list_text_box2:
        list_text_box2.remove(obj_bot)

    if obj_ntt is not None and len(obj_ntt.key[20:])<3:
        list_text_box2.remove(obj_ntt)
        obj_ntt = None
    
    for obj in list_text_box2:
        print('LEFT', obj.key)
    
    if len(list_text_box2) == 2:
        if list_text_box2[0].two_points[1]< list_text_box2[1].two_points[1]:
            quequan = quequan + ' ' + list_text_box2[0].key
            ntt = list_text_box2[1].key + ' ' + ntt
        else:
            quequan = quequan + ' ' + list_text_box2[1].key 
            ntt = list_text_box2[0].key + ' ' + ntt 
    
    if len(list_text_box2) == 1:
        if abs(list_text_box2[0].two_points[1]-box_top[1])<abs(list_text_box2[0].two_points[1]-box_bot[1]):
            quequan = quequan + ' '+list_text_box2[0].key 
        else:
            ntt = list_text_box2[0].key + ' ' + ntt
    
    if len(list_text_box2) == 3:
        minn = min(list_text_box2[0].two_points[1], list_text_box2[1].two_points[1], list_text_box2[2].two_points[1])
        for obj in list_text_box2:
            if obj.two_points[1] == minn:
                quequan = quequan + ' ' + obj.key
                obj_of_quequan = obj 

        list_text_box2.remove(obj_of_quequan)
        
        if list_text_box2[0].two_points[0]>list_text_box2[1].two_points[0]:
            ntt = list_text_box2[0].key + ' ' + ntt
        else:
            ntt = list_text_box2[1].key + ' ' + ntt

    print('Que quan: ', quequan)
    print('Noi thuong tru: ', ntt)
    quequan1, ntt1 = normalize_hometown_address(quequan, ntt)

    quequan = finalize(quequan1)
    ntt = finalize(ntt1)
    return quequan, ntt
    
def find_ngaythangnamsinh(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        key = obj.key
        if len(key) >= 19:
            key = key[:19]
            key = remove_accent(key)
            ratio = SequenceMatcher(a=key, b='Ngay thang nam sinh').ratio()
            if ratio > maxx:
                maxx = ratio 
                obj_res = obj 
    
    return obj_res

def find_gioitinh_base_vietnam(list_text_box2, VietNamdantoc, obj_quoctich_dantoc):
    key = VietNamdantoc.key 
    key = remove_accent(key)

    if key.count('Nam') == 2:
        print('Found NAM base Viet Nam, connected boxes')
        return 'Nam'
    elif key.find('Nu') != -1:
        print('Found NU base Viet Nam, connected boxes')
        return 'Nữ'
    
    list_text_box_temp = list_text_box2

    if VietNamdantoc != obj_quoctich_dantoc and obj_quoctich_dantoc is not None:
        list_text_box_temp = list_text_box2.remove(obj_quoctich_dantoc)
    
    obj = box_nearest(VietNamdantoc, list_text_box_temp)
    
    if remove_accent(obj.key).find('Nam') != -1:
        print('Found NAM base Viet Nam')
        return 'Nam'
    elif remove_accent(obj.key).find('Nu') != -1:
        print('Found NU base Viet Nam')
        return 'Nữ'
    
    return  ''
  