FROM python:3.11

WORKDIR /usr/src/app

COPY app/ ./
COPY requirements.txt ./

RUN pip install uv
RUN uv pip install -r requirements.txt --system

CMD ["python", "-m", "streamlit", "run", "site.py"]
