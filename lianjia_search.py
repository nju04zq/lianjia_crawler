#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cgi
import sys
import logging
import collections
from html_page import *
from lianjia_crawler_conf import *
from lianjia_crawler import SQLDB, \
                            get_region_data_table_name, \
                            get_region_change_table_name

def get_script_name():
    if os.environ.has_key("SCRIPT_NAME"):
        script_name = os.environ["SCRIPT_NAME"]
    else:
        script_path = os.path.abspath(__file__)
        script_name = os.path.basename(script_path)
    return script_name

def get_request_uri():
    if os.environ.has_key("REQUEST_URI"):
        request_uri = os.environ["REQUEST_URI"]
    else:
        request_uri = get_script_name()
    return request_uri

def add_to_query_table_old_query(query_param_table, old_query_str):
    if old_query_str == "":
        return
    params = old_query_str.split("&")
    for param in params:
        key_value_pair = param.split("=")
        key = key_value_pair[0]
        value = key_value_pair[1]
        if query_param_table.has_key(key):
            query_param_table[key].append(value)
        else:
            query_param_table[key] = [value]

def add_to_query_table_new_query(query_param_table, new_param_table):
    for key in new_param_table.keys():
        value = new_param_table[key]
        if query_param_table.has_key(key):
            query_param_table[key] += value
        else:
            query_param_table[key] = value

def generate_query_str(new_param_table, old_query_str):
    query_param_table = collections.OrderedDict()
    add_to_query_table_old_query(query_param_table, old_query_str)
    add_to_query_table_new_query(query_param_table, new_param_table)
    s = ""
    for key in query_param_table.keys():
        values = query_param_table[key]
        values = list(set(values))
        for value in values:
            if s != "":
                s += "&"
            s += "{}={}".format(urllib.quote(key), urllib.quote(value))
    return s

def request_uri_append_query_param(new_param_table):
    ## this case for test on local machine
    if not os.environ.has_key("QUERY_STRING") or \
       not os.environ.has_key("SCRIPT_NAME"):
       return "pending"
    script_name = os.environ["SCRIPT_NAME"]
    old_query_str = os.environ["QUERY_STRING"]
    query_str = generate_query_str(new_param_table, old_query_str)
    s = "{}?{}".format(script_name, query_str)
    return s

def create_html_page():
    page = HtmlPage()
    page.get_head().set_title("Lianjia Search")
    return page

def get_region_id_list():
    a = []
    for region in region_def.keys():
        a.append(region_def[region])
    return a

def get_defined_region_cnt():
    cnt = len(region_def.keys())
    return cnt

def get_region_full_str(region_id):
    for region_full in region_def.keys():
        if region_id == region_def[region_full]:
            return region_full
    return None

def compose_search_regions(form, default_region_id):
    popup = HtmlPopupMenu()
    popup.set_attrib_name(SearchEnv.s_region)

    form.add_entry(HtmlLiteral("Region:"))
    form.add_entry(HtmlSpace(2))
    form.add_entry(popup)

    region_id_list = get_region_id_list()
    for region_id in region_id_list:
        opt = HtmlOption()
        popup.add_entry(opt)
        opt.set_value(get_region_full_str(region_id))
        opt.set_attrib_value(region_id)
        if region_id == default_region_id:
            opt.set_selected()

def compose_search_types(form, default_search_type):
    popup = HtmlPopupMenu()
    popup.set_attrib_name(SearchEnv.s_type)

    form.add_entry(HtmlLiteral("Data type:"))
    form.add_entry(HtmlSpace(2))
    form.add_entry(popup)

    search_types = SearchEnv.search_types
    for search_type in search_types:
        opt = HtmlOption()
        popup.add_entry(opt)
        opt.set_value(SearchEnv.get_search_type_desc(search_type))
        opt.set_attrib_value(search_type)
        if search_type == default_search_type:
            opt.set_selected()

def compose_submit(form):
    submit = HtmlSubmit()
    submit.set_attrib_value("search")
    form.add_entry(submit)

def compose_html_search(body, search_env):
    if get_defined_region_cnt() == 0:
        return

    form = HtmlForm()
    body.add_element(form)
    form.set_action(get_script_name())

    compose_search_regions(form, search_env.region_id)
    form.add_entry(HtmlSpace(4))
    compose_search_types(form, search_env.search_type)
    form.add_entry(HtmlSpace(4))
    compose_submit(form)

def compose_error_paragraph(body, error_msg):
    p = HtmlParagraph()
    body.add_element(p)
    p.set_color("red")
    p.set_value(error_msg)

def display_error_page(error_msg):
    page = create_html_page()
    body = page.get_body()
    compose_html_search(body, default_search_env)
    compose_error_paragraph(body, error_msg)
    print page

def display_default_page():
    page = create_html_page()
    body = page.get_body()
    compose_html_search(body, default_search_env)
    print page

