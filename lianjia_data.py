#!/usr/bin/env python
# -*- coding: utf-8 -*-

# ALTER TABLE xz_data MODIFY COLUMN location char(64) CHARACTER SET utf8 COLLATE utf8_general_ci;
# CREATE TABLE xz_change_bk SELECT * FROM xz_change;
# ALTER TABLE xz_data MODIFY location char(64);
# LOAD DATA INFILE '/Users/Qiang/project/lianjia_crawler/data/2018+02+05+21+44+30/xz_data_mapped.csv' INTO TABLE xz_data CHARACTER SET utf8mb4 FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';
# LOAD DATA INFILE '/Users/Qiang/project/lianjia_crawler/data/2018+02+05+21+44+30/xz_change_mapped.csv' INTO TABLE xz_change FIELDS TERMINATED BY ',' LINES TERMINATED BY '\n';

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

DATA_DIR = "./data"
WORK_DIR = ""

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

    def export(self, fpath, tbl_name):
        ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S%f")
        tempfpath = "/tmp/" + "csv-" + ts
        cmd = "SELECT * FROM {tbl} INTO OUTFILE '{path}' "\
              "FIELDS TERMINATED BY ',' "\
              "LINES TERMINATED BY '\n';".format(tbl=tbl_name, path=tempfpath)
        try:
            self.execute(cmd)
        except:
            raise
        shutil.copy(tempfpath, fpath)

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

    def query_nts(self, aid, region):
        tbl = "{0}_data".format(region)
        cmd = "SELECT nts FROM {0} WHERE aid = '{1}'".format(tbl, aid)
        res = self.select(cmd)
        return res[0][0]

    def close(self):
        self.db.close()

    def parse_ts(self, ts):
        return datetime.datetime.strptime(ts, self.ts_fmt)

    def fmt_ts(self, t):
        return t.strftime(self.ts_fmt)

class Apartment(object):
    def __init__(self, csvline):
        cols = csvline.split(",")
        self.location = cols[0]
        self.aid = cols[1]
        self.price = int(cols[2])
        self.size = cols[3]
        self.total = int(cols[4])
        self.nts = db.parse_ts(cols[5])
        self.uts = db.parse_ts(cols[6])
        self.subway = int(cols[7])
        self.station = cols[8]
        self.smeter = int(cols[9])
        self.floor = cols[10]
        self.tfloor = int(cols[11])
        self.year = self.parse_year(cols[12])

    def parse_year(self, s):
        if s == "\\N":
            return 0
        else:
            return int(s)

    def fmt_year(self, year):
        if year == 0:
            return "\\N"
        else:
            return str(year)

    def csv(self):
        vals = []
        vals.append(self.location)
        vals.append(self.aid)
        vals.append(str(self.price))
        vals.append(self.size)
        vals.append(str(self.total))
        vals.append(db.fmt_ts(self.nts))
        vals.append(db.fmt_ts(self.uts))
        vals.append(str(self.subway))
        vals.append(self.station)
        vals.append(str(self.smeter))
        vals.append(self.floor)
        vals.append(str(self.tfloor))
        vals.append(self.fmt_year(self.year))
        return ",".join(vals)

    def __repr__(self):
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

class Change(object):
    def __init__(self, csvline=None, data=None):
        if csvline is not None:
            self.init_from_csv(csvline)
        else:
            self.aid = data[0]
            self.old_price = str(data[1])
            self.new_price = str(data[2])
            self.old_total = str(data[3])
            self.new_total = str(data[4])
            self.ts = data[5]

    def init_from_csv(self, csvline):
        cols = csvline.split(",")
        self.aid = cols[0]
        self.old_price = cols[1]
        self.new_price = cols[2]
        self.old_total = cols[3]
        self.new_total = cols[4]
        self.ts = db.parse_ts(cols[5])

    def csv(self):
        vals = []
        vals.append(self.aid)
        vals.append(self.old_price)
        vals.append(self.new_price)
        vals.append(self.old_total)
        vals.append(self.new_total)
        vals.append(db.fmt_ts(self.ts))
        return ",".join(vals)

