from __future__ import absolute_import, division, print_function

#python3 tools/infer_det.py
import streamlit as st
from imutils import paths
import io 
import numpy as np
from copy import deepcopy
import os
import sys

__dir__ = os.path.dirname(os.path.abspath(__file__))
sys.path.append(__dir__)
sys.path.append(os.path.abspath(os.path.join(__dir__, '..')))

from paddle import fluid
from ppocr.utils.utility import create_module
import program
from ppocr.data.reader_main import reader_main
from tools.identify_text import *
#from tools.utils import OCR_text
import cv2

from ppocr.utils.utility import initial_logger
logger = initial_logger()
from ppocr.utils.utility import enable_static_mode

# Vietocr
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
        #logger.info("The detected Image saved in {}".format(save_path))

def paddle(img_path, config, exe, eval_prog, eval_fetch_list):
    
    config['Global']['infer_img'] = img_path
    #logger.info('pass1')
    test_reader = reader_main(config=config, mode='test')
    #logger.info('pass2')
    tackling_num = 0
    for data in test_reader():
        img_num = len(data)
        #tackling_num = tackling_num + img_num
        #logger.info("Number of images:%d", tackling_num)
        img_list = []
        ratio_list = []
        img_name_list = []
        for ino in range(img_num):
            img_list.append(data[ino][0])
            ratio_list.append(data[ino][1])
            img_name_list.append(data[ino][2])
        #logger.info('pass3')
        img_list = np.concatenate(img_list, axis=0)
        logger.info("Getting text boxes..")
        outs = exe.run(eval_prog,\
            feed={'image': img_list},\
            fetch_list=eval_fetch_list)
        logger.info('Done get text box!')

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

@st.cache(allow_output_mutation=True)
def load_model():   

    config = program.load_config('./configs/det/det_r18_vd_db_v1.1.yml')

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
    config_ocr['weights'] = './my_weights/transformer.pth'
    config_ocr['cnn']['pretrained']=False
    config_ocr['device'] = 'cpu'
    config_ocr['predictor']['beamsearch']=False

    detector = Predictor(config_ocr)

    return detector, exe, config, eval_prog, eval_fetch_list


enable_static_mode()
detector, exe, config, eval_prog, eval_fetch_list = load_model()

# Detect box text
st.header('TRÍCH XUẤT THÔNG TIN TRÊN CMND, THẺ CĂN CƯỚC')
uploaded_file = None
uploaded_file = st.file_uploader('CHỌN ẢNH')

if uploaded_file is not None:
    img_byte = uploaded_file.read()
    img = Image.open(io.BytesIO(img_byte))
    copy_img = img.copy()
    #resize_img = imutils.resize(img, width=500)
    #st.image(resize_img)
    img = img.convert('RGB')
    img.save('upload.jpg')
    img_path = 'upload.jpg'
    wpercent = (500/float(copy_img.size[0]))
    hsize = int((float(copy_img.size[1])*float(wpercent)))
    copy_img = copy_img.resize((500,hsize), Image.ANTIALIAS)
    st.image(copy_img)
    #logger.info('pass')
