import sys, os, re, shutil, logging, datetime

from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv
import slack


def main():
    logging.info(datetime.datetime.now())

    # 공지사항 게시판 html 가져오기
    list_url = 'https://seoulstartuphub.com/hub/noticeList.do'
    response = requests.get(list_url)
    list_html = response.content.decode(response.encoding)

    # 게시판 html에서 첫번째 메뉴 게시글의 index 찾아내기
    notices_soup = BeautifulSoup(list_html, "html.parser")
    latest_menu = notices_soup.find('a', text=re.compile(os.getenv('TARGET_KEYWORD_REGEX')))
    notice_index = re.compile(r'\d+').search(latest_menu['onclick']).group()

    # 게시글 html 가져오기
    post_url = 'https://seoulstartuphub.com/hub/noticeView.do?b_idx=' + notice_index
    response = requests.get(post_url)
    post_html = response.content.decode(response.encoding)

    # 게시글 html에서 'cont'클래스 안의 이미지 찾아내기
    post_soup = BeautifulSoup(post_html, "html.parser")
    menu_img_path = post_soup.find(text=re.compile('.*첨부파일')).parent.a['href']
    menu_img_index = re.compile(r'\d+').search(menu_img_path).group()

    # 이미지가 이미 있는지 확인
    if os.path.exists('./image/' + menu_img_index + '.jpg'):
        return

    # 이미지 다운로드
    with requests.get('https://seoulstartuphub.com' + menu_img_path, stream=True) as r:
        if r.status_code == 200:
            with open('./image/' + menu_img_index + '.jpg', 'wb') as f:
                for chunk in r.iter_content():
                    f.write(chunk)
        else:
            logging.error(r)

    # slack 메세지 전송
    slack_client = slack.WebClient(token=os.getenv('SLACK_TOKEN'))
    response = slack_client.files_upload(
        channels=os.getenv('TARGET_CHANNEL'),
        file='image/' + menu_img_index + '.jpg',
        initial_comment="이번주 메뉴판입니다"
    )
    if response['ok']:
        logging.info('image sent!')
    else:
        logging.error(response)


if __name__ == '__main__':
    logging.basicConfig(filename='./log/menu_notifier.log', level=logging.INFO)
    load_dotenv()

    scheduler = BlockingScheduler()
    scheduler.add_job(main, 'cron', day_of_week='mon-tue', hour='8,10', id="menu_scrap")
    scheduler.start()
    