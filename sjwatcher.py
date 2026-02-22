import requests
import time
import random
import json
import datetime
import os
import threading
import traceback
import sys
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

def log_exception(*args):
    traceback.print_exc()

threading.excepthook = log_exception

# curl -X POST "https://gwgs.ticketplay.zone/portal/realtime/productSearchJson" -d "stay_cnt=2&check_in=20230502" --silent | jq
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
    'Origin' : 'https://gwgs.ticketplay.zone',
    'Referer' : 'https://gwgs.ticketplay.zone/portal/realtime/productSearch',
    'Cookie' : '_gid=GA1.2.1202545219.1681777525; __utmc=83068928; __utmz=83068928.1681777525.1.1.utmcsr=(direct)|utmccn=(direct)|utmcmd=(none); JSESSIONID=CA0435BE3EDDD1859D1B62A389CE85E3.worker1; __utma=83068928.1196473108.1681777525.1681777525.1681824177.2; _ga_9WPCMLF9RN=GS1.1.1681824176.2.1.1681824193.0.0.0; _ga=GA1.2.1196473108.1681777525; __utmb=83068928.4.9.1681824193424',
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"'
}

def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

telegram_bot_token = get_required_env("TELEGRAM_BOT_TOKEN")
telegram_chat_id = get_required_env("TELEGRAM_CHAT_ID")

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
def check(name, stay_cnt, check_in, check_out):
    is_snooze = False  # 스누즈 상태 초기값
    snooze_start = 0  # 스누즈 시작 시간 초기값

    while True:
        # HTTP POST 요청 보내기
        data = {"stay_cnt": stay_cnt, "check_in" : check_in}
        session = requests.Session()
        response = session.post("https://gwgs.ticketplay.zone/portal/realtime/productSearchJson", data=data, headers=headers)

        # 응답값에서 PRD_NM 추출하기
        room_list = json.loads(response.text)["RESULT_DATA"]
        room_vals = [x.get("ROOM_AREA_NAME") + "(" + str(x.get("ROOM_CNT")) + "/" + str(x.get("TOT_ROOM_CNT")) + "):" + str(x.get("ROOM_AREA_NO")) for x in room_list if x.get("ROOM_CNT") > 0 and x.get("ROOM_AREA_NAME") == "통나무"]

        if not is_snooze and room_vals:
            # 스누즈 상태가 아니면서, 조건이 충족되면 작업 수행
            message = name + '\n\n'
            for r in room_vals:
                message = message + r.split(":")[0] + '\n'
                room_area_no = r.split(":")[1]
                durl = f'https://gwgs.ticketplay.zone/portal/realtime/productSelect?room_area_no={room_area_no}&stay_cnt={stay_cnt}&check_in={check_in}&check_out={check_out}'
                message = message + durl + '\n\n'
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
        interval = round(random.uniform(0.7, 1.1), 2)
        now = datetime.datetime.now() + timedelta(hours=9)
        print (name + " " + str(interval) + ", " + now.strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.flush()

        # 인터벌 대기하기
        time.sleep(interval)

    return 'done'

with ThreadPoolExecutor(max_workers=3) as executor:
    future01 = executor.submit(check,'송지호 5/5 1박', "1", "20230505", "20230506")
    future02 = executor.submit(check,'송지호 5/6 1박', "1", "20230506", "20230507")
    future03 = executor.submit(check,'송지호 2박3일', "2", "20230505", "20230507")
