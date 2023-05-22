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

# curl -X POST "https://gwgs.ticketplay.zone/portal/realtime/productSearchJson" -d "stay_cnt=2&check_in=20230502" --silent | jq
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
    #'Origin' : 'https://bytour.co.kr/item.php?it_id=1645153876',
    'Referer' : 'https://jsimc.or.kr/',
    'Cookie' : '_gid=GA1.2.1202545219.1681777525; __utmc=83068928; __utmz=83068928.1681777525.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); JSESSIONID=CA0435BE3EDDD1859D1B62A389CE85E3.worker1; __utma=83068928.1196473108.1681777525.1681777525.1681824177.2; _ga_9WPCMLF9RN=GS1.1.1681824176.2.1.1681824193.0.0.0; _ga=GA1.2.1196473108.1681777525; __utmb=83068928.4.9.1681824193424',
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"'
}

telegram_bot_token = "6236084783:AAGheuj2FnRgWvw191FEH1ABsqp1LIM4gA8"
telegram_chat_id = "-1001583606817"

"""
{
  "RESULT_CODE": "SUCCESS",
  "RESULT_DATA": [
    {
      "ROOM_CNT": 6,
      "ROOM_AREA_NAME": "통나무",
      "MASTER_IMAGE": "/2018/0515/201805151526396181530001.png",
      "ROOM_AREA_NO": 1,
      "TOT_ROOM_CNT": 10,
      "USE_AMT": 40000
    },
"""
def check(name, date) :
    is_snooze = False  # 스누즈 상태 초기값
    snooze_start = 0  # 스누즈 시작 시간 초기값

    while True:
        # HTTP POST 요청 보내기
        session = requests.Session()
        response = session.get("https://bytour.co.kr/item.php?it_id=1645153876", headers=headers)
        soup = BeautifulSoup(response.text, 'html.parser')
        room_vals = []
        for li in soup.find_all('li'):
            opt_id = li.get('data-opt_id')
            opt_name = str(li.get('data-opt_name'))
            opt_price2 = li.get('data-opt_price2')
            if opt_name != "" and opt_id != "":
                if opt_name == date :
                    room_vals.append(date)
                #print(str(opt_name) + ": " + str(opt_id) + ", " + str(opt_price2))

        if not is_snooze and room_vals:
            # 스누즈 상태가 아니면서, 조건이 충족되면 작업 수행
            message = name + '\n\n' + 'https://bytour.co.kr/item.php?it_id=1645153876'
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
        interval = round(random.uniform(3.7, 6.1), 2)
        now = datetime.datetime.now() + timedelta(hours=9)
        print (name + " " + str(interval) + ", " + now.strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.flush()

        # 인터벌 대기하기
        time.sleep(interval)

    return 'done'

futures = []
with ThreadPoolExecutor(max_workers=3) as executor:
    #future01 = executor.submit(check,'동강전망 5/5 1박', "2023-05-05")
    #futures.append(future01)
    future02 = executor.submit(check,'동강전망 5/27 1박', "2023-05-27")
    future02 = executor.submit(check,'동강전망 5/28 1박', "2023-05-28")
    futures.append(future02)

# 결과 출력 및 예외 처리
for future in concurrent.futures.as_completed(futures):
    try:
        result = future.result()
    except Exception as e:
        print('Exception: %s' % e)
