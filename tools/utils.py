import os
import numpy as np
import cv2
import math 
import imutils
from PIL import Image
# from infer_det import textbox
from difflib import SequenceMatcher
from tools.score import *

class textbox:
    def __init__(self, key, two_points, four_points, size, name_img):
        self.key = key
        self.two_points = two_points # describe text box by 2 points rectangle
        self.four_points = four_points # describe text box by 4 points quadrilateral
        self.size = size
        self.name_img = name_img

def order_points(pts):
    # initialzie a list of coordinates that will be ordered
    # such that the first entry in the list is the top-left,
    # the second entry is the top-right, the third is the
    # bottom-right, and the fourth is the bottom-left
    rect = np.zeros((4, 2), dtype = "float32")
    # the top-left point will have the smallest sum, whereas
    # the bottom-right point will have the largest sum
    s = pts.sum(axis = 1)
    rect[0] = pts[np.argmin(s)]
    rect[2] = pts[np.argmax(s)]
    # now, compute the difference between the points, the
    # top-right point will have the smallest difference,
    # whereas the bottom-left will have the largest difference
    diff = np.diff(pts, axis = 1)
    rect[1] = pts[np.argmin(diff)]
    rect[3] = pts[np.argmax(diff)]
    # return the ordered coordinates
    return rect

def four_point_transform(image, box):
    # obtain a consistent order of the points and unpack them
    # individually

    lst = []
    lst.append((box[0][0][0], box[0][0][1]))
    lst.append((box[1][0][0], box[1][0][1]))
    lst.append((box[2][0][0], box[2][0][1]))
    lst.append((box[3][0][0], box[3][0][1]))    

    #print(lst)
    lst = np.array(lst, dtype='float32')
    rect = order_points(lst)
    (tl, tr, br, bl) = rect
    height = abs(tl[1]-bl[1])
    tl[0] = tl[0]
    tl[1] = tl[1]- int(height/4.5)
    tr[0] = tr[0]+ int(height/3.7)
    tr[1] = tr[1]- int(height/4.5)
    br[0] = br[0]+ int(height/3.7)
    br[1] = br[1]+ int(height/7)
    bl[0] = bl[0]
    bl[1] = bl[1]+ int(height/7)
    
    # compute the width of the new image, which will be the
    # maximum distance between bottom-right and bottom-left
    # x-coordiates or the top-right and top-left x-coordinates
    widthA = np.sqrt(((br[0] - bl[0]) ** 2) + ((br[1] - bl[1]) ** 2))
    widthB = np.sqrt(((tr[0] - tl[0]) ** 2) + ((tr[1] - tl[1]) ** 2))
    maxWidth = max(int(widthA), int(widthB))
    # compute the height of the new image, which will be the
    # maximum distance between the top-right and bottom-right
    # y-coordinates or the top-left and bottom-left y-coordinates
    heightA = np.sqrt(((tr[0] - br[0]) ** 2) + ((tr[1] - br[1]) ** 2))
    heightB = np.sqrt(((tl[0] - bl[0]) ** 2) + ((tl[1] - bl[1]) ** 2))
    maxHeight = max(int(heightA), int(heightB))
    # now that we have the dimensions of the new image, construct
    # the set of destination points to obtain a "birds eye view",
    # (i.e. top-down view) of the image, again specifying points
    # in the top-left, top-right, bottom-right, and bottom-left
    # order
    dst = np.array([
        [0, 0],
        [maxWidth - 1, 0],
        [maxWidth - 1, maxHeight - 1],
        [0, maxHeight - 1]], dtype = "float32")
    # compute the perspective transform matrix and then apply it
    M = cv2.getPerspectiveTransform(rect, dst)
    warped = cv2.warpPerspective(image, M, (maxWidth, maxHeight))
    # return the warped image
    return warped

