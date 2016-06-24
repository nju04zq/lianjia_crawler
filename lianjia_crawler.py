#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import bs4
import sys
import time
import codecs
import MySQLdb
import hashlib
import logging
import requests
import datetime
import tempfile
import subprocess

class Apartment(object):
    def __init__(self, tag=None, csv=None):
        if tag is not None:
            self.init_from_tag(tag)
        elif csv is not None:
            self.init_from_csv(csv)
        else:
            raise Exception("Trying to init apartment from None")

    def init_from_tag(self, tag):
        self.parse_href(tag)
        self.parse_location(tag)
        self.parse_price(tag)
        self.parse_size(tag)
        self.parse_id()

        if self.aid == "":
            raise Exception("Apartment id could not be empty")

    def parse_id(self):
        self.aid = self.href.split("/")[-1].split(".")[0]

    def is_href_tag(self, tag):
        if tag.has_attr("name") and tag["name"] == "selectDetail":
            return True
        else:
            return False

    def parse_href(self, tag):
        result = tag.find_all(self.is_href_tag)
        self.href = result[0]["href"]

    def parse_location(self, tag):
        result = tag.find_all("div", "where")
        result = result[0].find_all("span", "nameEllipsis")
        self.location = result[0]["title"]

    def parse_price(self, tag):
        result = tag.find_all("div", "price-pre")
        result = re.findall("\d+", result[0].contents[0])
        self.price = int(result[0])

    def parse_size(self, tag):
        result = tag.find_all("div", "where")
        result = re.findall("<span>(\d+\.\d+)", str(result[0]))
        self.real_size = result[0]
        self.size = int(round(float(self.real_size)))

    def __str__(self):
        result = ""
        result += "{}\n".format(self.location)
        result += "{}\n".format(self.price)
        result += "{}\n".format(self.size)
        result += "{}\n".format(self.real_size)
        result += "{}\n".format(self.href)
        return result

#   CREATE TABLE xx(location CHAR(32) CHARACTER SET utf8,
#                   aid CHAR(32) CHARACTER SET utf8,
#                   price INT,
#                   size INT,
#                   real_size CHAR(32) CHARACTER SET utf8,
#                   ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
#                   PRIMARY KEY (aid));
    def sql_insert(self, table_name):
        s = ""
        s += "'{}',".format(self.location)
        s += "'{}',".format(self.aid)
        s += "{},".format(self.price)
        s += "{},".format(self.size)
        s += "'{}',".format(self.real_size)
        s += "NOW()"
        return "INSERT INTO {} VALUE({})".format(table_name, s)

    def sql_update(self, table_name):
        s = ""
        s += "price = {},".format(self.price)
        s += "size = {},".format(self.size)
        s += "ts = NOW()"
        return "UPDATE {} SET {} WHERE aid = '{}'".format(table_name,
                                                          s, self.aid)

    @staticmethod
    def csv_title():
        return "location,aid,price,size,real_size\n"

    def init_from_csv(self, csv):
        csv = csv.rstrip("\n")
        fields = csv.split(",")
        self.location = fields[0]
        self.aid = fields[1]
        self.price = int(fields[2])
        self.size = int(fields[3])
        self.real_size = fields[4]

# location,aid,price,size,real_size
    def csv(self):
        s = ""
        s += "{},".format(self.location)
        s += "{},".format(self.aid)
        s += "{},".format(self.price)
        s += "{},".format(self.size)
        s += "{}\n".format(self.real_size)
        return s

class SQLDB(object):
    def __init__(self):
        self.db_name = MySQL_conf["db"]
        self.db = MySQLdb.connect(**MySQL_conf)
        self.cursor = self.db.cursor()

    def create_table(self, table_name, create_cmd):
        cmd = "SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES WHERE "\
              "TABLE_SCHEMA = '{}' AND TABLE_NAME = '{}';"
        cmd = cmd.format(self.db_name, table_name)
        result = self.select(cmd)
        if len(result) == 0:
            self.execute(create_cmd)

    def create_trigger(self, trigger_name, create_cmd):
        cmd = "SELECT TRIGGER_NAME FROM INFORMATION_SCHEMA.TRIGGERS WHERE "\
              "TRIGGER_SCHEMA = '{}' AND TRIGGER_NAME = '{}';"
        cmd = cmd.format(self.db_name, trigger_name)
        result = self.select(cmd)
        if len(result) == 0:
            self.execute(create_cmd)

    def execute(self, cmd):
        try:
            self.cursor.execute(cmd)
            self.db.commit()
        except:
            logging.error("Fail to execute {}".format(cmd))
            self.db.rollback()
            raise

    def insert(self, cmd):
        self.execute(cmd)

    def update(self, cmd):
        self.execute(cmd)

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

