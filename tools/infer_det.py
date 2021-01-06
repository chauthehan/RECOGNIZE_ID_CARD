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
from tools.process_text import *
import cv2

from ppocr.utils.utility import initial_logger
logger = initial_logger()
from ppocr.utils.utility import enable_static_mode

# Vietocr
import matplotlib.pyplot as plt
from PIL import Image
import imutils

from vietocr.tool.predictor import Predictor
from vietocr.tool.config import Cfg

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

def paddle(img_path, config, exe, eval_prog, eval_fetch_list):
    config['Global']['infer_img'] = img_path
    test_reader = reader_main(config=config, mode='test')
    tackling_num = 0
    for data in test_reader():
        img_num = len(data)
        tackling_num = tackling_num + img_num
        logger.info("Number of images:%d", tackling_num)
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

            src_img = cv2.imread(img_name)              

            copy_img = src_img.copy()

            draw_det_res(dt_boxes, config, src_img, img_name) 

    return dt_boxes, copy_img

def main():
    config = program.load_config(FLAGS.config)
    program.merge_config(FLAGS.opt)
    #logger.info(config)

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

    # Detect box text

    img_path = config['Global'].get('infer_img')

    dt_boxes, copy_img = paddle(img_path, config, exe, eval_prog, eval_fetch_list)  

    #cut_img_path = cut_roi(dt_boxes, copy_img)
    #dt_boxes, copy_img = paddle(cut_img_path, config, exe, eval_prog, eval_fetch_list)  

    logger.info("Detect success!")

    logger.info("Begining ocr..")

    config_ocr = Cfg.load_config_from_name('vgg_seq2seq')
    config_ocr['weights'] = './my_weights/transformerocr.pth'
    config_ocr['cnn']['pretrained']=False
    config_ocr['device'] = 'cpu'
    config_ocr['predictor']['beamsearch']=False

    detector = Predictor(config_ocr)

    dic = {}
    dic_o = {}
    dic_s = {}
    import random

    for i, box in enumerate(dt_boxes):
        box = box.astype(np.int32).reshape((-1, 1, 2))
       
        crop = four_point_transform(copy_img, box)
        #box_rec = crop_image(copy_img, box)
        # Convert cv2 format to PIL
        crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
        
        im_pil = Image.fromarray(crop)
        pred = detector.predict(im_pil)     
        if dic is not None:
            for key in dic:
                if pred == key:
                    pred = pred + ' '       
        
        print(pred)
        dic[pred] = i
        dic_o[pred] = box
        #dic_s[pred] = crop.shape[0] * crop.shape[1]
    
    #print(dic_o)
    #exit()
    final_dic = {
        'Id': '',
        'Name': '',
        'Birth': '',
        'Sex' : '',
        'Hometown': '',
        'Date of expired': '',
        'Address': ''} 

    # check if the image is ID card or Citizen Card
    score = 0
    for key in dic:
        no_mark = remove_mark(key)

        if no_mark == 'Quoc tich':
            score += 1
        if no_mark == 'Viet Nam':
            score += 1
        if no_mark == 'Ho va ten':
            score += 1
        if no_mark == 'Gioi tinh':
            score += 1
        if no_mark == 'Noi thuong tru':
            score += 1
        if no_mark.find('Co gia tri den') != -1:
            score += 1
     
    # if 2 box appear to have 8 num, or 1 box has string 'CAN CUOC CONG DAN', than it mus be Citien card
        
    if score>=3:
    
    #-------------ID, Birth, ex---------------------
        list_key_remove = []
        birth_ex = [] 
        for key in dic:
            if count_num_in_key(key) in {7,8}:
                birth_ex.append(key)
                list_key_remove.append(key)
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
        #name_box = dic[name]
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
            no_mark_str = str.lower(no_mark_str)
            count = 0
            list_pos = []
            mark = True
            if no_mark_str.find('que') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('que'))
            if no_mark_str.find('quan') != -1:
                count = count + 1
                list_pos.append(no_mark_str.find('quan'))
            
            for i in range(len(list_pos)-1):
                if list_pos[i]>list_pos[i+1]:
                    mark = False 

            if count in {1, 2} and mark:
                address_box = dic[key1]
                list_key_remove.append(key1)
                
                
                pos = no_mark_str.find('que quan')
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
        cut_roi(dic, copy_img, dic_o)

        dt_boxes, copy_img = paddle('out.jpg', config, exe, eval_prog, eval_fetch_list)  
        
        # OCR again 
        dic = {}
        dic_o = {}
        dic_s = {}
        
        for i, box in enumerate(dt_boxes):
            box = box.astype(np.int32).reshape((-1, 1, 2))
        
            crop = four_point_transform(copy_img, box)
            box_rec = crop_image(copy_img, box)
            # Convert cv2 format to PIL
            crop = cv2.cvtColor(crop, cv2.COLOR_BGR2RGB)
            #crop = imutils.resize(crop, height=32)
            
            cv2.imwrite('box/{}.jpg'.format(i),crop)
            
            im_pil = Image.fromarray(crop)
            pred = detector.predict(im_pil)     
            if dic is not None:
                for key in dic:
                    if pred == key:
                        pred = pred + ' '       
            
            print(pred)
            dic[pred] = box_rec
            dic_o[pred] = box
            dic_s[pred] = crop.shape[0] * crop.shape[1]

        #---------------ID, Birth--------------------
        dic_s_birth = 0
        birth_key = ''
        for key in dic:
            #print(key)
            count = count_num_in_key(key)
            if count  == 8: #and check:
                # get the birth box
                birth_key = key
                final_dic['Birth'] = process_birth(key)
                birth_box = dic[key]
                # get the size of birth box
                dic_s_birth = dic_s[key]

            if (key[:2]=='19' and count==4):
                birth_key = key
                k = remove_mark(key)
                k = remove_char_birth(k)
                final_dic['Birth'] = key
                birth_box = dic[key]
                # get the size of birth box
                dic_s_birth = dic_s[key]*2

            if count >= 9:
                # remove unrelated character
                key = remove_char(key)
                key = key[-9:]
                final_dic['Id'] = key

            if count == 7:
                birth_key = key
                k = remove_mark(key)
                k = remove_char_birth(k)
                final_dic['Birth'] = k
                birth_box = dic[key]
                # get the size of birth box
                dic_s_birth = dic_s[key]

        # if the size of a box is smaller than some thresh, than delete it
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

        name_no_mark = remove_mark(name)
        for j, i in enumerate(name_no_mark[1:]):
            if i>='A' and i<='Y':
                pos = j
                break 

        final_dic['Name'] = name[pos:]

        #delete box has been already done
        list_key_remove = []

        for key in dic:
            if dic[key][1] < birth_box[1]:
                list_key_remove.append(key)
            
        #print('remove2', list_key_remove)
        for key in list_key_remove:
            del dic[key]
        del dic[birth_key]

        #--------------Remove wrong box-----------------

        #print('BEFORE ' ,dic)

        print(dic_s)
        list_key_remove = []
        for key in dic:
            if dic_s[key] < int(dic_s_birth/2.15):
                list_key_remove.append(key)
        #print('REMOVE', list_key_remove)
        for key in list_key_remove:
            del dic[key]
        
        #print('AFTER ', dic)
        print('-------------')

        # ---------HOMETOWN-----------

        hometown = ''
        nguyenquan = ''
        count = 0
        address = ''
        keys_above_dkhk = {}

        maxx = 0
        for key in dic:
            key_no_mark = remove_mark(key)
            key_no_mark = str.lower(key_no_mark)
            #print(key,' ', score_nguyenquan(key_no_mark))
        
            if score_nguyenquan(key_no_mark)>maxx:
                maxx = score_nguyenquan(key_no_mark)               
                nguyenquan = key
                box_nguyenquan = dic[key]
        
        # delete box left of nguyenquan
        remove = ''
        for key in dic:
            if dic[key][2] < box_nguyenquan[0]:
                remove = key

        if remove != '':
            del dic[remove]
  
        # remove box 'sinh ngay'
        sinhngay = None
        for key in dic:
            if dic[key][2] > dic[nguyenquan][0] and dic[key][2]<dic[nguyenquan][2] and dic[key][1]<dic[nguyenquan][1]:
                sinhngay = key
        if sinhngay is not None:
            del dic[sinhngay]

        maxx = 0

        for key in dic:
            # if box has at least 3 word in Noi DKHK thuong tru, 
            # than it must be address box
            no_mark_str = remove_mark(key)
            #print(key, ' ', score_dkhk(no_mark_str))
            
            if score_dkhk(no_mark_str)>maxx:
                
                maxx = score_dkhk(no_mark_str)
                dkhk = key

        if len(nguyenquan[12:]) > 3: 
            nguyenquan2 = nguyenquan[12:]
            nearest_hometown = nguyenquan
        else:
            nearest_hometown = box_nearest(nguyenquan, dic)
            nguyenquan2 = nearest_hometown

        #print('nearesthometown', nearest_hometown)
        #print('nguyeqnan', nguyenquan)

        hometown = hometown + nguyenquan2
        del dic[nearest_hometown]
        if nearest_hometown != nguyenquan:
            del dic[nguyenquan]
        
        #print('20: ', dkhk[20:])
        
        if len(dkhk[20:]) > 2:
            
            nearest_address = dkhk[20:]
            nearest_address_raw = dkhk
        else:
            nearest_address_raw = box_nearest(dkhk, dic)
            nearest_address = nearest_address_raw
        
        address = address + nearest_address

        for key in dic:
            if dic[key][1]<dic[dkhk][1] and key != nearest_address_raw:
                keys_above_dkhk[key] = dic[key]

        if len(keys_above_dkhk) != 0:
            hometown2 = sort_key_left2right(keys_above_dkhk)
            hometown = hometown + ', '+hometown2
                

        for key in keys_above_dkhk:
            del dic[key]
        del dic[nearest_address_raw]
        if nearest_address_raw != dkhk:
            del dic[dkhk]

        print('-----------------------')
        #print('DIC', dic)

        if len(dic) != 0:
            address2 = sort_key_left2right(dic)
            address = address + ', ' + address2     


        final_dic['Address'] = address
        final_dic['Hometown'] = hometown     
        
   #----------------------------------------------


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
