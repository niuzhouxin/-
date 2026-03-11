from email.policy import default
from threading import Lock
import requests
import re
from concurrent.futures import ThreadPoolExecutor
import time
from tqdm import tqdm
import argparse

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}
progress = None
progress_lock = Lock()
def request_sender(args):  # 指定url和字典路径
    url, chunk = args # Pool.map每次只可以传入一个参数，所以把url和chunk打包成一个元组传入
    session = requests.Session()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    for line in chunk:
        urls = url.rstrip("/") + '/' + line # 直接去掉url最后的/，统一加上/，简化了一下代码
        try:
            response = session.get(urls, headers = headers,allow_redirects=False, timeout=2)
            if response.status_code != 404: # 不输出404了，避免终端输出过多
                progress.write(str(response.status_code) + " " + line )
        except requests.RequestException as e:
            pass
        finally:
            with progress_lock:#加锁，确保只有一个线程更新进度条
                progress.update(1)# 每个请求完自动更新

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="目录扫描工具")
    parser.add_argument("-u", "--url",required=True ,help="目标url")
    parser.add_argument("-d" ,"--dict" , default="./dicts.txt", help="字典路径，默认 ./dicts.txt")
    parser.add_argument("-n", "--threads", default=40, type=int, help="线程数，默认 40")
    args = parser.parse_args()
    n = 40 # 线程数
    with open(args.dict,"r",encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    chunks = [lines[i::args.threads] for i in range(args.threads)]
    start = time.time()
    progress = tqdm(total = len(lines) ,desc = "扫描进度",unit = "个",position=0, leave=True)#进度条 position=0 确保进度条固定，leave=True 保证执行后进度条不消失
    with ThreadPoolExecutor(max_workers=args.threads) as executor:
        executor.map(request_sender, [(args.url,chunk) for chunk in chunks])
    print("总耗时："+ str(time.time()-start))
