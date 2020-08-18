FROM continuumio/anaconda3:latest

RUN apt-get update

# upgrade pip
RUN pip install --upgrade pip

# install other python requirements
ADD . /kbn/
RUN conda install geopandas shapely
RUN pip install tox
RUN pip install -r requirements.txt
RUN pip install -e .

RUN conda list

ENTRYPOINT python -u kbn/tests/test_pyFIS.py
