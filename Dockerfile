FROM ubuntu

WORKDIR .

COPY requirements.txt .

RUN apt-get update

RUN apt-get -y install software-properties-common

RUN add-apt-repository ppa:deadsnakes/ppa

RUN apt-get update

RUN apt-get -y install python3.8

RUN apt-get -y install libgl1-mesa-glx

RUN apt-get -y install python3-pip

RUN pip3 install --upgrade pip

RUN pip3 install -r requirements.txt

COPY . .

RUN ls

CMD streamlit run tools/infer_det.py

