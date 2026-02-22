import requests
import time
import random
import json
import datetime
import os
import threading
import traceback
import sys
import concurrent.futures
from datetime import timedelta
from concurrent.futures import ThreadPoolExecutor

def log_exception(*args):
    traceback.print_exc()

threading.excepthook = log_exception

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36 Edge/16.16299',
    'Origin' : 'https://reservation.knps.or.kr',
    'Referer' : 'https://reservation.knps.or.kr/',
    'Cookie' : 'ACEUCI=1; ACEFCID=UID-6437C383F8651902DC9533F4; AUFAH6A44218380733=1681376131558318284|2|1681376131558318284|1|1681376126845618284; ACEUACS=1681376126845618284; __utmc=4017075; ACEUCI=1; layer_popup4=done; layer_popup1=done; AUFAH2A44198880516=1681706288835418287|2|1681706288835418287|1|1679925320588348035; __utma=114587101.1434436220.1681706288.1681706288.1681706288.1; __utmc=114587101; __utmz=114587101.1681706288.1.1.utmcsr=reservation.knps.or.kr|utmccn=(referral)|utmcmd=referral|utmcct=/; JSESSIONID=D6F2EABF6DC183889AED7DD180A2951B.U1016; ssoInfo=AALly0iWdcZlyu4fVcyJSRPlamhStMDu5UiYnjyB7371%2FJvbJKjGvVfKSnzgAQrCt9V0VFlMIxLx3fpZSiuMYTfSEMZ02FcTvdB8sfG%2Bw9Xfzw%3D%3D; layer_error=done; NetFunnel_ID=; AUAH6A44218380733=1681731616885574183%7C11%7C1681376131558318284%7C1%7C1681376126845618284%7C1; ARAH6A44218380733=httpsreservationknpsorkrhttpswwwgooglecom; __utma=4017075.602854955.1681376128.1681725979.1681731616.11; __utmz=4017075.1681731616.11.6.utmcsr=google|utmccn=(organic)|utmcmd=organic|utmctr=(not%20provided); __utmb=4017075.1.9.1681731616; ASAH6A44218380733=1681731616885574183%7C1681731621100495933%7C1681731616885574183%7C0%7Chttpswwwgooglecom',
    'sec-ch-ua': '"Google Chrome";v="111", "Not(A:Brand";v="8", "Chromium";v="111"'
}

def get_required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value

telegram_bot_token = get_required_env("TELEGRAM_BOT_TOKEN")
telegram_chat_id = get_required_env("TELEGRAM_CHAT_ID")

def check(name, deptId, prdSalStcd, period, bgnDate, endDate, prdCtgIds) :
    is_snooze = False  # 스누즈 상태 초기값
    snooze_start = 0  # 스누즈 시작 시간 초기값

    while True:
        # HTTP POST 요청 보내기
        data = {"deptId": deptId, "prdSalStcd": prdSalStcd, "period": period, "bgnDate": bgnDate, "endDate": endDate, "prdCtgIds": prdCtgIds}
        session = requests.Session()
        response = session.post("https://reservation.knps.or.kr/reservation/campsite/campsites.do", data=data, headers=headers, allow_redirects=False)

        # 응답값에서 PRD_NM 추출하기
        prd_nm_list = []
        prd_nm_values = []
        try :
            prd_nm_list = json.loads(response.text)["avails"]
        except json.JSONDecodeError as e:
            print(f"Error: {str(e)}")
        else :
            prd_nm_values = [x.get("PRD_NM") for x in prd_nm_list if x.get("PRD_NM")]
        #prd_nm_values = list(filter(lambda x: not x.startswith('B'), prd_nm_values))
        if prd_nm_values :
            print (prd_nm_values)

        if not is_snooze and prd_nm_values:

            if prdSalStcd == 'W': nw = '대기'
            else : nw = '예약'

            # 스누즈 상태가 아니면서, 조건이 충족되면 작업 수행
            message = name + '(' + nw + ')\n' + ', '.join(prd_nm_values) + '\n\n' + 'https://reservation.knps.or.kr/reservation/searchSimpleCampReservation.do'
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
        interval = round(random.uniform(1.0, 3.0), 2)
        #interval = round(random.uniform(7.0, 9.0), 2)
        now = datetime.datetime.now() + timedelta(hours=9)
        print (name + " " + str(interval) + ", " + now.strftime("%Y-%m-%d %H:%M:%S"))
        sys.stdout.flush()

        # 인터벌 대기하기
        time.sleep(interval)

    return 'done'

