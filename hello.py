import streamlit as st
from imutils import paths
import io 
from PIL import Image
import imutils

st.header('TRÍCH XUẤT THÔNG TIN TRÊN CMND, THẺ CĂN CƯỚC')
uploaded_file = None
uploaded_file = st.file_uploader('Chọn ảnh có chứa cmnd, thẻ căn cước', type=['jpg', 'png'])

if uploaded_file is not None:
    img_byte = uploaded_file.read()
    img = Image.open(io.BytesIO(img_byte))

    wpercent = (300/float(img.size[0]))
    hsize = int((float(img.size[1])*float(wpercent)))
    img = img.resize((300,hsize), Image.ANTIALIAS)
    #resize_img = img.resize((600, 400))
    st.image(img)
    img = img.convert('RGB')
    img.save('upload.jpg')

    
    