# for i in range(11, 620):
#     img_path = 'test/' + str(i) + '.jpg'
#     if not os.path.exists(img_path):
#         img_path = 'test/' + str(i) + '.png'
#     if not os.path.exists(img_path):
#         continue

    #print('pass')
    copy_img_rotate = None
    j = -1
    while True:
        j += 1
        try:
            logger.info("Begining detect id card..")
            #src_img = cv2.imread(img_name)

            dt_boxes, ori_img = paddle(img_path, config, exe, eval_prog, eval_fetch_list)
            
            if j==0:
                copy_img_rotate = ori_img.copy()
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
                #print('[INFO] This is a Citizenship card!')

                type_cut = cut_roi_cc(list_text_box1, ori_img)
                dt_boxes, copy_img = paddle('out.jpg', config, exe, eval_prog, eval_fetch_list)  

                # OCR again         
                list_text_box2 = OCR_text(1, dt_boxes, copy_img, detector)

                # Find Id text
                final_dic['Id'], obj_id = find_id_text_cc(list_text_box2, detector)
                # Find box 'Quoc tich'
                try:
                    obj_quoctich_dantoc = find_box_Quoctich_Dantoc(list_text_box2)
                except:
                    pass
                try:
                    VietNamdantoc = find_VietNam_dantoc(list_text_box2, obj_quoctich_dantoc)
                except:
                    pass
                #print('QUOCTIChDANTOC', obj_quoctich_dantoc.key)

                # Find birth text
                try:
                    final_dic['Birth'], obj_birth = find_birth_text_cc(list_text_box2, obj_quoctich_dantoc, copy_img)
                except:
                    pass
                # Remove wrong box

                try: 
                    list_text_box2 = remove_wrong_box_cc(list_text_box2, obj_id)
                except:
                    pass
                # Find name text
                try:
                    final_dic['Name'] = find_name_text_cc(list_text_box2, obj_quoctich_dantoc, VietNamdantoc, obj_id, copy_img)
                except:
                    pass
                
                # Find date of expired
                try:
                    if type_cut == 2:
                        final_dic['Date of expired'], obj_expired = '', None
                    else:
                        final_dic['Date of expired'], obj_expired = find_key_expired(list_text_box2, obj_birth)
                except:
                    pass

                # Find sex
                try:
                    final_dic['Sex'], obj_Gioitinh, obj_nam_or_nu = find_sex(list_text_box2)
                except:
                    pass

                try:
                    if VietNamdantoc is not None and obj_nam_or_nu is None and obj_Gioitinh is None:
                        final_dic['Sex'] = find_gioitinh_base_vietnam(list_text_box2, VietNamdantoc, obj_quoctich_dantoc)
                except:
                    pass
                # Delete box has been already  processed

                try:
                    list_text_box2, obj_cogiatriden = delete_box_processed_cc(list_text_box2, obj_Gioitinh, obj_nam_or_nu, obj_quoctich_dantoc, obj_expired, obj_birth, VietNamdantoc, type_cut)
                except:
                    pass
                #for obj in list_text_box2:
                #    print('left', obj.key)
                # find hometown and address
                try:
                    final_dic['Hometown'], final_dic['Address'] = find_hometown_address_text_cc(list_text_box2, obj_cogiatriden)
                except:
                    pass
                #print('Final dic: ', final_dic)
            else:
                #print('[INFO] This is a Identification Card!')
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
                try:
                    final_dic['Birth'], birth_size, obj_birth  = find_birth_text(list_text_box2, obj_id)
                except:
                    pass
                # Find cmnd
                try:
                    obj_cmnd = find_cmnd(list_text_box2)
                except:
                    pass
                # Remove wrong box
                try:
                    list_text_box2 = remove_wrong_box(list_text_box2, obj_id, obj_birth, birth_size, obj_cmnd)
                except:
                    pass
                # Find name text
                
                try:
                    final_dic['Name'], obj_name = find_name_text(list_text_box2, obj_id, obj_birth, obj_cmnd, detector, copy_img)
                except:
                    pass

                try:
                    if (final_dic['Id'] == remove_char(final_dic['Birth']) or len(final_dic['Id'])<9) and obj_name is not None:
                        final_dic['Id'] = draw_box_id(list_text_box2, box_id, obj_name, copy_img, detector, obj_cmnd)
                except:
                    pass
                # Delete box has been already processed
                
                try:
                    list_text_box2 = delete_box_processed(list_text_box2, obj_birth.two_points)
                except:
                    pass
                # find hometown and address
                #for obj in list_text_box2:
                #    print('left', obj.key)
                try:
                    final_dic['Hometown'], final_dic['Address'] = find_hometown_address_text(list_text_box2)  
                except:
                    pass            

            if final_dic['Id'] == '':
                a = 1/0
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

            st.write('Id number: ', final_dic['Id'])
            st.write('Name: ', final_dic['Name'])
            st.write('Sex: ', final_dic['Sex'])
            st.write('Date of birth: ', final_dic['Birth'])
            st.write('Hometown: ', final_dic['Hometown'])
            st.write('Address: ', final_dic['Address'])
            st.write('Date of expired: ', final_dic['Date of expired'])
            break 
            
        except:
            if j == 0:
                ro_img = imutils.rotate_bound(copy_img_rotate, -90)
                cv2.imwrite('{}.jpg'.format(j), ro_img)
                img_path = '{}.jpg'.format(j)
            elif j ==1:
                ro_img = imutils.rotate_bound(copy_img_rotate, 90)
                cv2.imwrite('{}.jpg'.format(j), ro_img)
                img_path = '{}.jpg'.format(j)
            elif j ==2:
                ro_img = imutils.rotate_bound(copy_img_rotate, 180)
                cv2.imwrite('{}.jpg'.format(j), ro_img)
                img_path = '{}.jpg'.format(j)
            else:
                print('Cannot recognizing')
                st.write('Cannot recognize id card information!')
                break                                             
#---------------------------------------------
