# Copyright (c) 2020 PaddlePaddle Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

#python3 tools/infer_det.py -c configs/det/det_r18_vd_db_v1.1.yml -o Global.checkpoints="./output/det_db/best_accuracy" PostProcess.box_thresh=0.1 PostProcess.unclip_ratio=1.5 Global.infer_img="/home/han/Downloads/Telegram Desktop/110x.jpg"
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import numpy as np
from copy import deepcopy
import json

import os
import sys
__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '..')))


def set_paddle_flags(**kwargs):
    for key, value in kwargs.items():
        if os.environ.get(key, None) is None:
            os.environ[key] = str(value)


# NOTE(paddle-dev): All of these flags should be
# set before `import paddle`. Otherwise, it would
# not take any effect.
set_paddle_flags(
    FLAGS_eager_delete_tensor_gb=0,  # enable GC to save memory
)

from paddle import fluid
from ppocr.utils.utility import create_module, get_image_file_list
import program
from ppocr.utils.save_load import init_model
from ppocr.data.reader_main import reader_main
import cv2

from ppocr.utils.utility import initial_logger
logger = initial_logger()
from ppocr.utils.utility import enable_static_mode

# Vietocr
import matplotlib.pyplot as plt
from PIL import Image

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

def crop_image(I, box):

    box[0][0][0] = box[0][0][0] - 5
    box[0][0][1] = box[0][0][1] - 2
    box[1][0][0] = box[1][0][0] + 5
    box[1][0][1] = box[1][0][1] - 2
    box[2][0][0] = box[2][0][0] + 5
    box[2][0][1] = box[2][0][1] + 2
    box[3][0][0] = box[3][0][0] - 5
    box[3][0][1] = box[3][0][1] + 2
    
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

    # Go over the points in the image if thay are out side of the emclosing rectangle put zero
    # if not check if thay are inside the polygon or not
    cropedImage = np.zeros_like(I)
    for y in range(0,I.shape[0]):
        for x in range(0, I.shape[1]):

            if x < minX or x > maxX or y < minY or y > maxY:
                continue

            if cv2.pointPolygonTest(np.asarray(box),(x,y),False) >= 0:
                cropedImage[y, x, 0] = I[y, x, 0]
                cropedImage[y, x, 1] = I[y, x, 1]
                cropedImage[y, x, 2] = I[y, x, 2]

    # Now we can crop again just the envloping rectangle
    finalImage = cropedImage[minY:maxY,minX:maxX]

    return finalImage, [minX, minY, maxX, maxY]

def draw_det_res(dt_boxes, config, img, img_name):
    if len(dt_boxes) > 0:
        src_im = img
        for box in dt_boxes:
            box = box.astype(np.int32).reshape((-1, 1, 2))
            cv2.polylines(src_im, [box], True, color=(255, 255, 0), thickness=2)
        save_det_path = os.path.dirname(config['Global'][
            'save_res_path']) + "/det_results/"
        if not os.path.exists(save_det_path):
            os.makedirs(save_det_path)
        save_path = os.path.join(save_det_path, os.path.basename(img_name))
        cv2.imwrite(save_path, src_im)
        logger.info("The detected Image saved in {}".format(save_path))

def remove_mark(str):
    new_str = ''
    for i in str:
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
        
def Key(x):
    return x[0]

def same_rows(key1, dic):
    box1 = dic[key1]
    min_dis = 1000
    for key2 in dic:
        if key1 == key2:
            continue
        box2 = dic[key2]
        
        if abs((box2[3] + box2[1])/2-(box1[3]+box1[1])/2) < min_dis:
            min_dis = abs((box2[3] + box2[1])/2-(box1[3]+box1[1])/2)
            key_same = key2 
    
    return key_same

def under_rows(key1, dic):
    box1 = dic[key1]
    lst = []
    for key2 in dic:
        box2 = dic[key2]
        if box2[0] < box1[0]-(box1[3]-box1[1]):
            continue
       
        if (box1[3]<box2[3]):
            lst.append(box2)
    lst.sort(key=Key)

    return lst        

def remove_char(key):
    id = ''
    for i in key:
        if i>='0' and i<='9':
            id = id+i
    return id

def remove_low_char(key):
    mark_pos = 0
    key_no_mark = remove_mark(key)
    for i, char in enumerate(key_no_mark):
        if not (char>='A' and char<='Y' or char==' '):
            mark_pos = i
    if mark_pos != 0:
        return key[mark_pos+1:]
    else:
        return key[mark_pos:]
   