def crop_image(I, box):
    # Go over the points in the image if thay are out side of the emclosing rectangle put zero
    # if not check if thay are inside the polygon or not

    # Now we can crop again just the envloping rectangle
    box[0][0][0] = max(box[0][0][0] - 5, 0)
    box[0][0][1] = max(box[0][0][1] - 2, 0)
    box[1][0][0] = min(box[1][0][0] + 5, I.shape[1])
    box[1][0][1] = max(box[1][0][1] - 2, 0)
    box[2][0][0] = min(box[2][0][0] + 5, I.shape[1])
    box[2][0][1] = min(box[2][0][1] + 2, I.shape[0])
    box[3][0][0] = max(box[3][0][0] - 5, 0)
    box[3][0][1] = min(box[3][0][1] + 2, I.shape[0])
    
    minX = I.shape[1]
    maxX = -1
    minY = I.shape[0]
    maxY = -1

    for point in box:

        x = point[0][0]
        y = point[0][1]

        if x < minX:
            minX = x
        if x > maxX:
            maxX = x
        if y < minY:
            minY = y
        if y > maxY:
            maxY = y

    return [minX, minY, maxX, maxY]

def remove_accent(str1):
    # Remove accent in text
    new_str = ''
    for i in str1:
        if i in ['á', 'à', 'ạ', 'ã', 'ả', 'ắ', 'ằ', 'ẳ', 'ẵ', 'ặ', 'ă', 'â', 'ấ', 'ầ', 'ẩ', 'ẫ', 'ậ']:
            new_str = new_str + 'a'
        elif i in ['Á','À','Ạ','Ã','Ả','Ắ','Ằ','Ẵ','Ẳ','Ặ','Ă','Â','Ấ','Ầ','Ẩ','Ẫ', 'Ậ']:
            new_str = new_str + 'A'
        elif i in ['é', 'è', 'ẻ', 'ẽ', 'ẹ', 'ế', 'ề', 'ể', 'ễ', 'ệ', 'ê']:
            new_str = new_str + 'e'
        elif i in ['É', 'È', 'Ẻ', 'Ẽ', 'Ẹ', 'Ế', 'Ề', 'Ê', 'Ể', 'Ễ', 'Ệ']:
            new_str = new_str + 'E'
        elif i in ['í', 'ì', 'ỉ', 'ĩ', 'ị']:
            new_str = new_str + 'i'
        elif i in ['Í', 'Ì', 'Ỉ', 'Ĩ', 'Ị']:
            new_str = new_str + 'I'
        elif i in ['ó', 'ò', 'ỏ', 'õ', 'ọ', 'ớ', 'ờ', 'ở', 'ỡ', 'ợ', 'ơ', 'ô', 'ố', 'ồ', 'ổ', 'ỗ', 'ộ']:
            new_str = new_str + 'o'
        elif i in ['Ó', 'Ò', 'Ỏ', 'Õ', 'Ọ', 'Ớ', 'Ờ', 'Ở', 'Ỡ', 'Ợ', 'Ơ', 'Ô', 'Ố', 'Ồ', 'Ổ', 'Ỗ', 'Ộ']:
            new_str = new_str + 'O'
        elif i in ['ú', 'ù', 'ủ', 'ũ', 'ụ', 'ứ', 'ư', 'ừ', 'ử', 'ữ', 'ự']:
            new_str = new_str + 'u'
        elif i in ['Ú', 'Ù', 'Ủ', 'Ũ', 'Ụ', 'Ứ', 'Ư', 'Ừ', 'Ử', 'Ữ', 'Ự']:
            new_str = new_str + 'U'
        elif i == 'Đ':
            new_str = new_str + 'D'
        elif i == 'đ':
            new_str = new_str + 'd'
        elif i in ['ý', 'ỳ', 'ỹ', 'ỷ', 'ỵ']:
            new_str = new_str + 'y'
        elif i in ['Ý', 'Ỳ', 'Ỹ', 'Ỷ', 'Ỵ']:
            new_str = new_str + 'Y'
        else:
            new_str = new_str + i
    return new_str