def crawl_one_page(region, page_id, apartment_list):
    full_link = lianjia_link.format(page_id, region)
    r = requests.get(full_link)
    soup = bs4.BeautifulSoup(r.text)

    apartment_tags = soup.find_all("div", "info-panel")
    for apartment_tag in apartment_tags:
        apartment = Apartment(tag=apartment_tag)
        apartment_list.append(apartment)

def crawl_pages(region, page_start, page_end):
    apartment_list = []
    for page_id in xrange(page_start, page_end):
        crawl_one_page(region, page_id, apartment_list)
    return apartment_list

def crawl_page_process(region, csv_filepath, page_start, page_end):
    logging.debug("pid {}, crawl {}-{}".format(os.getpid(), page_start,
                                               page_end))
    fp = codecs.open(csv_filepath, mode="w", encoding="utf-8")
    apartment_list = crawl_pages(region, page_start, page_end)
    for apartment in apartment_list:
        fp.write(apartment.csv())
    fp.close()
    logging.debug("{}-{}, written to {}".format(page_start, page_end,
                                                csv_filepath))

def get_region_maxpage(ctx):
    full_link = lianjia_link.format(1, ctx.region)
    r = requests.get(full_link)
    s = r.text

    soup = bs4.BeautifulSoup(s)

    result = soup.find_all("div", "page-box house-lst-page-box")
    pages = re.findall(">(\d+)<", str(result[0]))
    maxpage = int(pages[-1])
    ctx.maxpage = maxpage

def generate_tmp_csv_filepath(tmpfile_base, i):
    csv_filepath = tmpfile_base + "_{}.csv".format(i)
    return csv_filepath

def create_crawl_subprocess(ctx):
    maxpage = ctx.maxpage
    page_load = (maxpage + ctx.crawl_process_cnt - 1) / ctx.crawl_process_cnt
    page_start, i = 1, 0
    process_list = []
    while maxpage > 0:
        page_load = min(maxpage, page_load)
        csv_filepath = generate_tmp_csv_filepath(ctx.tmpfile_base, i)
        args = [sys.argv[0], "subprocess", ctx.region, csv_filepath,
                str(page_start), str(page_start + page_load)]
        process = subprocess.Popen(args)
        process_list.append(process)
        maxpage -= page_load
        page_start += page_load
        i += 1
    ctx.crawl_process_list = process_list

def wait_for_crawl_subprocess(ctx):
    process_list = ctx.crawl_process_list
    while len(process_list) > 0:
        new_list = []
        for process in process_list:
            rc = process.poll()
            if rc is None:
                new_list.append(process)
        process_list = new_list
        time.sleep(0.1)

def collect_crawl_result(ctx):
    result_filename = ctx.tmpfile_base + "_total"
    fp_result = codecs.open(result_filename, mode="w", encoding="utf-8")
    fp_result.write(Apartment.csv_title())
    for i in xrange(0, len(ctx.crawl_process_list)):
        csv_filepath = generate_tmp_csv_filepath(ctx.tmpfile_base, i)
        fp_tmp = codecs.open(csv_filepath, mode="r", encoding="utf-8")
        csv_data = fp_tmp.read()
        fp_tmp.close()
        os.remove(csv_filepath)
        fp_result.write(csv_data)
    fp_result.close()
    ctx.result_csv = result_filename

def prepare_db(ctx):
    db = SQLDB()
    create_region_data_table(ctx, db)
    create_region_change_table(ctx, db)
    create_db_trigger(ctx, db)
    return db

def create_region_data_table(ctx, db):
    table_name = ctx.region_data_table
    cmd = '''CREATE TABLE {}(location CHAR(32) CHARACTER SET utf8,
             aid CHAR(32) CHARACTER SET utf8,
             price INT,
             size INT,
             real_size CHAR(32) CHARACTER SET utf8,
             ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
             PRIMARY KEY (aid));'''.format(table_name)
    db.create_table(table_name, cmd)

def create_region_change_table(ctx, db):
    table_name = ctx.region_change_table
    cmd = '''CREATE TABLE {}(aid CHAR(32) CHARACTER SET utf8,
             old_price INT,
             new_price INT,
             ts TIMESTAMP DEFAULT CURRENT_TIMESTAMP);'''.format(table_name)
    db.create_table(table_name, cmd)

