# recognize_id_card

# Yêu cầu
Python 3.8

streamlit==0.75.0
imutils==0.5.3
numpy==1.19.5
opencv-python
pillow==8.1.0
vietocr==0.3.5
paddlepaddle==2.0.0
PyYAML==5.3.1
argparse==1.1
requests==2.25.1
torch==1.7.1
torchvision==0.8.2
pyclipper==1.2.1
shapely
imgaug
pyclipper
lmdb
tqdm
numpy
visualdl
python-Levenshtein

# Cách sử dụng:
Tạo một môi trường sử dụng python 3.8

Cài đặt thư viện:

```
pip install -r requirements.txt
```
Chạy webapp:

```
streamlit run tools/infer_det.py
```

Giao diện webapp hiện ra, chọn 1 file ảnh chứa ảnh cmnd hoặc thẻ căn cước công dân. Đợi 1 thời gian sẽ cho ra kết quả thông tin trên trên ảnh.

![alt text](https://github.com/chauthehan/RECOGNIZE_ID_CARD/blob/master/output/demo.png)

# Dùng docker
Tải và cài đặt docker

Tạo image:

```
sudo docker build -t [name image] .
```

Chạy image:

```
sudo docker run [image id] 
```