def box_nearest(obj, list_text_box2):
    # Function to find the nearest box on the right of a specified box
    count = 0
    sum_corner = 0
    c = 0
    for ob in list_text_box2:
        point1 = [(ob.four_points[0][0][0]+ob.four_points[3][0][0])/2, (ob.four_points[0][0][1]+ob.four_points[3][0][1])/2] 
        point2 = [(ob.four_points[1][0][0]+ob.four_points[2][0][0])/2, (ob.four_points[1][0][1]+ob.four_points[3][0][1])/2]
        dis = math.sqrt((point2[0]-point1[0])**2+(point2[1]-point1[1])**2)
        h = point2[1] - point1[1]
        sin = h/dis
        corner_rad = np.arcsin(sin)
        #corner_deg = corner_rad/np.pi*180
        #print(ob.key,' ', corner_deg)
        count = count+1
        sum_corner += corner_rad
    
    corner = abs(sum_corner/count)
    #print('CORNER', corner/np.pi*180)    
    
    point1 = [(obj.four_points[0][0][0]+obj.four_points[1][0][0]+obj.four_points[2][0][0]+obj.four_points[3][0][0])/4, (obj.four_points[0][0][1]+obj.four_points[1][0][1]+obj.four_points[2][0][1]+obj.four_points[3][0][1])/4]

    min_dis = 10000
    for objj in list_text_box2:
        #print('objj', objj.key,' ', objj.four_points)
        if obj.key == objj.key:
            continue
        point2 = [(objj.four_points[0][0][0]+objj.four_points[1][0][0]+objj.four_points[2][0][0]+objj.four_points[3][0][0])/4, (objj.four_points[0][0][1]+objj.four_points[1][0][1]+objj.four_points[2][0][1]+objj.four_points[3][0][1])/4]

        dis = math.sqrt((point2[0]-point1[0])**2+(point2[1]-point1[1])**2)
        h = point2[1] - point1[1]
        sin = h/dis
        corner_rad = abs(np.arcsin(sin))
        #print('CORNER_rad', corner_rad/np.pi*180)    
        #corner_deg = abs(corner_rad/np.pi*180)

        corner_a = abs(corner_rad - corner)
        #print('corner_a', corner_a/np.pi*180)

        dis_a = dis*np.sin(corner_a)

        #print(obj.key, ' ',objj.key,' ', dis_a)
        if dis_a < min_dis:
            min_dis = dis_a
            return_obj = objj
    
    return return_obj

def remove_char(key):
    # Get only numbers in a string
    id = ''
    for i in key:
        if i>='0' and i<='9':
            id = id+i
    return id

def remove_low_char(key):

    # remove lower characters in a tring
    mark_pos = 0
    key_no_mark = remove_accent(key)
    for i, char in enumerate(key_no_mark):
        if not (char>='A' and char<='Y' or char==' '):
            mark_pos = i
    if mark_pos != 0:
        return key[mark_pos+1:]
    else:
        return key[mark_pos:]

def remove_char_birth(key):
    # Remove alphabet characters in birth text 
    id = ''
    for i in key:
        if not (i>='a' and i<='z' or (i>='A' and i<='Z')):
            id = id+i
    return id    

def process_birth(key):
    # convert 11021900 => 11-02-1900
    birth = ''
    for char in key:
        if char>='0' and char<='9':
            birth = birth + char 
    
    if len(birth)==8:
        if birth[2] == '7':
            birth = birth[:2] + '1' +birth[3:]
        if int(birth[2]) > 1 and int(birth[2])!=7:
            birth = birth[:2] + '0' +birth[3:]

        if birth[0] == '7':
            birth = birth[:0] + '1' +birth[1:]
        if int(birth[0]) > 3 and int(birth[2])!=7:
            birth = birth[:0] + '0' +birth[1:]
       
    final_birth = ''
    i = -1
    while True:
        i = i+1
        final_birth = final_birth+birth[i]
        if i in {1, 3}:
            final_birth = final_birth + '-'
        if i==len(birth)-1:
            break 
    return final_birth
        
def finalize(key):
    # Clean text to get the final result
    if key == '':
        return ''
    key_no_mark = remove_accent(key)
    i = -1
    while True:
        i = i+1

        char = key_no_mark[i]
        
        if not (('a'<=char and 'y'>=char) or ('A'<=char and 'Y'>=char)or ('0'<=char and '9'>=char)):

            key = key[:i] + key[i+1:]
            key_no_mark = remove_accent(key)
            i = i-1
        else:
            break

    if key == '':
        return ''

    i = len(key)
    key_no_mark = remove_accent(key)
    while True:
        i = i-1
        char = key_no_mark[i]
        if not (('a'<=char and 'y'>=char) or ('A'<=char and 'Y'>=char)or ('0'<=char and '9'>=char)):
            key = key[:i]
        else:
            break 
        if i==0:
            break    
    i = 0
    while True:
        if key[i]==',' and key[i+1]==',':
            key = key[:i] + key[i+1:]
            i = i-1
        i=i+1
        if i == len(key):
            break 
    
    return key 

