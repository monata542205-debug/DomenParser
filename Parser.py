import requests
import datetime
from bs4 import BeautifulSoup
import time
import os
import json
import signal
import sys

def resource_path(rel_path):
    """ Работает и при запуске python Parser.py, и в PyInstaller-бандле """
    base = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel_path)
def read_files():
    current_dir = resource_path('.')
    files = [f for f in os.listdir(current_dir) if os.path.isfile(os.path.join(current_dir, f))]
    return files
def dates():
    today = datetime.datetime.today()
    yesterday = str(today - datetime.timedelta(days=1)).split()[0]
    beforeyesterday = str(today - datetime.timedelta(days=2)).split()[0]
    today = str(today).split()[0]

    return today, yesterday, beforeyesterday
def check_url(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    try:
        response = requests.get(url, timeout=5, headers=headers)
        return response.status_code, "OK"
    except requests.exceptions.ConnectionError:
        return None, "Ошибка подключения"
    except requests.exceptions.Timeout:
        return None, "Таймаут"
    except requests.exceptions.RequestException as e:
        return None, f"Ошибка: {e}"
def download_url_list(today):
    page = 1
    status = 1
    links = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Cache-Control': 'max-age=0',
    }

    while status == 1:
        try:
            print('page:',page)
            url = ('https://domains.ihead.ru/domains/new/' +
                   today + '_ru.html?page=' + str(page))
            response = requests.get(url, timeout=5, headers=headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            soup = soup.find(class_ = 'body').find(class_='cb').find('table')
            soup = soup.find_all('a')
            for link in soup:
                links.append(link.text)
            page += 1
            time.sleep(2)
        except:
            status = 0
        print('links wrote', len(links))

    return links
def links_write(links, today):
    with open(resource_path(today + '.txt'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(links))
def days_write(today, yesterday, beforeyesterday):
    with open(resource_path('dates.txt'), 'w', encoding='utf-8') as f:
        f.write(today + '\n')
        f.write(yesterday + '\n')
        f.write(beforeyesterday + '\n')
def days_read():
    with open(resource_path('dates.txt'), 'r', encoding='utf-8') as f:
        days = [day[:-1] for day in f.readlines()]
    return days
def links_read(date):
    with open(resource_path(date + '.txt'), 'r', encoding='utf-8') as f:
        links = [line.strip() for line in f.readlines()]
    return links
def discord_message(url):
    file = open(resource_path('webhook.txt'), 'r')
    WEBHOOK_URL = file.read()
    file.close()

    payload = {
        "content": f"✅ **Новый зарегистрированный домен:** {url}"
    }

    # Отправляем POST-запрос
    response = requests.post(WEBHOOK_URL, json=payload)

    if response.status_code == 204:
        print("Сообщение успешно отправлено в Discord!")
    else:
        print(f"Ошибка: {response.status_code}")
def signal_handler(signum, frame):
    global running
    running = False
def main():
    # Чтение записанных дней
    days = days_read()
    print(days)
    # Получаем сегодня, вчера и позавчера
    today, yesterday, beforeyesterday = dates()
    # Проверяем есть ли сегодняшний день в файле
    for day in days:
        if day in [today, yesterday, beforeyesterday]:
            pass
        else:
            os.remove(day + '.txt')
    # перезаписали файл с датами
    days_write(today, yesterday, beforeyesterday)
    # записывам новые файлы с датами которых нет
    files = read_files()
    days = days_read()
    print("Файлы в текущей директории:", files)
    for day in days:
        if day + '.txt' in files:
            pass
        else:
            print(day)
            links = download_url_list(day)
            links_write(links, day)

    # проверяем ссылки в файлах
    days = days_read()
    for day in days:
        links = links_read(day)
        good_links = []
        for domen in links:
            print(domen)
            code, message = check_url('https://' + domen)
            print(f"Статус: {code or 'Нет ответа'}, {message}")
            if code == 200:
                discord_message('https://' + domen)
                links.remove(domen)
                links_write(links, day)
            else:
                pass
        # После чтения всех ссылок перезаписываем файл
        links_write(links, day)

if __name__ == '__main__':
    running = True
    signal.signal(signal.SIGINT, signal_handler)
    while running:
        main()
    print("✅ Цикл завершен")