def export_data(region):
    tbl = "{0}_data".format(region)
    fpath = WORK_DIR + os.sep + "{0}.csv".format(tbl)
    db.export(fpath, tbl)
    tbl = "{0}_change".format(region)
    fpath = WORK_DIR + os.sep + "{0}.csv".format(tbl)
    db.export(fpath, tbl)

def export_all_data():
    regions = ["cs", "ml", "sjdxc", "xz"]
    for region in regions:
        export_data(region)

def dump(apartments):
    print "{0} records".format(len(apartments))
    for apartment in apartments:
        print apartment

def load_apartments(region):
    datapath = WORK_DIR + os.sep + "{0}_data.csv".format(region)
    with open(datapath, "r") as fp:
        lines = fp.readlines()
    all_apartments = []
    for line in lines:
        apartment = Apartment(line.rstrip())
        all_apartments.append(apartment)
    return all_apartments

def load_changes(region):
    datapath = WORK_DIR + os.sep + "{0}_change.csv".format(region)
    with open(datapath, "r") as fp:
        lines = fp.readlines()
    all_changes = []
    for line in lines:
        all_changes.append(Change(line.rstrip()))
    return all_changes

def filter_regions():
    tbl = {}
    for region in regions:
        filter_region_data(region, tbl)
    path = WORK_DIR + os.sep + "aid_map.json"
    with open(path, "w") as fp:
        json.dump(tbl, fp, indent=2)
    return tbl

def filter_region_data(region, tbl):
    print "### processing region {0}".format(region)
    ts_fmt = "%Y-%m-%d %H:%M:%S"
    LAST_DAY_S = "2018-01-31 00:00:00"
    LAST_DAY = datetime.datetime.strptime(LAST_DAY_S, ts_fmt)
    FIRST_DAY_S = "2018-02-04 00:00:00"
    FIRST_DAY = datetime.datetime.strptime(FIRST_DAY_S, "%Y-%m-%d %H:%M:%S")
    all_apartments = load_apartments(region)
    oldgrp, newgrp = {}, {}
    for apartment in all_apartments:
        if apartment.nts > FIRST_DAY:
            dump([apartment])
        if apartment.uts < LAST_DAY or apartment.nts > FIRST_DAY:
            continue
        if apartment.aid.startswith("sh"):
            grp = oldgrp
        else:
            grp = newgrp
        lo = apartment.location
        if lo in grp:
            grp[lo].append(apartment)
        else:
            grp[lo] = [apartment]
    new_cnt, old_cnt = 0, 0
    for lo in newgrp:
        new_cnt += len(newgrp[lo])
        if lo not in oldgrp:
            print "{0} not found in new data".format(lo)
            dump(newgrp[lo])
    old_size = len(tbl)
    for lo in oldgrp:
        old_cnt += len(oldgrp[lo])
        if lo not in newgrp:
            print "{0} not found in new data".format(lo)
            continue
        map_grp(region, lo, tbl, oldgrp[lo], newgrp[lo])
    addon_size = len(tbl) - old_size
    ratio = float(addon_size)/float(min(old_cnt, new_cnt)) * 100
    print "Match ratio {0:.2f}%".format(ratio)

def map_grp(region, lo, tbl, old, new):
    print "### map {0}, old/new {1}/{2}".format(lo, len(old), len(new))
    matched = {}
    for n in new:
        candidates = []
        for o in old:
            if n.size == o.size and n.year == o.year and n.tfloor == o.tfloor \
               and n.floor == o.floor:
                candidates.append(o)
        if len(candidates) == 0:
            print "$$$ {0} no match".format(n.aid)
        elif len(candidates) == 1:
            print "$$$ {0} matches {1}".format(n.aid, candidates[0].aid)
            tbl[candidates[0].aid] = n.aid
            matched[n.aid] = True
        else:
            aids = []
            for o in candidates:
                aids.append(o.aid)
            print "$$$ {0} candidates {1}".format(n.aid, aids)
            res, aids = [], []
            for o in candidates:
                if o.total == n.total:
                    res.append(o)
                    aids.append(o.aid)
            if len(res) == 0:
                print "$$$ {0}, no match".format(n.aid, candidates)
            elif len(res) == 1:
                print "$$$ {0} matches {1}".format(n.aid, res[0].aid)
                tbl[res[0].aid] = n.aid
                matched[n.aid] = True
            else:
                print "$$$ {0}, too many match {1}".format(n.aid, aids)
                aid = search_closest(region, n.aid, aids)
                tbl[aid] = n.aid
                matched[n.aid] = True
                print "$$$ {0} matches {1}, closest".format(n.aid, aid)
        if n.aid in matched or len(candidates) > 0:
           continue
        candidates, aids = [], []
        for o in old:
            if n.total== o.total and n.year == o.year and n.tfloor == o.tfloor \
               and n.floor == o.floor:
                candidates.append(o)
                aids.append(o.aid)
        if len(candidates) == 0:
            print "$$$ {0} no match".format(n.aid)
        elif len(candidates) == 1:
            print "$$$ {0} matches {1}".format(n.aid, candidates[0].aid)
            tbl[candidates[0].aid] = n.aid
        else:
            print "$$$ {0}, too many match {1}".format(n.aid, aids)
    return tbl

