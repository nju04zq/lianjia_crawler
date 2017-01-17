#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import bs4
import sys
import time
import MySQLdb
import hashlib
import logging
import requests
import datetime
import tempfile
import subprocess
from lianjia_crawler_conf import MySQL_conf, region_def

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
        self.parse_subway(tag)
        self.parse_building(tag)

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
        result = tag.find_all("span", "num")
        result = re.findall("\d+", result[0].contents[0])
        self.total = int(result[0])
        result = tag.find_all("div", "price-pre")
        result = re.findall("\d+", result[0].contents[0])
        self.price = int(result[0])

    def parse_size(self, tag):
        result = tag.find_all("div", "where")
        result = re.findall("<span>(\d+\.\d+)", str(result[0]))
        self.size = result[0]

    def parse_subway(self, tag):
        result = tag.find_all("span", "fang-subway-ex")
        if len(result) == 0:
            self.subway = 0
            self.station = ""
            self.smeter = 0
            return

        result = re.findall("<span>(.*)</span>", str(result[0].contents[0]))
        result = re.findall("(\d+)号线(.*)站(\d+)米", result[0])
        self.subway = result[0][0]
        self.station = result[0][1]
        self.smeter = result[0][2]

    def parse_building(self, tag):
        result = tag.find_all("div", "con")
        result = re.findall("<span>\|[ ]*</span>(.*)\r?\n\t", str(result[0]))
        if len(result)  == 1:
            result += [result[0], result[0]]
        elif len(result) == 2:
            result.append(result[1])
        self.parse_floor(result[0])
        self.parse_year(result[2])

    def parse_floor(self, s):
        result = self.parse_normal_floor(s)
        if result:
            return
        result = self.parse_villa_floor(s)
        if result:
            return
        self.floor = "U"
        self.tfloor = 0

    def parse_normal_floor(self, s):
        result = re.findall("(.*)层/(\d+)层", s)
        if len(result) == 0:
            return False

        result = result[0]

        if result[0] == "低":
            self.floor = "L"
        elif result[0] == "中":
            self.floor = "M"
        elif result[0] == "高":
            self.floor = "H"
        else:
            self.floor = "U"

        self.tfloor = int(result[1])
        return True

    def parse_villa_floor(self, s):
        result = re.findall("(\d+)层", s)
        if len(result) == 0:
            return False

        self.floor = "V"
        self.tfloor = int(result[0])
        return True

    def parse_year(self, s):
        self.year = "NULL"

        result = re.findall("(\d+)", s)
        if len(result) == 0:
            return

        self.year = int(result[0])
        if self.year < 1000:
            self.year = "NULL"
        else:
            self.year = str(self.year)

    def __str__(self):
        result = ""
        result += "{}\n".format(self.aid)
        result += "{}\n".format(self.location)
        result += "{}\n".format(self.price)
        result += "{}\n".format(self.size)
        result += "{}\n".format(self.total)
        result += "{}/{}/{}\n".format(self.subway, self.station, self.smeter)
        result += "{}/{}\n".format(self.floor, self.tfloor)
        result += "{}\n".format(self.year)
        return result

#   CREATE TABLE xx(location CHAR(32) CHARACTER SET utf8,
#                   aid CHAR(32) CHARACTER SET utf8,
#                   price INT,
#                   size CHAR(32) CHARACTER SET utf8,
#                   total INT,
#                   nts DATETIME, # first recorded
#                   uts DATETIME, # recently updated
#                   subway INT,
#                   station CHAR(16) CHARACTER SET utf8,
#                   smeter INT,
#                   floor CHAR(4) CHARACTER SET utf8,
#                   tfloor INT,
#                   year INT,
#                   PRIMARY KEY (aid));
    def sql_insert(self, table_name):
        s = ""
        s += "'{}',".format(self.location)
        s += "'{}',".format(self.aid)
        s += "{},".format(self.price)
        s += "'{}',".format(self.size)
        s += "'{}',".format(self.total)
        s += "NOW(), NOW(),"
        s += "{},".format(self.subway)
        s += "'{}',".format(self.station)
        s += "{},".format(self.smeter)
        s += "'{}',".format(self.floor)
        s += "{},".format(self.tfloor)
        s += "{}".format(self.year)
        return "INSERT INTO {} VALUE({})".format(table_name, s)

    def sql_update(self, table_name):
        s = ""
        s += "price = {},".format(self.price)
        s += "size = '{}',".format(self.size)
        s += "total= {},".format(self.total)
        s += "subway= {},".format(self.subway)
        s += "station= '{}',".format(self.station)
        s += "smeter= {},".format(self.smeter)
        s += "floor= '{}',".format(self.floor)
        s += "tfloor= {},".format(self.tfloor)
        s += "year= {},".format(self.year)
        s += "uts = NOW()"
        return "UPDATE {} SET {} WHERE aid = '{}'".format(table_name,
                                                          s, self.aid)

    @staticmethod
    def csv_title():
        return "location,aid,price,size,total\n"

    def init_from_csv(self, csv):
        csv = csv.rstrip("\n")
        fields = csv.split(",")
        self.location = fields[0]
        self.aid = fields[1]
        self.price = int(fields[2])
        self.size = float(fields[3])
        self.total = fields[4]
        self.subway = int(fields[5])
        self.station = fields[6]
        self.smeter = int(fields[7])
        self.floor = fields[8]
        self.tfloor = int(fields[9])
        self.year = fields[10]

