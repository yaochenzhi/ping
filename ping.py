#!/usr/bin/env python36
# -*- coding: utf-8 -*-
"""
Date: 2018/11/5
Auth: ycz
Desc: brand new ping monitor totally powered by ycz. all rights reserved!
"""
from local_settings import ping_database as database
from ping_alert import ping_alert
from threading import Thread
import subprocess
import datetime
import pymysql
import logging


logging.basicConfig(level=logging.DEBUG)

CMD = "ping -W 10 -c 10 {}"

class PING(Thread):
    def __init__(self, ip_addr, items):
        Thread.__init__(self)
        self.ip_addr = ip_addr
        self.is_ok = 0
        self.items = items
    def run(self):
        r = subprocess.getstatusoutput(CMD.format(self.ip_addr))
        self.is_ok = 1 if r[0] == 0 else 0
        self.item = {
            "ip_addr": self.ip_addr,
            "is_ok": self.is_ok
        }
        self.items.append(self.item)


class Monitor:
    def __init__(self, ip_addr_list=[]):
        self.conn = pymysql.connect(**database)
        self.cursor = self.conn.cursor()
        self.ip_addr_list = ip_addr_list
        self.monitor_info = []
        self.time = datetime.datetime.now()
        self.check_mode = False

    def start_monitor(self, check_mode=False):

        if not self.ip_addr_list:
            if check_mode:
                self.check_mode = True
                self.get_ip_list_from_event()
            else:
                self.get_ip_list()

        threads = []
        for ip_addr in self.ip_addr_list:
            t = PING(ip_addr, self.monitor_info)
            threads.append(t)
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    def get_monitor_info(self):
        return self.monitor_info

    def get_ip_list(self):
        self.cursor.execute("SELECT ip_addr FROM ping_ip_addr_list_tb WHERE is_active = 1")
        self.ip_addr_list = [i[0] for i in self.cursor]

    def get_ip_list_from_event(self):
        self.cursor.execute("SELECT ip_addr FROM ping_failed_event")
        self.ip_addr_list = [i[0] for i in self.cursor]

    def db_store(self):
        if not self.check_mode:
            self.__status_store()
        self.__event_store()

    def __status_store(self):
        self.cursor.execute("TRUNCATE ping_ip_addr_status")
        self.conn.commit()
        self.cursor.executemany("INSERT INTO ping_ip_addr_status (ip_addr, is_ok, create_time) VALUES (%s, %s, %s)", ((i['ip_addr'], i['is_ok'], self.time) for i in self.monitor_info))
        self.cursor.executemany("INSERT INTO ping_ip_addr_status_history (ip_addr, is_ok, create_time) VALUES (%s, %s, %s)", ((i['ip_addr'], i['is_ok'], self.time) for i in self.monitor_info))
        self.conn.commit()

    def __event_store(self):
        # all types of events are set container
        self.__get_current_faied()
        self.get_last_failed()

        self.gone_events = self.last_failed - self.current_failed
        self.contin_events = self.current_failed - self.gone_events
        if not self.check_mode:
            self.new_events = self.current_failed - self.last_failed
            logging.info("new events : {}".format(self.new_events))
            if self.new_events:
                self.__create_event()
        logging.info("gone events : {}".format(self.gone_events))
        logging.info("contin events : {}".format(self.contin_events))

        self.__update_event()
        self.__delete_event()

        self.__event_alert()

    def __event_alert(self):
        ping_alert(self.current_failed, self.ignored_events, self.gone_events)

    def __create_event(self):
        self.cursor.executemany("INSERT INTO ping_failed_event (ip_addr, create_time, update_time) VALUES (%s, %s, %s)", ((ip_addr, self.time, self.time) for ip_addr in self.new_events))
        self.conn.commit()

    def __update_event(self):
        for i in self.contin_events:
            self.cursor.execute("UPDATE ping_failed_event SET update_time = %s WHERE ip_addr = %s", (self.time, i))
        self.conn.commit()

    def __delete_event(self):
        for i in self.gone_events:

            self.cursor.execute("SELECT ip_addr, create_time, update_time, is_ignored FROM ping_failed_event WHERE ip_addr = %s", (i, ))

            ip_addr, create_time, update_time, is_ignored = self.cursor.fetchall()[0]
            recover_time = self.time
            event = (ip_addr, create_time, update_time, is_ignored, recover_time)

            self.cursor.execute("INSERT INTO ping_failed_event_history (ip_addr, first_failed, last_failed, is_ignored, recover_time ) VALUES (%s, %s, %s, %s, %s)", event)
            self.cursor.execute("DELETE FROM ping_failed_event WHERE ip_addr = %s", (i,))
            self.conn.commit()

    def __get_current_faied(self):
        self.current_failed = {i['ip_addr'] for i in self.monitor_info if not i['is_ok']}

    def get_last_failed(self):
        self.cursor.execute("SELECT ip_addr, is_ignored FROM ping_failed_event")
        r = self.cursor.fetchall()

        self.last_failed =  {i[0] for i in r}
        self.ignored_events = {i[0] for i in r if i[1]}

    def close(self):
        self.cursor.close()
        self.conn.close()