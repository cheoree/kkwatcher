import requests
import time
import random
import json
import datetime
import threading
import traceback
import sys
import concurrent.futures
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from bs4 import BeautifulSoup

def log_exception(*args):
    traceback.print_exc()

threading.excepthook = log_exception

# curl -X POST "https://www.yao.or.kr:451/reservation.asp?location=001_02" -d "res_date=2023-05-26&reading=readok&x=82&y=4" -H "Origin: https://www.yao.or.kr:451" -H "Referer: https://www.yao.or.kr:451/reservation.asp?location=001_01" --silent
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
    'Origin' : 'https://www.yao.or.kr:451',
    'Referer' : 'https://www.yao.or.kr:451/reservation.asp?location=001_01',
    'Cookie' : 'ASPSESSIONIDCQABQTQD=AJLICHCADLJDMIJPHHOLGFBB; cookie_name=cookie_value; ASPSESSIONIDCUAFQTQD=BJLICHCAKCMFJHAAPDAAMIHJ; __utma=237822344.2053226346.1683603013.1683603013.1683603013.1; __utmc=237822344; __utmz=237822344.1683603013.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); safeCookie1=foo; safeCookie2=foo; crossCookie=bar; __utmb=237822344.18.9.1683603503108'
}

telegram_bot_token = "6236084783:AAGheuj2FnRgWvw191FEH1ABsqp1LIM4gA8"
telegram_chat_id = "-1001583606817"

def check(name, dt, tm) :
    is_snooze = False  # 스누즈 상태 초기값
    snooze_start = 0  # 스누즈 시작 시간 초기값

    while True:
        # HTTP POST 요청 보내기
        data = {"res_date" : dt, "reading" : "readok", "x": "82", "y":"4"}
        session = requests.Session()
        response = session.post("https://www.yao.or.kr:451/reservation.asp?location=001_02", data=data, headers=headers)

        soup = BeautifulSoup(response.text, 'html.parser')
        room_vals = []
        for start in soup.find_all('input', {'name': 'sch_time'}) :
            if start['value'] in tm:
                room_vals.append(start['value'])

        if not is_snooze and room_vals:
            # 스누즈 상태가 아니면서, 조건이 충족되면 작업 수행
            message = name + '\n\n'
            for r in room_vals:
                message = message + r + '\n'
            message = message + '\nhttps://www.yao.or.kr:451/reservation.asp?location=001'
            print (message)
            telegram_url = f"https://api.telegram.org/bot{telegram_bot_token}/sendMessage"
            telegram_data = {"chat_id": telegram_chat_id, "text": message}

            response = session.post(telegram_url, data=telegram_data, headers=headers)
            #session2.close()
            is_snooze = True
            snooze_start = time.time()
        elif is_snooze and time.time() - snooze_start >= 600:
            # 스누즈 상태이면서, 5분이 경과하면 스누즈 해제
            is_snooze = False

        session.close()

        # 무작위 인터벌 설정하기
        interval = round(random.uniform(4.6, 2.1), 2)
        now = datetime.datetime.now() + timedelta(hours=9)
        print (name + " " + str(interval) + ", " + now.strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.flush()

        # 인터벌 대기하기
        time.sleep(interval)

    return 'done'

futures = []
with ThreadPoolExecutor(max_workers=2) as executor:
    future01 = executor.submit(check,'별마로 05-27', "2023-05-27", ["20:30", "21:00", "21:30"])
    futures.append(future01)
    future02 = executor.submit(check,'별마로 05-28', "2023-05-28", ["20:30", "21:00", "21:30"])
    futures.append(future02)

# 결과 출력 및 예외 처리
for future in concurrent.futures.as_completed(futures):
    try:
        result = future.result()
    except Exception as e:
        print('Exception: %s' % e)
