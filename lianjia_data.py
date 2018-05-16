#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import shutil
import tarfile
import datetime
from lianjia_crawler import SQLDB, CrawlContext, prepare_db
from lianjia_crawler_conf import region_def

def export():
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    dirname = "data-{0}".format(ts)
    os.mkdir(dirname)
    path = os.path.abspath(dirname)
    db = SQLDB()
    for region in region_def:
        region_id = region[1]
        export_one_table(db, path, region_id+"_data")
        export_one_table(db, path, region_id+"_change")
    tgz_fname = path + ".tgz"
    with tarfile.open(tgz_fname, "w:gz") as tf:
        for fname in os.listdir(path):
            tf.add(os.path.join(dirname, fname))
    shutil.rmtree(path)
    db.close()
    print "Data packed to {0}".format(tgz_fname)

def export_one_table(db, path, tbl_name):
    ts = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    fname = tbl_name+".csv"
    src = os.path.join("/tmp", fname+ts)
    dst = os.path.join(path, fname)
    print "Export to {0}.csv".format(tbl_name)
    cmd = "SELECT * FROM {tbl} INTO OUTFILE '{fname}' "\
          "FIELDS TERMINATED BY ',' ENCLOSED BY '\"'"\
          "LINES TERMINATED BY '\r\n'".format(tbl=tbl_name, fname=src)
    db.execute(cmd)
    shutil.copyfile(src, dst)
    # can't remove it, permission problem
    #os.remove(src)

def import_(tgz_fname):
    with tarfile.open(tgz_fname, "r:gz") as tf:
        tf.extractall()
    dirname = tgz_fname.rstrip(".tgz")
    path = os.path.abspath(dirname)
    create_tables()
    db = SQLDB()
    res = []
    for fname in os.listdir(path):
        fpath = os.path.join(path, fname)
        import_one_file(db, fpath, res)
    shutil.rmtree(dirname)
    db.close()
    print "Import from {0} done.".format(tgz_fname)
    show_result(res)

def create_tables():
    for region in region_def:
        region_id = region[1]
        ctx = CrawlContext(region_id)
        prepare_db(ctx)

def import_one_file(db, fpath, res):
    tbl_name = os.path.basename(fpath).rstrip(".csv")
    print "Import table {0}".format(tbl_name)
    cmd = "LOAD DATA LOCAL INFILE '{fpath}' INTO TABLE {tbl_name} "\
          "CHARACTER SET utf8mb4 "\
          "FIELDS TERMINATED BY ',' ENCLOSED BY '\"' "\
          "LINES TERMINATED BY '\r\n'".format(fpath=fpath, tbl_name=tbl_name)
    db.execute(cmd)
    db_lines = db.select("SELECT COUNT(*) from {tbl_name}".format(\
                         tbl_name=tbl_name))[0][0]
    with open(fpath, "r") as fp:
        file_lines = len(fp.readlines())
    res.append((tbl_name, file_lines, db_lines))

class PrettyTable(object):
    def __init__(self, header, lines):
        self.header = header
        self.lines = lines
        self.col_limit = self.get_table_col_limit()
        # pad the seperator between columns
        self.col_seperator = "  "

    # print the whole table
    def show(self):
        sys.stdout.write(self.format())

    # format the whole table, return string
    def format(self):
        output = ""
        output += self.format_table_one_line(self.header)
        output += self.format_table_seperator()
        for oneline in self.lines:
            output += self.format_table_one_line(oneline)
        return output

    # calculate the width limit for each column in table
    def get_table_col_limit(self):
        self.lines.append(self.header)
        col_cnt = len(self.header)
        col_limit = [0 for i in xrange(col_cnt)]
        for line in self.lines:
            if len(line) != col_cnt:
                raise Exception("Table line {0} not match header {1}".format(\
                                line, self.header))
            for i in xrange(len(col_limit)):
                col_limit[i] = max(col_limit[i], len(line[i]))
        self.lines.pop()
        return col_limit

    # format one line in the table, each line is defined by a tuple containing
    # column values. If column value string length is less than the column width
    # limit, extra spaces will be padded
    def format_table_one_line(self, line):
        output = ""
        cols = []
        for i in xrange(len(line)):
            s = ""
            s += line[i]
            s += (" " * (self.col_limit[i]-len(line[i])))
            cols.append(s)
        output += (self.col_seperator.join(cols) + "\n")
        return output

    # format the seperator as -------
    def format_table_seperator(self):
        sep_cnt = sum(self.col_limit)
        # count in column seperators, why -1?, 2 columns only have one
        sep_cnt += (len(self.col_limit) - 1)*len(self.col_seperator)
        # one extra sep to make it pretty
        sep_cnt += 1
        return "-" * sep_cnt + "\n"

def show_result(results):
    header = ["Name", "File lines", "DB lines", "OK?"]
    lines = []
    for res in results:
        line = [str(x) for x in res]
        if res[1] == res[2]:
            line.append("---")
        else:
            line.append("???")
        lines.append(line)
    tbl = PrettyTable(header, lines)
    tbl.show()

def main():
    if len(sys.argv) <= 1:
        print "Tell me what to do"
    elif sys.argv[1] == "export":
        export_()
    elif sys.argv[1] == "import":
        if len(sys.argv) <=2:
            print "Tell me the file to import"
        else:
            import_(sys.argv[2])
    else:
        print "Not support {0}".format(sys.argv[1])

if __name__ == "__main__":
    main()
