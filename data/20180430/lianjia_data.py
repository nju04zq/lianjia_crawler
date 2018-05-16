#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import bs4
import json
import shutil
import MySQLdb
import logging
import datetime
import requests
from lianjia_crawler_conf import MySQL_conf, region_def

class SQLDB(object):
    # 2016-07-21 11:16:52
    ts_fmt = "%Y-%m-%d %H:%M:%S"

    def __init__(self):
        self.db_name = MySQL_conf["db"]
        self.db = MySQLdb.connect(**MySQL_conf)
        self.cursor = self.db.cursor()

    def execute(self, cmd):
        try:
            self.cursor.execute(cmd)
            self.db.commit()
        except:
            logging.error("Fail to execute {}".format(cmd))
            self.db.rollback()
            raise

    def select(self, cmd):
        try:
            self.cursor.execute(cmd)
            if self.cursor.rowcount == 0:
                return []
            else:
                return self.cursor.fetchall()
        except:
            logging.error("Fail to execute {}".format(cmd))
            raise

    def close(self):
        self.db.close()

db = SQLDB()
locations = db.select('select distinct location from xz_data where nts < "2018-04-28";')
apartments = db.select('select aid,location from xz_data where nts >= "2018-04-28";')
aids = []
for aid, location in apartments:
    if location not in locations:
        aids.append(aid)
        db.execute('delete from xz_data where aid = "{0}"'.format(aid))
        db.execute('delete from xz_change where aid = "{0}"'.format(aid))
print len(aids)
