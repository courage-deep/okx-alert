import datetime
import os
import statistics
import time
import requests

# OKX ETH 永续合约行情 API
OKX_API = os.getenv("OKX_API") or "https://www.okx.com/api/v5/market/candles?instId=ETH-USDT-SWAP&bar=5m"

# Bark 推送 API (替换成你自己的 Key)
BARK_KEY = os.getenv("BARK_KEY") or None

# 运行配置
RUN_DURATION = int(os.getenv("RUN_DURATION") or 60 * 61 * 4)
CHECK_INTERVAL = float(os.getenv("CHECK_INTERVAL") or 0.5)
CHECK_WAIT = int(os.getenv("CHECK_WAIT") or 60 * 15)
CHECK_WAIT_INTERVAL = int(os.getenv("CHECK_WAIT_INTERVAL") or 1)

# 阈值
THRESHOLD = int(os.getenv("THRESHOLD") or 1e8)
AVG_RANGE = int(os.getenv("AVG_RANGE") or 5)   # 这里应该用 AVG_RANGE，不是 AVG_MULTI
AVG_MULTI = int(os.getenv("AVG_MULTI") or 3)

# 波动比例阈值
INCREASE_PERCANTAGE_THRESHOLD = float(os.getenv("INCREASE_PERCANTAGE_THRESHOLD") or 0.5)
DECREASE_PERCANTAGE_THRESHOLD = float(os.getenv("DECREASE_PERCANTAGE_THRESHOLD") or 0.5)
RANGE_PERCANTAGE_THRESHOLD = float(os.getenv("RANGE_PERCANTAGE_THRESHOLD") or 0.8)


def format_volume(vol):
    if vol >= 1e8:
        return f"{vol/1e8:.2f}y"
    elif vol >= 1e4:
        return f"{vol/1e4:.2f}w"
    else:
        return str(vol)
def send_bark(msg):
    if not msg and not BARK_KEY :
        return
    url = f"https://api.day.app/{BARK_KEY}/{msg}"
    #print(url)
    try:
        requests.get(url, timeout=10)
    except Exception as e:
        print('send bark error',e)

def get_data():
    try:
        return requests.get(OKX_API,timeout=10).json()
    except Exception as e:
        print('get data error',e)
        return None

def get_increase_percantage(data):
    r=( float(data[2]) - float(data[1]) ) / float(data[1])
    return r *100

def get_decrease_percantage(data):
    r=( float(data[3]) - float(data[1]) ) / float(data[1])
    return r *100 * -1

def get_range_percantage(data):
    r=( float(data[2]) - float(data[3]) ) / float(data[1])
    return r *100
    
def volume_alarm():
    msg = None
    r = get_data()
    if(r):
        data=r["data"]
        current_data=data[0]
        current_vol = float(current_data[7])  
        current_range_percantage=get_range_percantage(current_data)
        current_increase_percantage=get_increase_percantage(current_data)
        current_decrease_percantage=get_decrease_percantage(current_data)
        # print(current_range_percantage)
        # print(current_increase_percantage)
        # print(current_decrease_percantage)
        #print(f"当前 ETH 永续 成交量: {format_volume(current_vol)}")
        if current_vol >= THRESHOLD:
            msg = f"当前: {format_volume(current_vol)}"
        elif current_range_percantage >= RANGE_PERCANTAGE_THRESHOLD :
            msg = f"变化: {current_range_percantage:.2f}"
        elif current_increase_percantage >=INCREASE_PERCANTAGE_THRESHOLD:
            msg = f"in: {current_increase_percantage:.2f}"   
        elif current_decrease_percantage >= DECREASE_PERCANTAGE_THRESHOLD:
            msg = f"de: {current_decrease_percantage:.2f}" 
        else:
            vols = [float(item[7]) for item in data[1:AVG_RANGE+1]]
            avg_vol = statistics.mean(vols)
            #print("倒数6到倒数2的平均值:", format_volume(avg_vol))
            if current_vol >= avg_vol * AVG_MULTI:
                msg = f" 当前: {format_volume(current_vol)} 均值: {format_volume(avg_vol)}"
        if msg:
            send_bark(msg)
            print("已发送告警:", msg,"当前时间:",datetime.datetime.now())
    return msg

def get_wait_time():
    now = datetime.datetime.now()
    next_time=now + datetime.timedelta(minutes= 5*(1+CHECK_WAIT_INTERVAL))
    next_time = next_time.replace( minute=(next_time.minute//5)*5, second=0, microsecond=0)
    return (next_time - now).total_seconds() + 1  

def main():
    os.environ['TZ'] = os.getenv("TZ","Asia/Shanghai")
    time.tzset() 
    start_time = datetime.datetime.now()
    print("运行开始",start_time)
    while (datetime.datetime.now() - start_time).total_seconds() < RUN_DURATION:
        if(volume_alarm()):
            time.sleep(get_wait_time())
        else:
            time.sleep(CHECK_INTERVAL)
    print("运行结束",datetime.datetime.now())

if __name__ == "__main__":
    main()