def create_db_trigger(ctx, db):
    trigger_name = ctx.region_trigger
    cmd = '''CREATE TRIGGER {} AFTER UPDATE ON {} FOR EACH ROW
             BEGIN
                 IF OLD.price <> NEW.price THEN
                     INSERT INTO {} VALUE(OLD.aid, OLD.price, NEW.price, NULL);
                 END IF;
                 IF OLD.size <> NEW.size THEN
                     INSERT INTO {} VALUE(OLD.aid, OLD.size, NEW.size, NULL);
                 END IF;
             END'''.format(trigger_name, ctx.region_data_table,
                           ctx.region_change_table, ctx.region_change_table)
    db.create_trigger(trigger_name, cmd)

def is_apartment_in_db(ctx, db, apartment):
    cmd = "SELECT * FROM {} WHERE aid = \"{}\";".format(ctx.region_data_table,
                                                        apartment.aid)
    result = db.select(cmd)
    if len(result) == 0:
        return False
    else:
        return True

def update_apartment_into_db(ctx, db, apartment):
    if is_apartment_in_db(ctx, db, apartment):
        db.update(apartment.sql_update(ctx.region_data_table))
    else:
        db.insert(apartment.sql_insert(ctx.region_data_table))

def update_db(ctx):
    db = prepare_db(ctx)
    fp = codecs.open(ctx.result_csv, mode="r", encoding="utf-8")
    fp.readline() #skip heading column stating
    for csv_line in fp.readlines():
        apartment = Apartment(csv=csv_line)
        update_apartment_into_db(ctx, db, apartment)
    fp.close()
    db.close()

def crawl_one_region(ctx):
    logging.debug("crawl region {}".format(ctx.region))
    get_region_maxpage(ctx)
    create_crawl_subprocess(ctx)
    wait_for_crawl_subprocess(ctx)
    collect_crawl_result(ctx)
    update_db(ctx)

class CrawlContext(object):
    def __init__(self, region):
        self.region = region
        self.region_id = region_def[region]
        self.tmpfile_base = self.generate_tmpfile_base()
        self.maxpage = 0
        self.crawl_process_cnt = crawl_process_cnt
        self.crawl_process_list = []
        self.result_csv = ""
        self.region_data_table = "{}_data".format(self.region_id)
        self.region_change_table = "{}_change".format(self.region_id)
        self.region_trigger = "{}_trigger".format(self.region_id)

    def generate_tmpfile_base(self):
        now = "{}".format(datetime.datetime.now())
        s = hashlib.md5(now).hexdigest()
        tempdir = tempfile.gettempdir()
        return tempdir + os.sep + "lianjia_" + s

    def clean(self):
        os.remove(self.result_csv)

def init_logging():
    logging.basicConfig(format="%(asctime)s %(message)s",
                        level=logging.ERROR)

def validate_region_def():
    region_id_set = set()
    for region in region_def.keys():
        region_id = region_def[region]
        if region_id in region_id_set: 
            raise Exception("Duplicate region id {}".format(region_id))
        else:
            region_id_set.add(region_id)

###########################################################
##########        Crawl Configurations           ##########
###########################################################
## MySQL configurations
## Create database with "CREATE DATABASE lianjia;" first
MySQL_conf = {
        "host": "localhost",
        "user": "dir",
        "passwd": "123",
        "db": "lianjia",
        "charset": "utf8"}

## The regions to crawl, with name-id pair, id should be unique
region_def = {"松江大学城":"sjdxc", "罗阳":"ly"}

## How many processes to crawl for a region at the same time
crawl_process_cnt = 4

## lianjia web link
lianjia_link = "http://sh.lianjia.com/ershoufang/d{}rs{}"
###########################################################

if __name__ == "__main__":
    init_logging()
    reload(sys)
    sys.setdefaultencoding("utf-8")

    # argv: "subprocess"/region/tmp_csv_file_path/page_start/page_end
    if len(sys.argv) > 1 and sys.argv[1] == "subprocess":
        crawl_page_process(sys.argv[2], sys.argv[3], int(sys.argv[4]),
                           int(sys.argv[5]))
        sys.exit()

    validate_region_def()

    logging.critical("crawl start")
    for region in region_def.keys():
        ctx = CrawlContext(region)
        crawl_one_region(ctx)
        ctx.clean()
    logging.critical("crawl done")