def process_birth(key):
    birth = ''
    for char in key:
        if char>='0' and char<='9':
            birth = birth + char 
    
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
    if key == '':
        return ''
    key_no_mark = remove_mark(key)
    i = -1
    while True:
        i = i+1

        char = key_no_mark[i]
        
        if not (('a'<=char and 'y'>=char) or ('A'<=char and 'Y'>=char)or ('0'<=char and '9'>=char)):

            key = key[:i] + key[i+1:]
            key_no_mark = remove_mark(key)
            i = i-1
        else:
            break

    if key == '':
        return ''

    i = len(key)
    key_no_mark = remove_mark(key)
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
    count = 0
    # check = False
    for i in key:
        if i >= '0' and i <= '9':
            count = count+1
    return count

def count_upper_in_key(key):
    count = 0
    for i in key:
        if i>='A' and i<='Y':
            count += 1
    return count

def main():
    config = program.load_config(FLAGS.config)
    program.merge_config(FLAGS.opt)
    logger.info(config)

    # check if set use_gpu=True in paddlepaddle cpu version
    use_gpu = config['Global']['use_gpu']
    program.check_gpu(use_gpu)

    place = fluid.CUDAPlace(0) if use_gpu else fluid.CPUPlace()
    exe = fluid.Executor(place)

    det_model = create_module(config['Architecture']['function'])(params=config)

    startup_prog = fluid.Program()
    eval_prog = fluid.Program()
    with fluid.program_guard(eval_prog, startup_prog):
        with fluid.unique_name.guard():
            _, eval_outputs = det_model(mode="test")
            fetch_name_list = list(eval_outputs.keys())
            eval_fetch_list = [eval_outputs[v].name for v in fetch_name_list]

    eval_prog = eval_prog.clone(for_test=True)
    exe.run(startup_prog)

    # load checkpoints
    checkpoints = config['Global'].get('checkpoints')
    if checkpoints:
        path = checkpoints
        fluid.load(eval_prog, path, exe)
        logger.info("Finish initing model from {}".format(path))
    else:
        raise Exception("{} not exists!".format(checkpoints))

    save_res_path = config['Global']['save_res_path']
    if not os.path.exists(os.path.dirname(save_res_path)):
        os.makedirs(os.path.dirname(save_res_path))

    with open(save_res_path, "wb") as fout:
        test_reader = reader_main(config=config, mode='test')
        tackling_num = 0
        for data in test_reader():
            img_num = len(data)
            tackling_num = tackling_num + img_num
            logger.info("tackling_num:%d", tackling_num)
            img_list = []
            ratio_list = []
            img_name_list = []
            for ino in range(img_num):
                img_list.append(data[ino][0])
                ratio_list.append(data[ino][1])
                img_name_list.append(data[ino][2])

            img_list = np.concatenate(img_list, axis=0)
            outs = exe.run(eval_prog,\
                feed={'image': img_list},\
                fetch_list=eval_fetch_list)

            global_params = config['Global']
            postprocess_params = deepcopy(config["PostProcess"])
            postprocess_params.update(global_params)
            postprocess = create_module(postprocess_params['function'])\
                (params=postprocess_params)
            if config['Global']['algorithm'] == 'EAST':
                dic = {'f_score': outs[0], 'f_geo': outs[1]}
            elif config['Global']['algorithm'] == 'DB':
                dic = {'maps': outs[0]}
            elif config['Global']['algorithm'] == 'SAST':
                dic = {
                    'f_score': outs[0],
                    'f_border': outs[1],
                    'f_tvo': outs[2],
                    'f_tco': outs[3]
                }
            else:
                raise Exception(
                    "only support algorithm: ['EAST', 'DB', 'SAST']")
            dt_boxes_list = postprocess(dic, ratio_list)
            for ino in range(img_num):
                dt_boxes = dt_boxes_list[ino]
                img_name = img_name_list[ino]
                dt_boxes_json = []
                for box in dt_boxes:
                    tmp_json = {"transcription": ""}
                    tmp_json['points'] = box.tolist()
                    dt_boxes_json.append(tmp_json)
                otstr = img_name + "\t" + json.dumps(dt_boxes_json) + "\n"
                fout.write(otstr.encode())
                src_img = cv2.imread(img_name)
                copy_img = src_img.copy()

                draw_det_res(dt_boxes, config, src_img, img_name)

    logger.info("success!")

    logger.info("Begining ocr..")

    config_ocr = Cfg.load_config_from_name('vgg_transformer')
    config_ocr['weights'] = './weights/transformerocr.pth'
    #config['weights'] = 'https://drive.google.com/uc?id=13327Y1tz1ohsm5YZMyXVMPIOjoOA0OaA'
    config_ocr['cnn']['pretrained']=False
    config_ocr['device'] = 'cpu'
    config_ocr['predictor']['beamsearch']=False

    detector = Predictor(config_ocr)

    dic = {}
    dic_o = {}

    for box in dt_boxes:
        box = box.astype(np.int32).reshape((-1, 1, 2)) 
        
        crop, box_rec = crop_image(copy_img, box)

        # Convert cv2 format to PIL
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        im_pil = Image.fromarray(crop)
        pred = detector.predict(im_pil)
        
        if dic is not None:
            for key in dic:
                if pred == key:
                    pred = pred + ' '
        
        dic[pred] = box_rec
        dic_o[pred] = box
    #print(dic)    


    final_dic = {
        'Id': '',
        'Name': '',
        'Birth': '',
        'Sex' : '',
        'Hometown': '',
        'Date of expired': '',
        'Address': ''} 

    # check if the image is ID card or Citizen Card
    count_date = 0
    can_cuoc = 0
    for key in dic:
        count = count_num_in_key(key)
        if count in {7, 8}:
            count_date += 1
        no_mark = remove_mark(key)

        if no_mark == 'CAN CUOC CONG DAN':
            can_cuoc += 1
        
    # if 2 box appear to have 8 num, or 1 box has string 'CAN CUOC CONG DAN', than it mus be Citien card
        
    if count_date ==  2 or can_cuoc==1:
    
    #-------------ID, Birth, ex---------------------
        list_key_remove = []
        birth_ex = [] 
        for key in dic:
            if count_num_in_key(key) in {7,8}:
                birth_ex.append(key)
                list_key_remove.append(key)
            #                  and dic[key][2]>int(src_img.shape[1]/2):
                
            #     key_no_mark = remove_char(key)
            #     key_no_mark = process_birth(key_no_mark)
            #     final_dic['Birth'] = key_no_mark
            #     birth_box = dic[key]
            #     list_key_remove.append(key)
            #     continue
            # if count_num_in_key(key) in {7,8} and dic[key][0]<int(src_img.shape[1]/2):
            #     #print(key)
            #     key_no_mark = remove_char(key)
            #     #print(key())
            #     key_no_mark = process_birth(key_no_mark) 
            #     #print(key)
            #     final_dic['Date of expired'] = key_no_mark
            #     ex_box = dic[key]
            #     list_key_remove.append(key)
            if count_num_in_key(key) > 8:
                key_no_mark = remove_char(key)
                final_dic['Id'] = key_no_mark 
                list_key_remove.append(key)
        
        copy_birth_ex = []
        copy_birth_ex.append(birth_ex[0])
        copy_birth_ex.append(birth_ex[1])

        birth_ex[0] = remove_char(birth_ex[0])
        birth_ex[0] = process_birth(birth_ex[0])
        birth_ex[1] = remove_char(birth_ex[1])
        birth_ex[1] = process_birth(birth_ex[1])

        if dic[copy_birth_ex[0]][0] < dic[copy_birth_ex[1]][1]:
            final_dic['Date of expired'] = birth_ex[0]
            final_dic['Birth'] = birth_ex[1]
            birth_box = dic[copy_birth_ex[1]]
        else:
            final_dic['Date of expired'] = birth_ex[1]
            final_dic['Birth'] = birth_ex[0]
            birth_box = dic[copy_birth_ex[0]]   

    #-------------------NAME---------------------
        bottom = 0
        for key in dic:
            if dic[key][1] < birth_box[1]:
                
                key_no_mark = remove_mark(key)
                count = count_upper_in_key(key_no_mark)

                if count >= 3:
                    if dic[key][1] > bottom:
                        bottom = dic[key][1]
                        name = key
        final_dic['Name'] = name
        name_box = dic[name]
        list_key_remove.append(name)

        for key in list_key_remove:
            del dic[key]

    #-------------------Address---------------------
        list_key_remove = []

        for key1 in dic:
            # if box has at least 3 word in Noi DKHK thuong tru, 
            # than it must be address box
            no_mark_str = remove_mark(key1)
            count = 0
            list_pos = []
            mark = True
            if no_mark_str.find('Noi') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('Noi'))
            if no_mark_str.find('thuong') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('thuong'))
            if no_mark_str.find('tru') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('tru'))
            
            for i in range(len(list_pos)-1):
                if list_pos[i]>list_pos[i+1]:
                    mark = False 

            if count in {2, 3} and mark:
                address_box = dic[key1]
                list_key_remove.append(key1)
                
                
                pos = no_mark_str.find('Noi thuong tru')
                address_str = key1[pos+15:]
                
                same = ''
                if len(address_str) == 0:

                    same = same_rows(key1, dic)

                    address_str = address_str + same + ', '

                    list_key_remove.append(same)
                else:
                    address_str = address_str + ', '
                
                under = under_rows(key1, dic)

                for box_under in under:
                    for key in dic:
                        if box_under == dic[key] and key != same:
                            address_str = address_str + key
                            list_key_remove.append(key)

                final_dic['Address'] = address_str
        
        #delete box has been already done
        for key in list_key_remove:
            del dic[key]      

     #----------------------------------------------------------   
    #-------------------Hometown---------------------
        list_key_remove = []

        for key1 in dic:
            # if box has at least 3 word in Noi DKHK thuong tru, 
            # than it must be address box
            no_mark_str = remove_mark(key1)
            count = 0
            list_pos = []
            mark = True
            if no_mark_str.find('Que') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('Que'))
            if no_mark_str.find('quan') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('quan'))
            
            for i in range(len(list_pos)-1):
                if list_pos[i]>list_pos[i+1]:
                    mark = False 

            if count in {1, 2} and mark:
                address_box = dic[key1]
                list_key_remove.append(key1)
                
                
                pos = no_mark_str.find('Que quan')
                hometown = key1[pos+10:]
                
                same = ''
                if len(hometown) == 0:

                    same = same_rows(key1, dic)

                    hometown = hometown + same + ', '

                    list_key_remove.append(same)
                else:
                    hometown = hometown + ', '
                
                under = under_rows(key1, dic)

                for box_under in under:
                    for key in dic:
                        if box_under == dic[key] and key != same:
                            hometown = hometown + key
                            list_key_remove.append(key)

                final_dic['Hometown'] = hometown 
        
        #delete box has been already done
        for key in list_key_remove:
            del dic[key]
     #----------------------------------------------------------   
        list_key_remove = []
        for key in dic:
            if birth_box[1] > dic[key][1]:
                list_key_remove.append(key)
        for key in list_key_remove:
            del dic[key]
        
        for key in dic:
            key_no_mark = remove_mark(key)

            if key_no_mark.find('Nu') != -1:
                final_dic['Sex'] = 'Nữ'
        if final_dic['Sex'] == '':
            final_dic['Sex'] = 'Nam'
    else:
        
    
        #---------------ID, Birth--------------------
        for key in dic:
            count = count_num_in_key(key)
            if count in {7, 8}: #and check:
                # get the birth box
                
                final_dic['Birth'] = key
                birth_box = dic[key]
                # get the size of birth box
                birth_w = dic[key][2]-dic[key][0]
                birth_h = dic[key][3]-dic[key][1]
            if count > 8:
                # get the id box
                #id_box = dic[key]
                # remove unrelated character
                key = remove_char(key)
                final_dic['Id'] = key
        # if the size of a box is smaller than some thresh, than delete it

        #--------------Remove wrong box-----------------

        print('BEFORE ' ,dic)
        list_key_remove = []
        for key in dic:
            if dic[key][2]-dic[key][0] < birth_w*0.4 or dic[key][3]-dic[key][1]<birth_h*13/18:
                list_key_remove.append(key)
        for key in list_key_remove:
            del dic[key]
        
        print('AFTER ', dic)
        print('-------------')

        # ------------ADDRESS----------------------

        list_key_remove = []

        for key1 in dic:
            # if box has at least 3 word in Noi DKHK thuong tru, 
            # than it must be address box
            no_mark_str = remove_mark(key1)
            count = 0
            list_pos = []
            mark = True
            if no_mark_str.find('Noi') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('Noi'))
            if no_mark_str.find('DKHK') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('DKHK'))
            if no_mark_str.find('thuong') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('thuong'))
            if no_mark_str.find('tru') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('tru'))
            
            for i in range(len(list_pos)-1):
                if list_pos[i]>list_pos[i+1]:
                    mark = False 

            if count in {3, 4} and mark:
                address_box = dic[key1]
                list_key_remove.append(key1)
                
                
                pos = no_mark_str.find('Noi DKHK thuong tru')
                address_str = key1[pos+20:]
                
                same = ''
                if len(address_str) == 0:

                    same = same_rows(key1, dic)

                    address_str = address_str + same + ', '

                    list_key_remove.append(same)
                else:
                    address_str = address_str + ', '
                
                under = under_rows(key1, dic)

                for box_under in under:
                    for key in dic:
                        if box_under == dic[key] and key != same:
                            address_str = address_str + key
                            list_key_remove.append(key)

                final_dic['Address'] = address_str
        
        #delete box has been already done
        for key in list_key_remove:
            del dic[key]

        # ----------NAME-----------
        # if the box has more than 3 upper character, than it must be the box name

        bottom = 0
        for key in dic:
            if dic[key][1] < birth_box[1]:
                
                key_no_mark = remove_mark(key)
                count = count_upper_in_key(key_no_mark)

                if count >= 3:
                    if dic[key][1] > bottom:
                        bottom = dic[key][1]
                        name = key
        name_box = dic[name]
        
        if (abs(name_box[0] - address_box[0]) < (birth_box[2]-birth_box[0])*1/4) and (abs(birth_box[1] - name_box[3])>(birth_box[3]-birth_box[1])*4/5):
                
            # Cut head of box name base on the length of box birth
            name_o_box = dic_o[name]
            name_o_box[0][0][0] = name_o_box[0][0][0] + (birth_box[2]-birth_box[0])*2/3
            name_o_box[3][0][0] = name_o_box[3][0][0] + (birth_box[2]-birth_box[0])*2/3
            
            # OCR again with new box
            crop, box_rec = crop_image(copy_img, name_o_box)

            # Convert cv2 format to PIL
            crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            im_pil = Image.fromarray(crop)
            pred = detector.predict(im_pil)
            dic[pred] = box_rec 

            final_dic['Name'] = pred
        else:
            final_dic['Name'] = name
        


        #delete box has been already done
        list_key_remove = []
        sinhngay = same_rows(final_dic['Birth'], dic)
        del dic[sinhngay]

        for key in dic:
            if dic[key][1] < birth_box[1]:
                list_key_remove.append(key)
        for key in list_key_remove:
            del dic[key]
        del dic[final_dic['Birth']]

        # ---------HOMETOWN-----------
        hometown = ''
        count = 0
        print('FINAL', dic)
        for key in dic:
            key_no_mark = remove_mark(key)
            if key_no_mark.find('Nguyen quan') != -1:
                nguyenquan = key
        
        pos = remove_mark(nguyenquan).find('Nguyen quan')
        hometown = nguyenquan[pos+12:]
        
        same = ''
        if len(hometown) == 0:

            same = same_rows(nguyenquan, dic)
            print('same', same)
            hometown = hometown + same + ', '
    
        else:
            hometown = hometown + ', '
        
        under = under_rows(nguyenquan, dic)

        for box_under in under:
            for key in dic:
                if box_under == dic[key] and key != same:
                    print('........', key)

                    hometown = hometown + key
        

        final_dic['Hometown'] = hometown   
        final_dic['Birth'] = process_birth(final_dic['Birth'])
    #---------------------------------


    print('-------------------------------------')
    print('Id number: ', finalize(final_dic['Id']))
    print('Name: ', finalize(final_dic['Name']))
    print('Date of birth: ', finalize(final_dic['Birth']))
    print('Hometown: ', finalize(final_dic['Hometown']))
    print('Address: ', finalize(final_dic['Address']))
    print('Date of expired: ', finalize(final_dic['Date of expired']))
    print('Sex: ', finalize(final_dic['Sex']))
    print('-------------------------------------')
    logger.info('Done!')

    
if __name__ == '__main__':
    enable_static_mode()
    parser = program.ArgsParser()
    FLAGS = parser.parse_args()
    main()