class SearchApartmentBase(object):
    columns = ["aid", "location", "price", "size", "total", "nts", "uts"]
    column_map = {"aid":"房源编号", "location":"小区", "price":"单价",
                  "size":"面积", "total":"总价",
                  "nts":"上架日期", "uts":"更新日期"}
    column_trim = {"size":"ROUND(size)", "nts":"DATE(nts)", "uts":"DATE(uts)"}
    default_columns = ["aid", "location", "price", "size", "total", "uts"]

    def __init__(self, region_id, show_column_ids):
        self.region_id = region_id
        self.show_columns = self.get_show_columns(show_column_ids)

    def get_show_columns(self, show_columns_ids):
        if len(show_columns_ids) == 0:
            return self.default_columns
        show_columns_ids.sort()
        show_columns = []
        for column_id in show_columns_ids:
            if column_id < 0 or column_id >= len(columns):
                continue
            show_columns.append(columns[column_id])
        return show_columns

    def make_sql_column_str(self):
        show_columns = []
        for column in self.show_columns:
            if self.column_trim.has_key(column):
                column = self.column_trim[column]
            show_columns.append(column)
        column_str = ",".join(show_columns)
        return column_str

    def search_all(self):
        if len(self.show_columns) == 0:
            self.rows = []
            return
        column_str = self.make_sql_column_str()
        table_name = get_region_data_table_name(self.region_id)
        sql_cmd = "SELECT {} FROM {} "\
                  "ORDER BY uts DESC, price;".format(column_str, table_name)
        db = SQLDB()
        logging.debug(sql_cmd)
        self.rows = db.select(sql_cmd)

    def make_html_table(self, body):
        table = HtmlTable()
        body.add_element(table)
        tr = self.make_html_table_header_row()
        table.add_row(tr)
        for row in self.rows:
            tr = self.make_html_table_row(row)
            table.add_row(tr)

    def make_html_table_header_row(self):
        tr = HtmlTableRow()
        for column in self.show_columns:
            header = HtmlTableHeader()
            header.set_value(self.column_map[column])
            tr.add_cell(header)
        return tr

    def make_html_table_row(self, row):
        tr = HtmlTableRow()
        for column in row:
            cell = HtmlTableCell()
            logging.debug("column {}, {}".format(column, type(column)))
            if isinstance(column, float): #ROUND(size) still gets x.0, why
                column = int(round(column))
            cell.set_value(str(column))
            tr.add_cell(cell)
        return tr

def display_search_all(search_env):
    s = SearchApartmentBase(search_env.region_id, [])
    s.search_all()
    page = create_html_page()
    body = page.get_body()
    compose_html_search(body, search_env)
    s.make_html_table(body)
    print page

def display_search_result(search_env):
    if search_env.search_type == SearchEnv.s_all:
        display_search_all(search_env)
    elif search_env.search_type == SearchEnv.s_change:
        display_search_all(search_env)
    elif search_env.search_type == SearchEnv.s_multi_change:
        display_search_all(search_env)
    elif search_env.search_type == SearchEnv.s_sold:
        display_search_all(search_env)
    else:
        display_error_page("Unknown type {}".format(search_env.search_type))

def get_web_params():
    params = {}
    web_params = cgi.FieldStorage()
    for name in web_params.keys():
        value = web_params.getlist(name)
        params[name] = value
        logging.debug("param {}, value {}".format(name, value))
    return params

def get_web_param_cnt(params):
    cnt = len(params.keys())
    return cnt

def init_logging():
    logging.basicConfig(filename="/var/log/lianjia_search.log",
                        format="%(asctime)s %(message)s",
                        level=logging.DEBUG)

class SearchEnv(object):
    s_region = "region"
    s_type = "type"

    s_all = "s_all"
    s_change = "s_change"
    s_multi_change = "s_multi_change"
    s_sold = "s_sold"
    search_types = [s_all, s_change, s_multi_change, s_sold]

    def __init__(self, web_params={}):
        if get_web_param_cnt(web_params) == 0:
            self.init_as_default()
        else:
            self.init_from_web_params(web_params)

    def init_as_default(self):
        all_region_ids = get_region_id_list()
        if len(all_region_ids) == 0:
            return
        self.region_id = all_region_ids[0]
        self.search_type = SearchEnv.s_all

    def init_from_web_params(self, web_params):
        s_region = SearchEnv.s_region
        s_type = SearchEnv.s_type

        self.init_as_default()
        param_keys = web_params.keys()
        all_region_ids = get_region_id_list()
        if s_region in param_keys:
            region_id = web_params[s_region][0]
            logging.debug("region_id {}".format(region_id))
            if region_id in all_region_ids:
                self.region_id = region_id
        if s_type in param_keys:
            search_type = web_params[s_type][0]
            if search_type in SearchEnv.search_types:
                self.search_type = search_type

    @staticmethod
    def get_search_type_desc(search_type):
        if search_type == SearchEnv.s_all:
            return "所有房源"
        elif search_type == SearchEnv.s_change:
            return "调价记录"
        elif search_type == SearchEnv.s_multi_change:
            return "多次调价"
        elif search_type == SearchEnv.s_sold:
            return "下架房源"
        else:
            raise Exception("Unknown search type {}".format(search_type))

if __name__ == "__main__":
    init_logging()
    reload(sys)
    sys.setdefaultencoding("utf-8")
    default_search_env = SearchEnv()
    web_params = get_web_params()
    if get_web_param_cnt(web_params) == 0:
        display_default_page()
    else:
        search_env = SearchEnv(web_params)
        display_search_result(search_env)

