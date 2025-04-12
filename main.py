import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime, timedelta
import time
# import ssl
# from requests.adapters import HTTPAdapter
# from urllib3.util.ssl_ import create_urllib3_context
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# 創建自定義適配器來處理特殊的SSL憑證
# class TLSAdapter(HTTPAdapter):
#     def init_poolmanager(self, *args, **kwargs):
#         context = create_urllib3_context()
#         # 設定較寬鬆的SSL選項，但仍保持基本安全性
#         context.options |= ssl.OP_NO_SSLv2
#         context.options |= ssl.OP_NO_SSLv3
#         context.options |= ssl.OP_NO_TLSv1
#         context.check_hostname = True
#         kwargs['ssl_context'] = context
#         return super().init_poolmanager(*args, **kwargs)

# 在你的爬蟲函數中使用該適配器
def scrape_fsc_news(yesterday):
    
    # 基本網址
    base_url = "https://www.fsc.gov.tw/ch/home.jsp?id=96&parentpath=0,2"
    
    # 發送請求獲取主頁內容
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }

      # 創建會話並設定適配器
    # session = requests.Session()
    # adapter = TLSAdapter()
    # session.mount('https://', adapter)
    # 增加重試次數和超時設定
    session = requests.Session()
    retries = urllib3.util.Retry(
        total=5,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504]
    )
    adapter = requests.adapters.HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    
    response = requests.get(base_url, headers=headers, verify=False, timeout=30)
    response.encoding = 'utf-8'  # 設置正確的編碼
    
    if response.status_code != 200:
        print(f"錯誤: 無法訪問網頁，狀態碼 {response.status_code}")
        return []
    
    # 解析 HTML
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 使用正確的選擇器找到新聞列表
    news_list = soup.select('#messageform > div.newslist > ul > li[role="row"]')
    
    # 跳過第一個 li 元素，因為它是標題行
    news_list = news_list[1:]
    
    # 存儲結果
    results = []
    
    # 遍歷新聞列表
    for news_item in news_list:
        try:
            # 提取編號
            no_element = news_item.select_one('span.no')
            news_number = no_element.text.strip() if no_element else ""
            
            # 提取發布日期
            date_element = news_item.select_one('span.date')
            if date_element:
                news_date = date_element.text.strip()
                # 只處理今天發布的新聞
                if news_date != yesterday:
                    continue
            else:
                continue  # 如果找不到日期，跳過此新聞
            
            # 提取資料來源
            unit_element = news_item.select_one('span.unit')
            news_source = unit_element.text.strip() if unit_element else ""
            
            # 提取標題和連結
            title_element = news_item.select_one('span.title a')
            if title_element:
                news_title = title_element.text.strip()
                relative_link = title_element.get('href')
                # 處理相對 URL 轉為絕對 URL
                if relative_link.startswith('http'):
                    news_link = relative_link
                else:
                    news_link = "https://www.fsc.gov.tw/ch/" + relative_link
                
                # 訪問新聞詳情頁面獲取內文和瀏覽人次
                detail_response = requests.get(news_link, headers=headers, verify=False, timeout=30)
                detail_response.encoding = 'utf-8'
                
                if detail_response.status_code == 200:
                    detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                    
                    # 提取內文 (根據實際網頁結構調整)
                    content_element = detail_soup.select_one('#ap > div.maincontent > div.page-edit > div > div > div')
                  
                    news_content = content_element.text.strip() if content_element else ""
                    
                    # 提取瀏覽人次 (根據實際網頁結構調整)
                    view_count_element = detail_soup.select_one('#ap > div.pageview > div > ul > li:nth-child(1) > span')
                    view_count = ""
                    if view_count_element:
                        view_count = view_count_element.text.strip()
      
                    # 將所有資訊加入結果
                    result = {
                        "編號": news_number,
                        "發布日期": news_date,
                        "資料來源": news_source,
                        "標題": news_title,
                        "連結": news_link,
                        "內文": news_content,
                        "瀏覽人次": view_count
                    }
                    
                    results.append(result)
                    print(f"已抓取新聞: {news_title}")
                    
                    # 休息一下，避免請求過於頻繁
                    time.sleep(1)
            
        except Exception as e:
            print(f"處理新聞項目時發生錯誤: {str(e)}")
    
    return results

def main():
    
    print("Web scraper ran at", datetime.now())
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    
    # 爬取金管會新聞
    fsc_news = scrape_fsc_news(yesterday)
    #fsc_news =[]
    # 將結果轉換為 JSON 格式
    json_results = json.dumps(fsc_news, ensure_ascii=False, indent=2)
    
    # 也可以將結果保存到文件
    # with open(f'fsc_news_{yesterday}.json', 'w', encoding='utf-8') as f:
    #     f.write(json_results)
        
    print(f"共抓取到 {len(fsc_news)} 則昨日金管會新聞")
    
    # 輸出結果到控制台
    payload = {"news": fsc_news}
    payload = json.dumps(payload, ensure_ascii=False, indent=2)

    # Make.com 生成的 Webhook URL
    webhook_url = "https://hook.eu2.make.com/1afmx4mn534sfphv2jvf5skhpxjfnfk2" 
    #webhook_url = "https://hook.eu2.make.com/si5qqqfq4dfkp42pbrofm9j4igcpt5u8" # old 
    try:
     
        
        # 明確指定 Content-Type 為 application/json
        headers = {
            'Content-Type': 'application/json; charset=utf-8'
        }
        
        # 發送請求
        response = requests.post(
            webhook_url,
            data=json_results.encode('utf-8'),  # 使用 encode 確保正確的編碼
            headers=headers
        )
        
        if response.status_code == 200:
            print(f"成功發送資料到 Make.com，狀態碼：{response.status_code}")
        else:
            print(f"發送失敗，狀態碼：{response.status_code}，回應：{response.text}")
    
    except Exception as e:
        print(f"發送到 Make.com 時發生錯誤：{str(e)}")

if __name__ == "__main__":
    main()
  