# location,aid,price,size,total,subway,station,smeter,floor,tfloor,year
    def csv(self):
        s = ""
        s += "{},".format(self.location)
        s += "{},".format(self.aid)
        s += "{},".format(self.price)
        s += "{},".format(self.size)
        s += "{},".format(self.total)
        s += "{},".format(self.subway)
        s += "{},".format(self.station)
        s += "{},".format(self.smeter)
        s += "{},".format(self.floor)
        s += "{},".format(self.tfloor)
        s += "{}\n".format(self.year)
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

def crawl_link(link, apartment_list):
    r = requests.get(link)
    soup = bs4.BeautifulSoup(r.text, "html.parser")

    apartment_tags = soup.find_all("div", "info-panel")
    for apartment_tag in apartment_tags:
        apartment = Apartment(tag=apartment_tag)
        apartment_list.append(apartment)

def crawl_one_page(region_id, page_id, apartment_list):
    full_link = crawl_regions[region_id].get_link(page_id)
    crawl_link(full_link, apartment_list)

def crawl_pages(region_id, page_start, page_end):
    apartment_list = []
    for page_id in xrange(page_start, page_end):
        crawl_one_page(region_id, page_id, apartment_list)
    return apartment_list

def crawl_page_process(region_id, csv_filepath, page_start, page_end):
    logging.debug("pid {}, crawl {}-{}".format(os.getpid(), page_start,
                                               page_end))
    fp = open(csv_filepath, mode="w")
    apartment_list = crawl_pages(region_id, page_start, page_end)
    for apartment in apartment_list:
        fp.write(apartment.csv())
    fp.close()
    logging.debug("{}-{}, written to {}".format(page_start, page_end,
                                                csv_filepath))

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
        args = [sys.executable, sys.argv[0], "subprocess",
                ctx.region_id, csv_filepath,
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
    fp_result = open(result_filename, mode="w")
    fp_result.write(Apartment.csv_title())
    for i in xrange(0, len(ctx.crawl_process_list)):
        csv_filepath = generate_tmp_csv_filepath(ctx.tmpfile_base, i)
        fp_tmp = open(csv_filepath, mode="r")
        csv_data = fp_tmp.read()
        fp_tmp.close()
        os.remove(csv_filepath)
        fp_result.write(csv_data)
    fp_result.close()
    ctx.result_csv = result_filename
    logging.debug("Collect all results into {}".format(ctx.result_csv))

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
             size CHAR(32) CHARACTER SET utf8,
             total INT,
             nts DATETIME,
             uts DATETIME,
             subway INT,
             station CHAR(16) CHARACTER SET utf8,
             smeter INT,
             floor CHAR(4) CHARACTER SET utf8,
             tfloor INT,
             year INT,
             PRIMARY KEY (aid));'''.format(table_name)
    db.create_table(table_name, cmd)

def create_region_change_table(ctx, db):
    table_name = ctx.region_change_table
    cmd = '''CREATE TABLE {}(aid CHAR(32) CHARACTER SET utf8,
             old_price INT,
             new_price INT,
             old_total INT,
             new_total INT,
             ts DATETIME);'''.format(table_name)
    db.create_table(table_name, cmd)

def create_db_trigger(ctx, db):
    trigger_name = ctx.region_trigger
    cmd = '''CREATE TRIGGER {} AFTER UPDATE ON {} FOR EACH ROW
             BEGIN
                 IF OLD.price <> NEW.price THEN
                     INSERT INTO {} VALUE(OLD.aid, OLD.price, NEW.price,
                                          OLD.total, NEW.total, NOW());
                 END IF;
                 IF OLD.size <> NEW.size THEN
                     INSERT INTO {} VALUE(OLD.aid, ROUND(OLD.size),
                                          ROUND(NEW.size), OLD.total,
                                          NEW.total, NOW());
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

