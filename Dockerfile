FROM python:3.6

LABEL maintainer "telumo<drumscohika@gmail.com>"

RUN apt-get update && \
    apt-get install git -y && \
    git clone https://github.com/telumo/matrixflow.git

RUN pip install Cython==0.28.5 numpy==1.14.5
RUN pip install -r /matrixflow/requirements.txt

WORKDIR /matrixflow/src

EXPOSE 8081

CMD ["python", "app.py"]