def count_num_in_key(key):
    # Count the amount of number character in a string
    count = 0
    # check = False
    for i in key:
        if i >= '0' and i <= '9':
            count = count+1
    return count

def count_upper_consecutive(key):
    # Count the amount of consecutive upper characters in a string
    count = 0
    count_max = 0
    i = 0
    while True:
        if key[i]>='A' and key[i]<='Y':
            count = count+1

        if i == len(key)-1:
            if count>count_max:
                count_max = count
            return count_max

        if key[i+1]>='a' and key[i+1]<='y':
            if count>count_max:
                count_max = count
            count = 0
        i = i + 1

def count_lower(key):
    # count the amount of lower characters in a string
    count = 0
    count_max = 0
    i = 0
    for i in key:
        if i>='a' and i<='y':
            count +=1
    return count

def remove_first_lower(key):
    final = ''
    i = 0
    if key[0]>='a' and key[0]<='z':
        pos = key.find(' ')
        final = key[pos:]
        return final 
    else:
        return key

def distance(p0, p1):
    return math.sqrt(((p0[0]-p1[0])**2+(p0[1]-p1[1])**2))        

def calculate_size_quadrilateral(array):
    p0 = array[0][0]
    p1 = array[1][0]
    p2 = array[2][0]
    p3 = array[3][0]

    p0p1 = distance(p0, p1)
    p1p2 = distance(p1, p2)
    p2p3 = distance(p2, p3)
    p3p0 = distance(p3, p0)
    p0p2 = distance(p0, p2)

    c1 = (p0p1+p1p2+p0p2)/2
    c2 = (p0p2+p2p3+p3p0)/2

    s1 = math.sqrt((c1*(c1-p0p1)*(c1-p1p2)*(c1-p0p2)))
    s2 = math.sqrt((c2*(c2-p0p2)*(c2-p2p3)*(c2-p3p0)))

    return s1+s2 

def remove_last_char(pred):
    if pred is not None:
        if pred[-1] in {'.', ',','-', '/'}:
            pred = pred[:-1]
    return pred 

def cut_roi(list_text_box, copy_img):

    max1 = 0
    max2 = 0
    max3 = 0
    obj_conghoa = None

    for obj in list_text_box:
        text = obj.key
        text_no_accent = remove_accent(text)
        sc_dkhk = score_dkhk(text_no_accent)
        sc_conghoa = score_conghoa(text_no_accent)
        sc_cmnd = SequenceMatcher(a=text_no_accent, b='GIAY CHUNG MINH NHAN DAN').ratio()

        #print(key,' ' ,sc_dkhk)
        #print(key,' ', sc_conghoa)  
    
        if sc_dkhk > max1:
            max1 = sc_dkhk
            box_dkhk = obj.four_points
            #print('1', key)
        if sc_conghoa > max2:
            max2 = sc_conghoa
            obj_conghoa = obj
            box_conghoa = obj.four_points
            #print('2', key)
        if sc_cmnd > max3:
            max3 = sc_cmnd
            box_cmnd = obj.four_points

    if obj_conghoa.key[-2:] == 'AM':
        width = box_conghoa[1][0][0] - box_conghoa[0][0][0]
        height = box_conghoa[3][0][1] - box_conghoa[0][0][1]
        topleft = [max(int(box_conghoa[0][0][0] - width/3),0), max(int(box_conghoa[0][0][1] - height/2),0)]
        topright = [min(int(box_conghoa[1][0][0] + width/7), copy_img.shape[1]), max(int(box_conghoa[1][0][1] - height/2), 0)]
        botleft = [max(int(box_dkhk[3][0][0] - width/3), 0), min(int(box_dkhk[3][0][1] + height*2.5), copy_img.shape[0])]
        botright = [min(int(botleft[0]+topright[0]-topleft[0]),copy_img.shape[1]), min(int(topright[1] + botleft[1]-topleft[1]), copy_img.shape[0])]

    else:
        width = (box_cmnd[1][0][0] - box_cmnd[0][0][0])*1.05
        height = (box_cmnd[3][0][1] - box_cmnd[0][0][1])*0.9

        topleft = [max(int(box_cmnd[0][0][0] - width/3),0), max(int(box_cmnd[0][0][1] - height/2),0)]
        topright = [min(int(box_cmnd[1][0][0] + width/7), copy_img.shape[1]), max(int(box_cmnd[1][0][1] - height/2), 0)]
        botleft = [max(int(box_dkhk[3][0][0] - width/3), 0), min(int(box_dkhk[3][0][1] + height*2.5), copy_img.shape[0])]
        botright = [min(int(botleft[0]+topright[0]-topleft[0]),copy_img.shape[1]), min(int(topright[1] + botleft[1]-topleft[1]), copy_img.shape[0])]


    #copy_img = cv2.circle(copy_img,(topleft[0], topleft[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(topright[0], topright[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(botleft[0], botleft[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(botright[0], botright[1]), 5, (0,255,0), -1)

    box = [[topleft], [topright], [botright], [botleft]]
    #print('box', box)
    #print(box)
    #warped =  four_point_transform(copy_img, box)
    box_rec = crop_image(copy_img, box)
    #print('rec', box_rec[0], box_rec[1])
    save_img = copy_img[int(box_rec[1]):int(box_rec[3]), int(box_rec[0]):int(box_rec[2])]

    corner, c = cal_corner(list_text_box, box_rec)

    if c >=5:
        save_img = imutils.rotate_bound(save_img, corner)
    
    #cv2.imshow('', save_img)
    #cv2.waitKey(0)
    cv2.imwrite('out.jpg', save_img)

