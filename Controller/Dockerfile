FROM python:3.7

ADD requirements.txt /src/requirements.txt
WORKDIR /src
RUN pip install -r requirements.txt

ADD entrypoint.sh /src/entrypoint.sh
ADD app /src/app
ADD k8sbwbble /src/k8sbwbble
ENV PYTHONPATH="/src"

ENTRYPOINT [ "/bin/bash", "/src/entrypoint.sh"]
CMD []