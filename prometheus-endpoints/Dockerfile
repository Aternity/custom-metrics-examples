FROM python:3.6

ADD parser.py /
ADD pe_sync.py /

RUN pip install pytz requests python-dateutil
CMD [ "python", "./pe_sync.py" ]