def count_char_in_key(key):
    c = 0
    for i in key:
        if i>='a' and i<='y' or i>='A' and i<='B':
            c = c+1
    return c

def OCR_text(i, dt_boxes, copy_img, detector):
    # dic = {}
    # dic_o = {}
    # dic_s = {}
    #print('---------------')
    list_text_box = []

    for j, box in enumerate(dt_boxes):
        
        box = box.astype(np.int32).reshape((-1, 1, 2))      
        
        crop = four_point_transform(copy_img, box)
        #crop = imutils.resize(crop, height=32)
        
        box_rec = crop_image(copy_img, box)
        # Convert cv2 format to PIL
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        #cv2.imshow('', crop)
        #cv2.waitKey(0)
        cv2.imwrite('box{}/{}.jpg'.format(i, j), crop)
        im_pil = Image.fromarray(crop)
        pred = detector.predict(im_pil)     
        if list_text_box is not None:
            for text in list_text_box:
                if pred == text.key:
                    pred = pred + ' '

        #print(pred)    
        
        size = crop.shape[0] * crop.shape[1]
        obj = textbox(pred, box_rec, box, size, 'box{}/{}.jpg'.format(i, j))

        list_text_box.append(obj)

    return list_text_box

def cut_roi_cc(list_text_box, copy_img):

    max1 = 0
    max2 = 0

    for obj in list_text_box:
        text = obj.key
        text_no_accent = remove_accent(text)
        sc_ex = score_expired(text_no_accent)
        sc_conghoa = score_conghoa(text_no_accent)      

        #print(key,' ' ,sc_ex)
        #print(key,' ', sc_conghoa)    
        if sc_ex > max1:
            max1 = sc_ex
            obj_ex = obj
            #print('1', key)
        if sc_conghoa > max2:
            max2 = sc_conghoa
            obj_conghoa = obj
            #print('2', key)

    box_conghoa = obj_conghoa.four_points

    width_conghoa = box_conghoa[1][0][0] - box_conghoa[0][0][0]
    height_conghoa = box_conghoa[3][0][1] - box_conghoa[0][0][1]    
    
    if max1<25:
        maxx = 0
        for obj in list_text_box:
            text = obj.key
            text_no_accent = remove_accent(text)
            sc_Noithuongtru = score_Noithuongtru(text_no_accent)
            if sc_Noithuongtru > maxx:
                maxx = sc_Noithuongtru
                obj_Noithuongtru = obj

        box_ntt = obj_Noithuongtru.four_points

        topleft = [max(int(box_ntt[3][0][0]), 0), max(int(box_conghoa[0][0][1] - height_conghoa/2),0)]
        topright = [min(int(box_conghoa[1][0][0] + width_conghoa/7), copy_img.shape[1]), max(int(box_conghoa[1][0][1] - height_conghoa/2), 0)]
        botleft = [max(int(box_ntt[3][0][0]+height_conghoa/2), 0), min(int(box_ntt[3][0][1]+height_conghoa*2.5), copy_img.shape[0])]
        botright = [min(int(botleft[0]+topright[0]-topleft[0]),copy_img.shape[1]), min(int(topright[1] + botleft[1]-topleft[1]), copy_img.shape[0])]
        type_cut = 2
    else:    
        box_ex = obj_ex.four_points

        topleft = [max(int(box_ex[3][0][0]), 0), max(int(box_conghoa[0][0][1] - height_conghoa/2),0)]
        topright = [min(int(box_conghoa[1][0][0] + width_conghoa/7), copy_img.shape[1]), max(int(box_conghoa[1][0][1] - height_conghoa/2), 0)]
        botleft = [max(int(box_ex[3][0][0]+height_conghoa/2), 0), min(int(box_ex[3][0][1]+height_conghoa/2), copy_img.shape[0])]
        botright = [min(int(botleft[0]+topright[0]-topleft[0]),copy_img.shape[1]), min(int(topright[1] + botleft[1]-topleft[1]), copy_img.shape[0])]
        type_cut = 1
    #copy_img = cv2.circle(copy_img,(topleft[0], topleft[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(topright[0], topright[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(botleft[0], botleft[1]), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(botright[0], botright[1]), 5, (0,255,0), -1)

    box = [[topleft], [topright], [botright], [botleft]]
    #print('box', box)
    #print(box)
    #warped =  four_point_transform(copy_img, box)
    box_rec = crop_image(copy_img, box)
    #print('rec', box_rec[0], box_rec[1])
    save_img = copy_img[int(box_rec[1]):int(box_rec[3]), int(box_rec[0]):int(box_rec[2])]

    corner, c = cal_corner(list_text_box,box_rec)

    if c >=5:
        save_img = imutils.rotate_bound(save_img, corner)

    cv2.imwrite('out.jpg', save_img)

    return type_cut

