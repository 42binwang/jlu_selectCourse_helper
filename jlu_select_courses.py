#!/usr/bin/env python
# -*- coding: utf-8 -*-  

# author:42binwang
# 42binwang@gmail.com

import json
import queue
from hashlib import md5

# If you use python 2.7, you can use 
# cookielib to replace http.cookiejar 
# besides, urllib2 to replace urllib

import http.cookiejar
from urllib import request
from urllib import parse
from threading import Thread

user_id = ''
pass_plain = ''

# set num_of_worker to define the number of threads
# Please do not set the num_of_threads too large, 
# it will congest the network, please.

num_of_threads = 5

# If the network has been congested, you can increase the allowed_timeout,
# ensure that single thread can survive longer.

allowed_timeout = 1

# -----------------------   Attention!!!   ----------------------- 
#
# The course_id is not the one which provided by "教学班". 
# You should get the course_id from the source code of uims page.
# The valid course_id besides the "选课" button.
# Support multiple courses, use ',' to seperate them.
#
# -----------------------   Attention!!!   ----------------------- 

course_id = ['']

url_prefix = 'http://uims.jlu.edu.cn/ntms/'
uims_opener = request.build_opener(request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
uims_opener.open(url_prefix + 'j_spring_security_check',parse.urlencode({'j_username':user_id, 'j_password':'' + md5(('UIMS'+user_id+pass_plain).encode()).hexdigest() }).encode())

rest_work = queue.Queue()   
result = queue.Queue()   

class Worker(Thread):   
    thread_no = 0   
    def __init__( self, rest_work, result, timeout , **kwargs):   
        Thread.__init__( self, **kwargs ) 
        self.setDaemon( True )  
        self.id = Worker.thread_no  
        Worker.thread_no += 1
        self.timeout = timeout   
        self.start( )   
    def run( self ):     
        while True:  
            try:   
                callable, args, kwargs = rest_work.get( timeout = self.timeout)   
                res = callable(*args, **kwargs)   
                result.put(res)   
            except queue.Empty:   
                break   
            except :   
                print('worker[%d]' % self.id + ' occurred an error')   
                  
class Manager:   
    def __init__( self, num_of_threads, timeout):   
        self.workers = []   
        self.timeout = timeout   
        self.recruit( num_of_threads )   
    def recruit( self, num_of_threads ):   
        for i in range( num_of_threads ):   
            worker = Worker( rest_work, result, self.timeout )   
            self.workers.append(worker)   
    def supervise( self):     
        while len(self.workers):
            try:
                worker = self.workers.pop()   
                worker.join( )   
                if worker.isAlive():   
                    self.workers.append( worker )
            except list.empty:
                print ('Do not have enough living workers, please increase the num_of_threads.')
                break;
            except:
                print ('Something error, retrying...')

    def status( self, *args, **kwargs ):
        if not result.empty():      
            return result.get( *args, **kwargs )
        else:
            return None

class json_exp(Exception):
    def __init__(self):
        #Debug
        pass

def add(callable, *args, **kwargs ):   
    rest_work.put( (callable, args, kwargs) )  

def send_packet(datastr,url):
    headers = dict()
    headers['Content-Type'] = 'application/json'    
    req = request.Request(url, json.dumps(json.loads(datastr)).encode(), headers)
    ret = uims_opener.open(req)    
    return ret

def start():
    manager = Manager(len(course_id),allowed_timeout)
    for i in course_id:
        add(thread,i)
    manager.supervise()
    while True:
        res = manager.status()
        if res == None:
            print('Finish!')
            break

def check_state(data): 
    try:
        j = json.loads(data)
        ret = j['errno']
    except:
        raise json_exp()
    finally:
        return ret

def thread(i):
    print('Course ' + i + ' is selecting ...')
    while True:
        try:
            ret = send_packet('{"lsltId":"%s","opType":"Y"}' % (i) ,url_prefix + 
                'selectlesson/select-lesson.do').read().decode()
            if check_state(ret) == 1410:
                print( 'Course ' + i + ' has been successfully selected!')
                return
        except:
            raise json_exp()
            continue

if __name__ == "__main__":
    while True:
        try:
            start()
        except json_exp:
            print ('Something error, retrying...')
            continue
        break

