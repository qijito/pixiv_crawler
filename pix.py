# -*- coding:utf-8 -*-
import requests
from bs4 import BeautifulSoup
import os
import time
import re
import sys

se = requests.session() 


class Pixiv():

    def __init__(self):
        self.base_url = 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index'
        self.login_url = 'https://accounts.pixiv.net/login?lang=zh'
        self.target_url = 'https://www.pixiv.net/ranking.php?mode='
        self.main_url = 'http://www.pixiv.net'
        self.headers = {
            'Referer': 'https://accounts.pixiv.net/login?lang=zh&source=pc&view_type=page&ref=wwwtop_accounts_index',
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.75 Safari/537.36'
        } # you can use your own User-Agent
        self.pixiv_id = '$USER_ID' # USER_ID
        self.password = '$PASSWORD' # PASSWORD
        self.post_key = []
        self.return_to = 'http://www.pixiv.net'
        self.load_path = '/home/$USER/图片' # the path you want the crawler to save
        self.rank = 0 

    def login(self):
        post_key_html = se.get(self.base_url, headers=self.headers).text
        post_key_soup = BeautifulSoup(post_key_html, 'lxml')
        self.post_key = post_key_soup.find('input')['value']
        # 上面是去捕获postkey
        data = {
            'pixiv_id': self.pixiv_id,
            'password': self.password,
            'return_to': self.return_to,
            'post_key': self.post_key
        }
        se.post(self.login_url, data=data, headers=self.headers)

    def get_url(self, mode):
        html_rank = requests.get(self.target_url+mode).text 
        soup = BeautifulSoup(html_rank, 'lxml') 
        list = soup.find_all(class_ = "ranking-image-item")
        for x in list:
            y=str(x)
            id=re.findall(r"href=\"(.+?)\"", y, re.I)
            flag_mutipule = re.search(r'work _work multiple ', str(x))
            url = self.main_url+id[0]  # 获取图片的html
            jump_to_html=se.get(url, headers=self.headers).text
            img_soup = BeautifulSoup(jump_to_html, 'lxml')
            img_info = img_soup.find('div', attrs={'class', '_layout-thumbnail ui-modal-trigger'})
            img_original = re.search(r'http(.+?)(jpg|png)', re.search(r'"original":"(.+?)"', str(img_soup))[0])[0]
            if img_original[-3:] == 'gif':
                continue
            self.rank += 1 
            if flag_mutipule == None:  # 有些找不到url,continue会报错
                #img_ori_url =re.findall(r"src=\"(.+?)\"", str(img_original), re.I)[0] 
                #print(img_ori_url)
                self.download_img(img_soup, url, img_original)  # 去下载这个图片
            else:
                many_url = url.replace("medium&amp;illust", "manga&illust")
                #print(url)
                print(many_url)
                self.download_many_img(img_info, many_url)
            time.sleep(3)

    def download_img(self, img_soup, url, img_ori_url):
        title = re.search(r'「(.+?)\[pixiv\]', str(img_soup))[0]  # 提取标题
        src = img_ori_url.replace('\\', '')   # 提取图片位置 
        src_headers = self.headers
        src_headers['Referer'] = url  # 增加一个referer,否则会403,referer就像上面登陆一样找
        print('正在保存名字排行第{}的图片'.format(self.rank))
        title = title.replace('?', '_').replace('/', '_').replace('\\', '_').replace('*', '_').replace('|', '_')\
            .replace('>', '_').replace('<', '_').replace(':', '_').replace('"', '_').strip()
        # 去掉那些不能在文件名里面的.记得加上strip()去掉换行
        if os.path.exists(self.load_path + title + src[-4:]):
                print("图片已存在")
        else:
            try:
                html = requests.get(src, headers=src_headers)
                img = html.content
            except:  # 有时候会发生错误导致不能获取图片.直接跳过这张图吧
                print('获取该图片失败')
                return False
            with open(self.load_path + title + src[-4:], 'ab') as f:  # 图片要用b
                f.write(img)
            print('保存该图片完毕')

    def download_many_img(self, img_info, many_url):
        src_headers = self.headers 
        src_headers['Referer'] = many_url # 增加一个referer,否则会403,referer就像上面登陆一样找
        html = requests.get(many_url, headers=src_headers) 
        soup = BeautifulSoup(html.content, 'lxml')
        total = soup.find('span', attrs={'class', 'total'}).get_text() 
        title = soup.find("title").get_text() 
        title = title.replace('?', '_').replace('/', '_').replace('\\', '_').replace('*', '_').replace('|', '_')\
            .replace('>', '_').replace('<', '_').replace(':', '_').replace('"', '_').strip()
        # 去掉那些不能在文件名里面的.记得加上strip()去掉换行
        img_many = soup.find_all('img', attrs={'class', 'image ui-scroll-view'}) 
        for x in range(eval(total)):
            img_many_url = re.findall(r"data-src=\"(.+?)\"",str(img_many),re.I)[x] 
            print('正在保存名字排行第{}的图片第{}张'.format(self.rank,x+1)) 
            if os.path.exists(self.load_path + title +"{}".format(x+1) + img_many_url[-4:]):
                print("图片已存在")
                continue
            src_headers = self.headers
            src_headers['Referer'] = img_many_url   # 增加一个referer,否则会403,referer就像上面登陆一样找
            html = requests.get(img_many_url, headers=src_headers) 
            img = html.content
            with open(self.load_path + title +"{}".format(x+1) + img_many_url[-4:], 'ab') as f:  # 图片要用b
                f.write(img)
            print('保存该图片完毕')

    def work(self, mode):
        self.login()
        self.get_url(mode) 

def get_mode(mode=[]):
    modedic = {'1':'daily',
    '1r':'daily_r18',
    '2':'weekly',
    '2r':'weekly_r18',
    '2g':'weekly_r18g',
    '3':'monthly',
    '4':'rookie',
    '5':'original',
    '6':'male',
    '6r':'male_r18',
    '7':'female',
    '0':'done'}

    m = '1'
    while(m != '0'):
        m = modedic.get(input('''       
        1:daily
        1r:daily_r18
        2:weekly
        2r:weekly_r18
        2g:weekly_r18g
        3:monthly
        4:rookie
        5:original
        6:male
        6r:male_r18
        7:female
        0:done
        '''))
        if(m == None):
            sys.exit("invalid mode")
        elif(m == "done"):
            pix = Pixiv()
            for i in mode:
                pix.work(i)
            sys.exit()
        else:
            mode.append(m)

get_mode()