def cal_corner(list_text_box, box_rec):
    count = 0
    sum_corner = 0
    c = 0
    for obj in list_text_box:
        #print(obj.four_points)
        #print(obj.four_points[0][0][0])
        if obj.four_points[0][0][0] > box_rec[0] and obj.four_points[0][0][1]>box_rec[1] and obj.four_points[2][0][0]<box_rec[2] and obj.four_points[2][0][1]<box_rec[3] and len(obj.key)>=2:
            point1 = [obj.four_points[0][0][0], obj.four_points[0][0][1]] 
            point2 = [obj.four_points[1][0][0], obj.four_points[1][0][1]]
            dis = distance(point1, point2)
            h = point2[1] - point1[1]
            sin = h/dis
            corner = -np.arcsin(sin)
            corner_deg = corner/np.pi*180
            #print(obj.key,' ', corner_deg)
            count = count+1
            if abs(corner_deg) > 3:
                c = c+1
            sum_corner = sum_corner + corner_deg
    corner = sum_corner/count
    return corner, c

def box_nearest_gioitinh_cc(obj_Gioitinh, list_text_box2):

    max_dis = (obj_Gioitinh.two_points[2] - obj_Gioitinh.two_points[0])*2

    for obj in list_text_box2:
        center_obj = [(obj.two_points[0]+obj.two_points[2])/2 , (obj.two_points[1]+obj.two_points[3])/2]
        center_Gt = [(obj_Gioitinh.two_points[0]+obj_Gioitinh.two_points[2])/2 , (obj_Gioitinh.two_points[1]+obj_Gioitinh.two_points[3])/2]
        dis = math.sqrt((center_Gt[0]-center_obj[0])**2 + (center_Gt[1]-center_obj[1])**2)
        if dis < max_dis:
            key = obj.key
            key_no_accent = remove_accent(key)
            if key_no_accent == 'Nam' or key_no_accent == 'Nu':
                return obj

