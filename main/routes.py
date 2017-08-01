from flask import jsonify, Flask, request, g, redirect, sessions, url_for, abort, render_template, flash, logging, send_from_directory, send_file, after_this_request
from bs4 import BeautifulSoup, NavigableString, Comment
from celery import Celery
from celery import platforms
from models import db
import json

import csv
import os
from urllib.request import urlretrieve
import time, string, random
import zipfile
import shutil
from selenium import webdriver
from . import app

from .utils import *
from models import *
from main.celery_task import celery

@celery.task(bind=True)
def celery_test(self, links, type, contents):
    count = 0
    lines = []
    file_name = get_random_name()
    if not os.path.exists('crawlcache/'):
        os.mkdir('crawlcache/')
    if type == 'text':
        for link in links:
            count += 1
            line = []
            db_line = {}
            bsObj = modify_page(link)
            for i in contents:
                line.append(bsObj.find(_xlid_=i).get_text().strip())
                db_line[str(len(line))] = bsObj.find(_xlid_=i).get_text().strip()
            save(file_name, db_line)
            lines.append(line)
            self.update_state(state='PROGRESS', meta={'i': (count / len(links)) * 100})
            # with open('crawlcache/' + file_name + '.csv', 'a') as file:
            #     for i in contents:
            #         line.append(bsObj.find(_xlid_=i).get_text().strip())
            #     lines.append(line)
            #     write_csv(file, line)
            # self.update_state(state='PROGRESS',meta={'i': 20})
    elif type == 'webs':
        for link in links:
            count += 1
            bsObj = modify_page(link)
            # with open('crawlcache/' + file_name + '.csv', 'a') as file:
            for i in contents:
                node1 = bsObj.find(_xlid_=i)
                list1 = node1.get_text().strip()
                list2 = node1.get('href').strip() or node1.get('src').strip()
                lines.append([list1, list2])
                # table.insert_one({'name': list1, 'url': list2})
                save(file_name, {'name': list1, 'url': list2})
                # save(file_name, {list1: list2})
                # write_csv(file, [list1, list2])
            self.update_state(state='PROGRESS', meta={'i': (count/len(links))*100})
    elif type == 'pictures':

        for link in links:
            count += 1
            bsObj = modify_page(link)
            for i in contents:
                node1 = bsObj.find(_xlid_=i[0])
                list1 = node1.get_text()
                node2 = bsObj.find(_xlid_=i[1])
                list2 = node2.get('src') or node2.get('href')
                # download_pics(data=[list1, list2], path='crawlcache/' + file_name + '')
                lines.append([list1, list2])
                # table.insert_one({'name': list1, 'url': list2})
                save(file_name, {'name': list1, 'url': list2})

            self.update_state(state='PROGRESS', meta={'i': (count/len(links))*100})
    return {'lines': lines, 'file_name': file_name, 'type': type}


@app.route('/status/<task_id>', methods=['GET'])
def status(task_id):
    # 获取celery之中 task_id的状态信息
    the_task = celery_test.AsyncResult(task_id)   # 获取状态信息
    print("任务：{0} 当前的 state 为：{1}".format(task_id,the_task.state))
    if the_task.state == 'PROGRESS':
        resp = {'state':'progress','progress':the_task.info.get('i',0)}
    elif the_task.state == 'SUCCESS':
        resp = {'state':"success",'progress':100, 'lines':the_task.result.get('lines'), 'type':the_task.result.get('type'), 'file_name':the_task.result.get('file_name')}
    elif the_task.state == 'PENDING':   # 任务处于排队之中
        resp = {'state':'waitting','progress':0}
    else:
        resp = {'state':the_task.state,'progress':the_task.info.get('i',0)}
    return jsonify(resp),200


@app.route('/')
def index():
    """
    首页
    :return: show index.html 
    """
    return render_template('index.html')


@app.route('/get_url', methods=['POST'])
def get_url():
    """
    爬取选取页
    :return:show crawl.html 
    """
    url = request.form['url']  # 获取爬取的网址
    bs_obj = modify_page(url)   #
    crawl_result = request.form['result']   # 获取想要爬取的内容
    return render_template('crawl.html', source=bs_obj.prettify(), crawl_result=json.dumps(crawl_result), url=url)


