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

#python3 tools/infer_det.py -c configs/det/det_r18_vd_db_v1.1.yml -o Global.checkpoints="./output/det_db/best_accuracy" PostProcess.box_thresh=0.1 PostProcess.unclip_ratio=1.5"
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
from tools.identify_text import *
#from tools.identify_text_cc import *
#from tools.utils import *
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
import random


class textbox:
    def __init__(self, key, two_points, four_points, size, name_img):
        self.key = key
        self.two_points = two_points # describe text box by 2 points rectangle
        self.four_points = four_points # describe text box by 4 points quadrilateral
        self.size = size
        self.name_img = name_img

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
        #logger.info("The detected Image saved in {}".format(save_path))

def paddle(img_path, config, exe, eval_prog, eval_fetch_list):
    config['Global']['infer_img'] = img_path
    test_reader = reader_main(config=config, mode='test')
    tackling_num = 0
    for data in test_reader():
        img_num = len(data)
        tackling_num = tackling_num + img_num
        #logger.info("Number of images:%d", tackling_num)
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

    config_ocr = Cfg.load_config_from_name('vgg_seq2seq')
    config_ocr['weights'] = './my_weights/best.pth'
    #config_ocr['weights'] = './2-95,89.pth'
    config_ocr['cnn']['pretrained']=False
    config_ocr['device'] = 'cpu'
    config_ocr['predictor']['beamsearch']=False

    detector = Predictor(config_ocr)
    # Detect box text

    #for i in range(9, 400):
    for i in range(557, 620):
        img_path = 'test/' + str(i) + '.jpg'
        if not os.path.exists(img_path):
            img_path = 'test/' + str(i) + '.png'
        if not os.path.exists(img_path):
            continue
        #img_path = '/home/han/Documents/cmnd/recognize_id_card/akhoa.jpg'
      
        #print('pass')

        # i = -1
        # while True:
        #     i += 1
        #     try:
        logger.info("Begining detect id card..")
        dt_boxes, ori_img = paddle(img_path, config, exe, eval_prog, eval_fetch_list)
        logger.info("Detect success!")

        logger.info("Begining ocr..")
        #cv2.imshow('', ori_img)
        #cv2.waitKey(0)
        list_text_box1 = OCR_text(1, dt_boxes, ori_img, detector)
        final_dic = {
            'Id': '',
            'Name': '',
            'Birth': '',
            'Sex' : '',
            'Hometown': '',
            'Date of expired': '',
            'Address': ''} 

        # check if the image is ID card or Citizen Card

        score = score_of_cc_or_cmnd(list_text_box1)
            
        # if 2 box appear to have 8 num, or 1 box has string 'CAN CUOC CONG DAN', than it mus be Citien card
        if score>=1:
            print('[INFO] This is a Citizenship card!')

            type_cut = cut_roi_cc(list_text_box1, ori_img)
            dt_boxes, copy_img = paddle('out.jpg', config, exe, eval_prog, eval_fetch_list)  

            # OCR again         
            list_text_box2 = OCR_text(1, dt_boxes, copy_img, detector)

            # Find Id text
            final_dic['Id'], obj_id = find_id_text_cc(list_text_box2, detector)

            # Find box 'Quoc tich'
            obj_quoctich_dantoc = find_box_Quoctich_Dantoc(list_text_box2)
            VietNamdantoc = find_VietNam_dantoc(list_text_box2, obj_quoctich_dantoc)

            #print('QUOCTIChDANTOC', obj_quoctich_dantoc.key)

            # Find birth text
            final_dic['Birth'], obj_birth = find_birth_text_cc(list_text_box2, obj_quoctich_dantoc, copy_img)
            
            # Remove wrong box 
            list_text_box2 = remove_wrong_box_cc(list_text_box2, obj_id)

            # Find name text
            final_dic['Name'] = find_name_text_cc(list_text_box2, obj_quoctich_dantoc, VietNamdantoc, obj_id, copy_img)

            
            # Find date of expired
            if type_cut == 2:
                final_dic['Date of expired'], obj_expired = '', None
            else:
                final_dic['Date of expired'], obj_expired = find_key_expired(list_text_box2, obj_birth)

            # Find sex
            final_dic['Sex'], obj_Gioitinh, obj_nam_or_nu = find_sex(list_text_box2)

            if VietNamdantoc is not None and obj_nam_or_nu is None and obj_Gioitinh is None:
                final_dic['Sex'] = find_gioitinh_base_vietnam(list_text_box2, VietNamdantoc, obj_quoctich_dantoc)

            # Delete box has been already  processed

            list_text_box2 = delete_box_processed_cc(list_text_box2, obj_Gioitinh, obj_nam_or_nu, obj_quoctich_dantoc, obj_expired, obj_birth, VietNamdantoc, type_cut)
            
            for obj in list_text_box2:
                print('left', obj.key)
            # find hometown and address
            final_dic['Hometown'], final_dic['Address'] = find_hometown_address_text_cc(list_text_box2)

            print('Final dic: ', final_dic)
        else:
            print('[INFO] This is a Identification Card!')
            cut_roi(list_text_box1, ori_img)

            dt_boxes, copy_img = paddle('out.jpg', config, exe, eval_prog, eval_fetch_list)  
            
            # OCR again         
            list_text_box2 = OCR_text(1, dt_boxes, copy_img, detector)
            
            # Find Id text
            final_dic['Id'], obj_id = find_id_text(list_text_box2, detector)
            
            box_id = []
            if obj_id is not None:
                box_id = obj_id.four_points
            # Find birth text
            final_dic['Birth'], birth_size, obj_birth  = find_birth_text(list_text_box2, obj_id)
            
            # Find cmnd
            obj_cmnd = find_cmnd(list_text_box2)
            # Remove wrong box
            list_text_box2 = remove_wrong_box(list_text_box2, obj_id, obj_birth, birth_size, obj_cmnd)
            
            # Find name text
            
            final_dic['Name'], obj_name = find_name_text(list_text_box2, obj_id, obj_birth, obj_cmnd, detector, copy_img)
            
            if (final_dic['Id'] == remove_char(final_dic['Birth']) or len(final_dic['Id'])<9) and obj_name is not None:
                final_dic['Id'] = draw_box_id(list_text_box2, box_id, obj_name, copy_img, detector, obj_cmnd)

            # Delete box has been already processed
            
            list_text_box2 = delete_box_processed(list_text_box2, obj_birth.two_points)
            
            # find hometown and address
            for obj in list_text_box2:
                print('left', obj.key)
            
            final_dic['Hometown'], final_dic['Address'] = find_hometown_address_text(list_text_box2)  
        
            #    break
            # except:
            #     if i == 0:
            #         ori_img = imutils.rotate_bound(ori_img, -90)
            #         cv2.imwrite('{}.jpg'.format(i), ori_img)
            #         img_path = '{}.jpg'.format(i)
            #     elif i ==1:
            #         ori_img = imutils.rotate_bound(ori_img, 180)
            #         cv2.imwrite('{}.jpg'.format(i), ori_img)
            #         img_path = '{}.jpg'.format(i)
            #     elif i ==2:
            #         ori_img = imutils.rotate_bound(ori_img, 90)
            #         cv2.imwrite('{}.jpg'.format(i), ori_img)
            #         img_path = '{}.jpg'.format(i)                                       
    #----------------------------------------------
        print('-------------------------------------')
        print('Id number: ', final_dic['Id'])
        print('Name: ', final_dic['Name'])
        print('Sex: ', final_dic['Sex'])
        print('Date of birth: ', final_dic['Birth'])
        print('Hometown: ', final_dic['Hometown'])
        print('Address: ', final_dic['Address'])
        print('Date of expired: ', final_dic['Date of expired'])
        
        logger.info('Done recognizing!')
        print('-------------------------------------')

if __name__ == '__main__':
    enable_static_mode()
    parser = program.ArgsParser()
    FLAGS = parser.parse_args()
    main()