def normalize_hometown_address(nguyenquan, dkhk):

    nguyenquan = change_format(nguyenquan)
    dkhk = change_format(dkhk)  

    #print('Change format:', nguyenquan,' ', dkhk)  

    nguyenquan1 = mapping(nguyenquan)
    dkhk1 = mapping(dkhk)
    # check whether it's Ho Chi Minh region
    pos = 0
    if nguyenquan1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(nguyenquan)-1):
            if (nguyenquan[i]=='P' and nguyenquan[i+1] in '0123456789') or (nguyenquan[i]=='P' and nguyenquan[i+2] in '0123456789'):
                pos = i
                #print(pos)
        nguyenquan = nguyenquan[pos:]
        
    if pos != 0:
        nguyenquan1 = mapping(nguyenquan)    
    pos = 0
    if dkhk1.find('TP Hồ Chí Minh') != -1:
        for i in range(len(dkhk)-1):
            if (dkhk[i]=='P' and dkhk[i+1] in '0123456789') or (dkhk[i]=='P' and dkhk[i+2] in '0123456789'):
                pos = i
                #print(pos)
        dkhk = dkhk[pos:]
    
    if pos != 0:
        dkhk1 = mapping(dkhk)
    
    return nguyenquan1, dkhk1

def mapping(key):
    maxx = 0
    res1 = ''
    with open('diachi.txt', 'r') as infile:
        for i in infile.readlines():
            ratio = SequenceMatcher(a=i,b=key).ratio()
            if ratio>maxx:
                maxx = ratio
                res1 = i

    #print('ratio:',key,' ',maxx)    
    if maxx < 0.5:
        return key
    return res1      

def score_of_cc_or_cmnd(list_test_box1):
    score = 0

    for obj in list_test_box1:
        text = obj.key
        no_accent = remove_accent(text)

        #if no_accent.find('Quoc tich') != -1:
        #    score += 1
        #if no_accent.find('Viet Nam') != -1:
        #    score += 1
        if no_accent.find('Ho va ten') != -1:
            score += 1
        if no_accent.find('Gioi tinh') != -1:
            score += 1
        #if no_accent.find('Noi thuong tru') != -1:
        #    score += 1
        if no_accent.find('Co gia tri den') != -1:
            score += 1
        if no_accent.find('CAN CUOC CONG DAN') != -1:
            score +=1 
        if no_accent.find('Quoc tich') != -1:
            score +=1
    return score

def change_format(key):
    if not (key.find('Xã') != -1 or key.find('xã')!=-1):
        #key_no_accent = remove_accent(key)
        pos_phuong = key.find('Phường ')

        if pos_phuong != -1:
            key = key[:pos_phuong] + 'P.' + key[pos_phuong+7:]
    
    if not (key.find('Huyện') != -1 or key.find('huyện')!=-1):
        #key_no_accent = remove_accent(key)
        pos_quan = key.find('Quận ')
        if pos_quan != -1:
            key = key[:pos_quan] + 'Q.' +key[pos_quan+5:]
    
    key = key.replace('Xã', '')
    key = key.replace('Huyện', '')
    key = key.replace('Thành phố', 'TP')
    pos1 = key.find('P.')
    
    if pos1 != -1 and pos1>0:
        if key[pos1-1]!='T':
            key = key[pos1:]

    pos2 = key.find('P. ')
    if pos2 != -1 and pos2>0:
        print(pos2)
        if key[pos2-1]!='T':
            key = key[pos2:]    
    return key