def modify_page(url):
    """
    对爬取的网站进行处理，例如增加标志位_xlid_，对href与src链接进行处理等等
    :param url: 网站url
    :return: 返回html源码
    """
    driver = webdriver.PhantomJS()
    driver.get(url)

    # req = Request(url)
    # urlopen(url).read()
    # req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.1 (KHTML, like Gecko) Chrome/22.0.1207.1 Safari/537.")
    # html = urlopen(driver.page_source)
    bs_obj = BeautifulSoup(driver.page_source)
    head = bs_obj.find('head')
    body = bs_obj.find('body')
    i = 0  # 标志位计数
    # 对<head>里的src和href进行处理
    for child in head.descendants:
        if type(child) is not NavigableString and type(child) is not Comment:
            if child.has_key('href'):
                if child['href'].startswith('//'):
                    child['href'] = 'http://'+child['href'][2:]
                elif child['href'].startswith('/'):
                    child['href'] = 'http://'+url.split('/')[2]+child['href']
                elif child['href'].startswith(tuple(string.ascii_letters)) and not child['href'].startswith('http'):
                    child['href'] = '/'.join(url.split('/')[:-1])+'/'+child['href']

            if child.has_key('src'):
                if child['src'].startswith('//'):
                    child['src'] = 'http://'+child['src'][2:]
                elif child['src'].startswith('/'):
                    child['src'] = 'http://'+url.split('/')[2]+child['src']
                elif child['src'].startswith(tuple(string.ascii_letters)) and not child['src'].startswith('http'):
                    child['src'] = '/'.join(url.split('/')[:-1])+'/'+child['src']
    # 对<body>里的src和href进行处理，并添加标志位
    for child in body.descendants:
        if type(child) is not NavigableString and type(child) is not Comment:
            child['_xlid_'] = i
            i += 1
            if child.has_key('onclick'):
                child['onclick'] += "return false;"
            else:
                child['onclick'] = 'return false;'
            if child.has_key('href'):
                if child['href'].startswith('//'):
                    child['href'] = 'http://'+child['href'][2:]
                elif child['href'].startswith('/'):
                    child['href'] = 'http://'+url.split('/')[2]+child['href']
                elif child['href'].startswith(tuple(string.ascii_letters)) and not child['href'].startswith('http'):
                    child['href'] = '/'.join(url.split('/')[:-1])+'/'+child['href']
            if child.has_key('src'):
                if child['src'].startswith('//'):
                    child['src'] = 'http://'+child['src'][2:]
                elif child['src'].startswith('/'):
                    child['src'] = 'http://'+url.split('/')[2]+child['src']
                elif child['src'].startswith(tuple(string.ascii_letters)) and not child['src'].startswith('http'):
                    child['src'] = '/'.join(url.split('/')[:-1])+'/'+child['src']
    tag = bs_obj.new_tag('script', src='/static/crawl.js', type="text/javascript")
    body.insert(-1, tag)
    jquery_tag = bs_obj.new_tag('script', src='https://code.jquery.com/jquery-3.2.1.min.js', type="text/javascript")
    head.insert(-1, jquery_tag)
    return bs_obj


@app.route('/crawl_one', methods=['POST'])
def crawl_one():
    contents = json.loads(request.values.get('contents'))
    lines = []
    type = request.values.get('result')
    file_name = get_random_name()
    if not os.path.exists('crawlcache/'):
        os.mkdir('crawlcache/')
    if type == 'text':
        line = []
        with open('crawlcache/' + file_name + '.csv', 'w') as file:
            for i in contents:
                line.append(i[0])

            lines.append(line)
            write_csv(file, line)

    elif type == 'webs':
        with open('crawlcache/' + file_name + '.csv', 'w') as file:
            for i in contents:
                write_csv(file , i)
            lines = contents
    elif type == 'pictures':
        for i in contents:
            download_pics(data=i, path='crawlcache/' + file_name + '')
        lines = contents
    return render_template('result.html', lines=lines, type=type, file_name=file_name)


@app.route('/crawl_more', methods=['POST'])
def crawl_more():
    links = request.values.get('links').split(';')
    contents = json.loads(request.values.get('contents'))
    type = request.values.get('result')
    celery_task = celery_test.apply_async((links, type, contents))

    return render_template('crawling.html', task_id=celery_task.id)


@app.route('/crawl_more_result', methods=['POST'])
def crawl_more_result():
    lines = json.loads(request.values.get('lines'))

    type = request.values.get('type')
    file_name = request.values.get('file_name')



    return render_template('result.html', lines=lines, type=type, file_name=file_name)


def write_csv(file, line):
    """
    写入csv
    :param file: 文件路径名 
    :param line: 列数据
    :return: none
    """
    csv_writer = csv.writer(file)
    csv_writer.writerow(line)


def download_pics(data, path):
    """
    下载图片
    :param data: 图片信息[名字，url]
    :param path: 图片路径
    :return: 
    """
    if not os.path.isdir(path):
        os.mkdir(path)

    urlretrieve(url=data[1], filename=path+'/'+str(data[0]).strip()+'.'+data[1].split('.')[-1])


@app.route('/download/<filename>', methods=['GET', 'POST'])
def download(filename):
    """
    下载文件
    :param filename: 
    :return: 
    """


    if filename.endswith('.csv'):
        table = db.get_collection(filename[:15])
        results = table.find({}, {"_id": 0})
        with open('crawlcache/' + filename, 'a') as file:
            for result in results:
                line = []
                for key, value in result.items():
                    line.append(value)
                write_csv(file, line)

    else:
        table = db.get_collection(filename)
        results = table.find()
        for result in results:
            download_pics(data=[result['name'], result['url']], path='crawlcache/' + filename + '')

    if filename.endswith('.csv'):
        @after_this_request
        def remove_file(response):
            try:
                os.remove('crawlcache/' + filename)
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response
        return send_from_directory(directory='crawlcache/', filename=filename)
    else:

        zipf = zipfile.ZipFile(file='crawlcache/' + filename + '.zip', mode='w', compression=zipfile.ZIP_DEFLATED)
        zipdir('crawlcache/' + filename + "/", zipf)
        zipf.close()

        shutil.rmtree('crawlcache/' + filename)
        filename = filename + '.zip'
        @after_this_request
        def remove_file(response):
            try:
                os.remove('crawlcache/' + filename)
            except Exception as error:
                app.logger.error("Error removing or closing downloaded file handle", error)
            return response
        return send_from_directory(directory='crawlcache/', filename=filename, as_attachment=True)


def zipdir(path, ziph):
    """

    :param path: 
    :param ziph: ziph is zipfile handle
    :return: 
    """
    for root, dirs, files in os.walk(path):
        for file in files:
            ziph.write(os.path.join(root, file))


if __name__ == '__main__':
    app.run()