def search_closest(region, naid, aids):
    nts = query_nts(naid)
    minDelta, target_aid = None, None
    for aid in aids:
        old_nts = db.query_nts(aid, region)
        delta = abs((old_nts - nts).total_seconds())
        if minDelta is None or delta < minDelta:
            minDelta = delta
            target_aid = aid
    return target_aid

def query_nts(aid):
    # 2017-08-13
    link = "https://sh.lianjia.com/ershoufang/{0}.html".format(aid)
    r = requests.get(link)
    tag = bs4.BeautifulSoup(r.text, "html.parser")
    result = tag.find_all("div", class_="newwrap baseinform", id="introduction")
    result = re.findall("挂牌时间</span>\n<span>([\d-]+)</span>",str(result[0]))
    t = datetime.datetime.strptime(result[0], "%Y-%m-%d")
    return t

def init_regions():
    regions = []
    for entry in region_def:
        regions.append(entry[1])
    return regions

def make_workdir():
    ts = datetime.datetime.now().strftime("%Y+%m+%d+%H+%M+%S")
    dirpath = DATA_DIR + os.sep + ts
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)
    global WORK_DIR
    WORK_DIR = dirpath

def rebuild_data(tbl):
    for region in regions:
        rebuild_one_region(region, tbl)

def rebuild_one_region(region, tbl):
    print "*** Rebuild region {0}".format(region)
    ts_fmt = "%Y-%m-%d %H:%M:%S"
    CHANGE_DATE_S = "2018-02-02 12:00:00"
    CHANGE_DATE = datetime.datetime.strptime(CHANGE_DATE_S, ts_fmt)
    apartments = load_apartments(region)
    changes = load_changes(region)
    lookup = {}
    for apartment in apartments:
        lookup[apartment.aid] = apartment
    for change in changes:
        if change.aid in tbl:
            change.aid = tbl[change.aid]
    rebuild = []
    for apartment in apartments:
        aid = apartment.aid
        if aid not in tbl:
            rebuild.append(apartment)
            continue
        naid = tbl[aid]
        if naid not in lookup:
            continue
        o, n = lookup[aid], lookup[naid]
        if o.total != n.total:
            data = [naid, o.price, n.price, o.total, n.total, CHANGE_DATE]
            changes.append(Change(data=data))
        n.nts = o.nts
    write_rebuild_apartments(region, rebuild)
    write_rebuild_changes(region, changes)

def write_rebuild_apartments(region, apartments):
    path = WORK_DIR + os.sep + "{0}_data_mapped.csv".format(region)
    with open(path, "w") as fp:
        for apartment in apartments:
            fp.write(apartment.csv())
            fp.write("\n")

def write_rebuild_changes(region, changes):
    path = WORK_DIR + os.sep + "{0}_change_mapped.csv".format(region)
    with open(path, "w") as fp:
        for change in changes:
            fp.write(change.csv())
            fp.write("\n")

make_workdir()
db = SQLDB()
regions = init_regions()
export_all_data()
tbl = filter_regions()
with open(WORK_DIR + os.sep + "aid_map.json", "r") as fp:
    tbl = json.load(fp)
rebuild_data(tbl)