def normalize_name(key_name):

    key_name = finalize(key_name)
    key = remove_accent(key_name)
    key = str.lower(key)
    if 'ho ten' in key:
        key_name = key_name[6:]
    
    #delete space at first position

    while True:
        if key_name.find(' ') == 0:
            key_name = key_name[1:]
        else:
            break   

    #print(key_name)
    key_name = key_name.replace('-', ' ')
    s = key_name.split(' ')
    
    if remove_accent(s[0]) not in {'AN', 'ANH', 'AU', 'CAI', 'CHUNG', 'CO', 'CONG', 
    'CU', 'DAU', 'DOAN', 'DONG','DUONG', 'GIANG', 'HA', 'HAN', 'KHA', 'LA',
    'LIEU', 'LO', 'MA', 'MAU', 'ONG', 'PHI', 'PHU', 'QUANG', 'TONG', 'TRINH',
    'UNG', 'KIEU', 'LY', 'NGO', 'CHU', 'LAI'}:
        #print('HO', Ho)
        with open('ho.txt', 'r') as f:
            maxx = 0
            for i in f.readlines():
                name = remove_accent(i)
                name = str.upper(name)
                if name[:-1] == remove_accent(s[0]):
                    Ho = i       
                    Ho = str.upper(Ho)
                    s[0] = Ho[:-1]
        f.close()


    #print('SSS', s)
    for i in range(len(s)):
        if remove_accent(s[i]) == 'HUYEN':
            s[i] = 'HUYỀN'
        if remove_accent(s[i]) == 'HONG':
            s[i] = 'HỒNG'
        if remove_accent(s[i]) == 'HOANG':
            s[i] = 'HOÀNG'

    if s[0] in {'NGỎ', 'NGÕ', 'NGÓ', 'NGÒ'}:
        s[0] = 'NGÔ'
    if remove_accent(s[0]) == 'TE':
        s[0] = 'LÊ'
    
    for i in range(len(s)-1):
        if s[i] == 'THI' and len(s)>=3:
            s[i] = 'THỊ'
        if s[i] == 'ĂĂ' and len(s) >=3:
            s[i] = 'VĂN'
        if remove_accent(s[i]) == 'TUAN':
            s[i] = 'TUẤN'
        if remove_accent(s[i]) == 'HOÀNG':
            s[i] = 'HOÀNG'
    
    name = ''
    for i in range(len(s)):
        name = name + s[i] + ' '
    
    return name

def draw_box_id(list_text_box2, box_id, obj_name, copy_img, detector, obj_cmnd):
    
    w = obj_cmnd.two_points[2]-obj_cmnd.two_points[0]
    h = obj_cmnd.two_points[3]-obj_cmnd.two_points[1]
    
    if box_id != []:
        lean_w = box_id[3][0][0]-box_id[0][0][0]
    else:
        lean_w = obj_cmnd.four_points[3][0][0] - obj_cmnd.four_points[0][0][0]

    point1 = [int(obj_cmnd.four_points[3][0][0]+w/5), int(obj_cmnd.four_points[3][0][1])]
    point2 = [int(obj_cmnd.four_points[2][0][0]-w/11), int(obj_cmnd.four_points[2][0][1])]
    point4 = [int(point1[0]+ lean_w), int(obj_name.four_points[0][0][1]-h/7)]
    point3 = [int(point2[0]+ lean_w), int(obj_name.four_points[1][0][1]-h/7)]

    #print(copy_img.shape)
    #print(point1, ' ', point2,' ',point3,' ',point4)
    #copy_img = cv2.circle(copy_img,(int(point1[0]), int(point1[1])), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(int(point2[0]), int(point2[1])), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(int(point3[0]), int(point3[1])), 5, (0,255,0), -1)
    #copy_img = cv2.circle(copy_img,(int(point4[0]), int(point4[1])), 5, (0,255,0), -1)    

    box = [[point1], [point2], [point3], [point4]]

    warp = four_point_transform(copy_img, box)
    #warp = cv2.GaussianBlur(warp,(5,5),0)
    warp = cv2.cvtColor(warp, cv2.COLOR_BGR2RGB)

    im_pil = Image.fromarray(warp)
    pred = detector.predict(im_pil)
    #cv2.imshow('', warp)
    #cv2.waitKey(0)
    if count_num_in_key(pred) >= 9:
        return remove_char(pred) 
    else:
        return ''

def find_cmnd(list_text_box2):
    maxx = 0
    for obj in list_text_box2:
        s = 0
        key = obj.key 
        key = remove_accent(key)
        for i in {'GI', 'IA', 'AY', 'Y ', ' C', 'CH', 'HU', 'UN', 'NG', 'G ', ' M'
            ,'MI', 'IN', 'NH', 'H ', ' N', 'HA', 'AN', 'N ', ' D', 'DA'}:
            if key.find(i) !=-1:
                s += 1
        if s > maxx:
            maxx = s
            obj_cmnd = obj
    return obj_cmnd