# Could use SQL "REPLACE INTO", but in that way not possible let trigger happen
def update_apartment_into_db(ctx, db, apartment):
    if is_apartment_in_db(ctx, db, apartment):
        db.update(apartment.sql_update(ctx.region_data_table))
        logging.debug("updated {}".format(apartment.aid))
    else:
        db.insert(apartment.sql_insert(ctx.region_data_table))
        logging.debug("insert {}".format(apartment.aid))

def update_db(ctx):
    db = prepare_db(ctx)
    fp = open(ctx.result_csv, mode="r")
    fp.readline() #skip heading column stating
    apartment_cnt = 0
    for csv_line in fp.readlines():
        apartment = Apartment(csv=csv_line)
        update_apartment_into_db(ctx, db, apartment)
        apartment_cnt += 1
    fp.close()
    db.close()
    logging.critical("updated {} apartments".format(apartment_cnt))

def get_region_maxpage(ctx):
    full_link = crawl_regions[ctx.region_id].get_link(1)
    r = requests.get(full_link)
    s = r.text

    soup = bs4.BeautifulSoup(s, "html.parser")

    try:
        result = soup.find_all("div", "page-box house-lst-page-box")
        pages = re.findall(">(\d+)<", str(result[0]))
        maxpage = int(pages[-1])
        ctx.maxpage = maxpage
        logging.critical("Region maxpage {}".format(ctx.maxpage))
    except:
        print "Fail to get maxpage, lianjia resp:"
        print r.text
        raise

def crawl_one_region(ctx):
    region_name = crawl_regions[ctx.region_id].region_name
    logging.critical("crawl region {}".format(region_name))
    get_region_maxpage(ctx)
    create_crawl_subprocess(ctx)
    wait_for_crawl_subprocess(ctx)
    collect_crawl_result(ctx)
    update_db(ctx)

def get_region_data_table_name(region_id):
    return "{}_data".format(region_id)

def get_region_change_table_name(region_id):
    return "{}_change".format(region_id)

class CrawlRegion(object):
    def __init__(self, param):
        self.region_name = param[0]
        self.region_id = param[1]
        if len(param) > 2:
            self.big_region = param[2]
        else:
            self.big_region = None

    def get_link(self, page):
        if self.big_region is None:
            base_link = "http://sh.lianjia.com/ershoufang/d{}s3rs{}"
            full_link = base_link.format(page, self.region_name)
        else:
            base_link = "http://sh.lianjia.com/ershoufang/{}/d{}s3"
            full_link = base_link.format(self.big_region, page)
        return full_link

class CrawlContext(object):
    def __init__(self, region_id):
        self.region_id = region_id
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

def make_region_table(crawl_regions):
    for param in region_def:
        region = CrawlRegion(param)
        if crawl_regions.has_key(region.region_id):
            raise Exception("Duplicate region id {}".format(region.region_id))
        else:
            crawl_regions[region.region_id] = region

def crawl_main():
    logging.critical("crawl start")
    for region_id in crawl_regions.keys():
        ctx = CrawlContext(region_id)
        crawl_one_region(ctx)
        ctx.clean()
    logging.critical("crawl done")

###########################################################
##########        Crawl Configurations           ##########
##########        Think before change            ##########
###########################################################
## How many processes to crawl for a region at the same time
crawl_process_cnt = 4

## lianjia web link
lianjia_link = "http://sh.lianjia.com/ershoufang/d{}s3rs{}"
###########################################################

##--------------------START Test Code----------------------------##

def run_test_set_mysql_db_name():
    MySQL_conf["db"] = "lianjia_test"

def run_test(args):
    run_test_set_mysql_db_name()
    if args[0] == "csv_input":
        run_test_csv_input(args[1])
    elif args[0] == "link":
        run_test_link()
    else:
        crawl_main()

def run_test_csv_input(csv_filename):
    region_id = crawl_regions.keys()[0]
    ctx = CrawlContext(region_id)
    ctx.result_csv = csv_filename
    update_db(ctx)

def run_test_link():
    apartment_list = []
    crawl_link("http://sh.lianjia.com/ershoufang/putuo/s2rs",
               apartment_list)
    for apartment in apartment_list:
        print apartment

##--------------------END Test Code----------------------------##

if __name__ == "__main__":
    crawl_regions = {}

    init_logging()
    reload(sys)
    sys.setdefaultencoding("utf-8")

    make_region_table(crawl_regions)

    if len(sys.argv) > 1 and sys.argv[1] == "runtest":
        run_test(sys.argv[2:])
        sys.exit()

    # argv: "subprocess"/region_id/tmp_csv_file_path/page_start/page_end
    if len(sys.argv) > 1 and sys.argv[1] == "subprocess":
        crawl_page_process(sys.argv[2], sys.argv[3], int(sys.argv[4]),
                           int(sys.argv[5]))
        sys.exit()

    crawl_main()
