#!/usr/bin/env python
# -*- coding: utf-8 -*-

###########################################################
##########        Crawl Configurations           ##########
###########################################################
## MySQL configurations
## Create database with "CREATE DATABASE lianjia;" first
MySQL_conf = {
        "host": "localhost",
        "user": "root",
        "passwd": "",
        "db": "lianjia",
        "charset": "utf8"}

## The regions to crawl, with name/id pair, id should be unique.
## If you want to search for a big-region(板块) in lianjia, also need its
## abbreviation defines in lianjia as the 3rd parameter.
## To get that abbreviation, go to http://sh.lianjia.com/ershoufang/, and
## choose the big-region you are interested in(区域部分), the xx string in
## sh.lianjia.com/ershoufang/xx/ is the one we need.
region_def = [("松江大学城", "sjdxc"),
              ("罗阳", "ly"),
              ("梅陇", "ml", "meilong"),
              ("春申", "cs", "chunshen"),
              ("莘庄", "xz", "shenzhuang"),
              ("张江", "zj", "zhangjiang"),
             ]
###########################################################
