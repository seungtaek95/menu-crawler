FROM python:3.8.7

RUN ln -snf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && echo Asia/Seoul > /etc/timezone

WORKDIR /usr/src/menu-notifier

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "main.py"]