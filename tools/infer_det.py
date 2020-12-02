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
        else:
            new_str = new_str + i
    return new_str
        

def Key(x):
    return x[0]
def same_rows(key1, dic):
    box1 = dic[key1]
    lst = []
    min_dis = 1000
    for key2 in dic:
        if key1 == key2:
            continue
        box2 = dic[key2]
        
        if abs((box2[3] + box2[1])/2-(box1[3]+box1[1])/2) < min_dis:
            min_dis = box2[3] - box2[1]
            key_same = key2 
    
    return key_same

def under_rows(key1, dic):
    box1 = dic[key1]
    lst = []
    for key2 in dic:
        box2 = dic[key2]
        if (box1[3]<box2[3]):
            lst.append(box2)
    lst.sort(key=Key)

    return lst        

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
    print(dic)    
    
    # remove wrong box
    for key in dic:
        count = 0
        check = False
        for i in key:
            if i >= '0' and i <= '9':
                count = count+1
            if i == '-':
                check = True
        if count in {7, 8} and check:
            birth_w = dic[key][2]-dic[key][0]
            birth_h = dic[key][3]-dic[key][1] 

    list_key_remove = []
    for key in dic:
        if dic[key][2]-dic[key][0] < birth_w*0.4 or dic[key][3]-dic[key][1]<birth_h*7/9:
            list_key_remove.append(key)

   
    # address

    for key in list_key_remove:
        del dic[key]
    
    #print(dic)

    for key1 in dic:
        no_mark_str = remove_mark(key1)

        if no_mark_str.find('Noi DKHK thuong tru')!=-1:
            address_lst = []
            pos = no_mark_str.find('Noi DKHK thuong tru')
            address_str = key1[pos+20:]
            
            same = ''
            if len(address_str) == 0:

                same = same_rows(key1, dic)
                address_str = address_str + same + ', '
            else:
                address_str = address_str + ', '
            
            under = under_rows(key1, dic)
            for box_under in under:
                for key in dic:
                    if box_under == dic[key]:
                        address_str = address_str + key
            
            print('Address: ', address_str)           


if __name__ == '__main__':
    enable_static_mode()
    parser = program.ArgsParser()
    FLAGS = parser.parse_args()
    main()