futures = []
with ThreadPoolExecutor(max_workers=6) as executor:
    #future01 = executor.submit(check,'오대산 5/5 1박', 'B061001', 'N', '1', '20230505', '20230506', '02032')
    #futures.append(future01)
    future02 = executor.submit(check,'오대산 5/6 1박', 'B061001', 'N', '1', '20230506', '20230507', '02032')
    futures.append(future02)
    future03 = executor.submit(check,'오대산 2박3일', 'B061001', 'N', '2', '20230505', '20230507', '02032')
    futures.append(future03)

# 결과 출력 및 예외 처리
for future in concurrent.futures.as_completed(futures):
    try:
        result = future.result()
    except Exception as e:
        print('Exception: %s' % e)
"""
    future07 = executor.submit(check,'치악산 5/5 1박', 'B101001', 'N', '1', '20230505', '20230506', '02032,02021')
    future08 = executor.submit(check,'치악산 5/6 1박', 'B101001', 'N', '1', '20230506', '20230507', '02032,02021')
    future09 = executor.submit(check,'치악산 2박3일', 'B101001', 'N', '2', '20230505', '20230507', '02032,02021')

    future10 = executor.submit(check,'치악산 5/5 1박', 'B101001', 'W', '1', '20230505', '20230506', '02032,02021')
    future11 = executor.submit(check,'치악산 5/6 1박', 'B101001', 'W', '1', '20230506', '20230507', '02032,02021')
    future12 = executor.submit(check,'치악산 2박3일', 'B101001', 'W', '2', '20230505', '20230507', '02032,02021')

    future13 = executor.submit(check,'덕유산 5/5 1박', 'B051006', 'N', '1', '20230505', '20230506', '02032')
    future14 = executor.submit(check,'덕유산 5/6 1박', 'B051006', 'N', '1', '20230506', '20230507', '02032')
    future15 = executor.submit(check,'덕유산 2박3일', 'B051006', 'N', '2', '20230505', '20230507', '02032')

    future16 = executor.submit(check,'덕유산 5/5 1박', 'B051006', 'W', '1', '20230505', '20230506', '02032')
    future17 = executor.submit(check,'덕유산 5/6 1박', 'B051006', 'W', '1', '20230506', '20230507', '02032')
    future18 = executor.submit(check,'덕유산 2박3일', 'B051006', 'W', '2', '20230505', '20230507', '02032')

    future13 = executor.submit(check,'설악산 5/5 1박', 'B031005', 'N', '1', '20230505', '20230506', '02032')
    future14 = executor.submit(check,'설악산 5/6 1박', 'B031005', 'N', '1', '20230506', '20230507', '02032')
    future15 = executor.submit(check,'설악산 2박3일', 'B031005', 'N', '2', '20230505', '20230507', '02032')

    future16 = executor.submit(check,'설악산 5/5 1박', 'B031005', 'W', '1', '20230505', '20230506', '02032')
    future17 = executor.submit(check,'설악산 5/6 1박', 'B031005', 'W', '1', '20230506', '20230507', '02032')
    future18 = executor.submit(check,'설악산 2박3일', 'B031005', 'W', '2', '20230505', '20230507', '02032')

    future13 = executor.submit(check,'주왕산 5/5 1박', 'B071001', 'N', '1', '20230505', '20230506', '02032')
    future14 = executor.submit(check,'주왕산 5/6 1박', 'B071001', 'N', '1', '20230506', '20230507', '02032')
    future15 = executor.submit(check,'주왕산 2박3일', 'B071001', 'N', '2', '20230505', '20230507', '02032')

    future16 = executor.submit(check,'주왕산 5/5 1박', 'B071001', 'W', '1', '20230505', '20230506', '02032')
    future17 = executor.submit(check,'주왕산 5/6 1박', 'B071001', 'W', '1', '20230506', '20230507', '02032')
    future18 = executor.submit(check,'주왕산 2박3일', 'B071001', 'W', '2', '20230505', '20230507', '02032')

    future13 = executor.submit(check,'태백산 5/5 1박', 'B221004', 'N', '1', '20230505', '20230506', '02032')
    future14 = executor.submit(check,'태백산 5/6 1박', 'B221004', 'N', '1', '20230506', '20230507', '02032')
    future15 = executor.submit(check,'태백산 2박3일', 'B221004', 'N', '2', '20230505', '20230507', '02032')

    future16 = executor.submit(check,'태백산 5/5 1박', 'B221004', 'W', '1', '20230505', '20230506', '02032')
    future17 = executor.submit(check,'태백산 5/6 1박', 'B221004', 'W', '1', '20230506', '20230507', '02032')
    future18 = executor.submit(check,'태백산 2박3일', 'B221004', 'W', '2', '20230505', '20230507', '02032')
"""
