import datetime
import os
import statistics
import time
import requests

# OKX ETH 永续合约行情 API
OKX_API = "https://www.okx.com/api/v5/market/candles?instId=ETH-USDT-SWAP&bar=5m"

# Bark 推送 API (替换成你自己的 Key)
BARK_KEY = os.getenv("BARK_KEY")

RUN_DURATION = 60 * 61

CHECK_INTERVAL = 2 

CHECK_WAIT = 60 * 15

# 阈值
THRESHOLD = 1e8


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
    print(url)
    try:
        requests.get(url, timeout=10)
    except:
        print('send back error')

def volume_alarm():
    msg = None
    r = requests.get(OKX_API).json()
    data=r["data"]
    current_vol = float(data[0][7])  
    #print(f"当前 ETH 永续 成交量: {format_volume(current_vol)}")
    if current_vol > THRESHOLD:
        msg = f"当前: {format_volume(current_vol)}"
    else:
        vols = [float(item[7]) for item in data[1:6]]
        avg_vol = statistics.mean(vols)
        #print("倒数6到倒数2的平均值:", format_volume(avg_vol))
        if current_vol >= avg_vol * 3:
            msg = f" 当前: {format_volume(current_vol)} 均值: {format_volume(avg_vol)}"
    if msg:
        send_bark(msg)
        print("已发送告警:", msg)
    return msg

def main():
    start_time = datetime.datetime.now()
    print("运行开始",start_time)
    while (datetime.datetime.now() - start_time).total_seconds() < RUN_DURATION:
        if(volume_alarm()):
            time.sleep(CHECK_WAIT)
        else:
            time.sleep(CHECK_INTERVAL)
    print("运行结束",datetime.datetime.now())

if __name__ == "__main__":
    main()