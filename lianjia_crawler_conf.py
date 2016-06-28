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

## The regions to crawl, with name-id pair, id should be unique
region_def = {"松江大学城":"sjdxc", "罗阳":"ly"}
###########################################################
