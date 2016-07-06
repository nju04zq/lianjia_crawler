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

lianjia_ershoufang_aid = "http://sh.lianjia.com/ershoufang/{}.html"

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

def add_to_query_table_params(query_param_table, params):
    for key in params.keys():
        value = params[key]
        if query_param_table.has_key(key):
            query_param_table[key] += value
        else:
            query_param_table[key] = value

def generate_query_str(query_param_table):
    s1 = ""
    for key in query_param_table.keys():
        values = query_param_table[key]
        values = list(set(values))
        for value in values:
            if s1 != "":
                s1 += "&"
            s1 += "{}={}".format(urllib.quote(key), urllib.quote(value))
    s = "{}?{}".format(get_script_name(), s1)
    return s

def request_uri_append_query_param(new_params):
    query_param_table = collections.OrderedDict()
    add_to_query_table_params(query_param_table, web_params)
    add_to_query_table_params(query_param_table, new_params)
    s = generate_query_str(query_param_table)
    return s

def replace_query_table_params(query_param_table, params):
    for key in params.keys():
        query_param_table[key] = params[key]

def request_uri_replace_query_param(new_params):
    query_param_table = collections.OrderedDict()
    add_to_query_table_params(query_param_table, web_params)
    replace_query_table_params(query_param_table, new_params)
    s = generate_query_str(query_param_table)
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

def compose_href_aid(aid):
    a = HtmlAnchor()
    a.set_href(lianjia_ershoufang_aid.format(aid))
    a.set_value(aid)
    a.set_target_new_page()
    return a

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
        return None

    form = HtmlForm()
    body.add_element(form)
    form.set_action(get_script_name())

    compose_search_regions(form, search_env.region_id)
    form.add_entry(HtmlSpace(4))
    compose_search_types(form, search_env.search_type)
    form.add_entry(HtmlSpace(4))
    compose_submit(form)
    return form

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
    columns = ["aid", "location", "price", "size", "total", "uts", "days"]
    column_map = {"aid":"房源编号", "location":"小区", "price":"单价",
                  "size":"面积", "total":"总价",
                  "uts":"更新日期", "days":"上架天数"}
    column_sql = {"size":"ROUND(size)", "nts":"DATE(nts)", "uts":"DATE(uts)",
                  "days":"DATEDIFF(uts, nts)"}
    default_columns = ["aid", "location", "price", "size", "total", "uts"]
    rows_per_page = 20

    def __init__(self, search_env):
        self.region_id = search_env.region_id
        self.show_columns = self.get_show_columns(search_env.show_column_ids)
        self.cur_page = search_env.page

    def get_show_columns(self, show_column_ids):
        if len(show_column_ids) == 0:
            return self.default_columns
        show_column_ids.sort()
        show_columns = []
        for column_id in show_column_ids:
            if column_id < 0 or column_id >= len(self.columns):
                continue
            show_columns.append(self.columns[column_id])
        if len(show_columns) == 0:
            show_columns = self.default_columns
        return show_columns

    def make_sql_column_str(self):
        show_columns = []
        for column in self.show_columns:
            if self.column_sql.has_key(column):
                column = self.column_sql[column]
            show_columns.append(column)
        column_str = ",".join(show_columns)
        return column_str

    def make_sql_limit_str(self):
        # page from 0-xx
        max_page = (self.row_cnt+self.rows_per_page-1)/self.rows_per_page-1
        if self.cur_page > max_page:
            self.cur_page = max_page
        self.max_page = max_page
        limit_str = "LIMIT {}, {}".format(self.cur_page*self.rows_per_page,
                                          self.rows_per_page)
        return limit_str

    def get_qualified_apartment_count(self, db):
        table_name = get_region_data_table_name(self.region_id)
        sql_cmd = "SELECT COUNT(*) FROM {};".format(table_name)
        result = db.select(sql_cmd)
        self.row_cnt = result[0][0]

    def get_qualified_apartments(self, db):
        if self.row_cnt == 0:
            self.rows = []
            return
        column_str = self.make_sql_column_str()
        limit_str = self.make_sql_limit_str()
        table_name = get_region_data_table_name(self.region_id)
        sql_cmd = "SELECT {} FROM {} "\
                  "ORDER BY uts DESC, price {};"\
                   .format(column_str, table_name, limit_str)
        logging.debug(sql_cmd)
        self.rows = db.select(sql_cmd)

    def search_all(self):
        db = SQLDB()
        self.get_qualified_apartment_count(db)
        self.get_qualified_apartments(db)
        db.close()

    def make_html_table_brief(self, body):
        p = HtmlParagraph()
        value = "Retrieved <b>{}</b> records.".format(self.row_cnt)
        p.set_value(value, escape=False)
        body.add_element(p)

    def make_html_table(self, body):
        table = HtmlTable()
        table.set_tid("t01")
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
        for i in xrange(len(row)):
            cell = HtmlTableCell()
            escape = True
            column_value = row[i]
            if isinstance(column_value, float): #ROUND(size) still gets x.0, why
                column_value = int(round(column_value))
            elif self.columns[i] == "aid":
                column_value = compose_href_aid(column_value)
                escape = False
            cell.set_value(str(column_value), escape)
            if self.columns[i] == "days":
                cell.set_align("center")
            tr.add_cell(cell)
        return tr

    def make_html_show_columns(self, form):
        column_idx = 0
        for column in self.columns:
            if column in self.show_columns:
                is_show = True
            else:
                is_show = False
            c = self.make_html_show_column_option(column_idx, is_show)
            form.add_entry(c)
            column_idx += 1

    def make_html_show_column_option(self, column_idx, is_show):
        c = HtmlCheckBox()
        c.set_attrib_name(SearchEnv.s_column)
        c.set_attrib_value("{}".format(column_idx))
        value = self.column_map[self.columns[column_idx]]
        c.set_value(value)
        if is_show:
            c.set_checked()
        return c

    def get_page_list(self):
        page_list = []
        max_page, cur_page, more_page = self.max_page, self.cur_page, -1
        if max_page < 6:
            return range(0,6), -1, -1

        page_list.append(0)
        if cur_page-1 > 0:
            page_list.append(cur_page-1)
        if cur_page > 0 and cur_page < max_page:
            page_list.append(cur_page)
        if cur_page+1 < max_page:
            page_list.append(cur_page+1)
        page_list.append(max_page)

        if cur_page+2 < max_page:
            more_page = cur_page+2
        else:
            more_page = cur_page-2

        if cur_page-2 > 0:
            less_page = cur_page-2
        else:
            less_page = -1
        if less_page == more_page:
            less_page = -1
        if less_page != -1:
            page_list += [less_page]

        page_list += [more_page]
        page_list.sort()
        return page_list, more_page, less_page

    def make_html_table_page_list(self, body):
        page_list, more_page, less_page = self.get_page_list()
        for i in page_list:
            a = HtmlAnchor()
            param = {SearchEnv.s_page:[str(i)]}
            uri = request_uri_replace_query_param(param)
            a.set_href(uri)
            escape = True
            if i == more_page or i == less_page:
                value = "..."
            elif i == self.cur_page:
                value = "<mark>{}</mark>".format(i+1)
                escape = False
            else:
                value = "{}".format(i+1)
            a.set_value(value, escape)
            body.add_element(a)

def display_search_all(search_env):
    s = SearchApartmentBase(search_env)
    s.search_all()
    page = create_html_page()
    body = page.get_body()
    form = compose_html_search(body, search_env)
    form.add_entry(HtmlBr(2))
    s.make_html_show_columns(form)
    s.make_html_table_brief(body)
    s.make_html_table(body)
    body.add_element(HtmlBr())
    s.make_html_table_page_list(body)
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
    s_column = "c"
    s_page = "p"

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
        self.show_column_ids = []
        self.page = 0

    def parse_param_region(self, web_params):
        all_region_ids = get_region_id_list()
        region_id = web_params[SearchEnv.s_region][0]
        if region_id in all_region_ids:
            self.region_id = region_id

    def parse_param_search_type(self, web_params):
        search_type = web_params[SearchEnv.s_type][0]
        if search_type in SearchEnv.search_types:
            self.search_type = search_type

    def parse_param_column(self, web_params):
        self.show_column_ids = []
        column_ids = web_params[SearchEnv.s_column]
        for column_id in column_ids:
            try:
                column_id = int(column_id)
                self.show_column_ids.append(column_id)
            except:
                pass

    def parse_param_page(self, web_params):
        page = web_params[SearchEnv.s_page][0]
        try:
            page = int(page)
            if page < 0:
                page = 0
        except:
            page = 0
        self.page = page

    def init_from_web_params(self, web_params):
        self.init_as_default()
        keys = web_params.keys()
        if SearchEnv.s_region in keys:
            self.parse_param_region(web_params)
        if SearchEnv.s_type in keys:
            self.parse_param_search_type(web_params)
        if SearchEnv.s_column in keys:
            self.parse_param_column(web_params)
        if SearchEnv.s_page in keys:
            self.parse_param_page(web_params)

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

test_web_param = {
"region":["sjdxc"],
"type":["s_all"],
"c":['0', '1', '2', '3', '4', '5'],
"p":["11"]
}

if __name__ == "__main__":
    init_logging()
    reload(sys)
    sys.setdefaultencoding("utf-8")
    default_search_env = SearchEnv()
    web_params = get_web_params()
    #web_params = test_web_param
    if get_web_param_cnt(web_params) == 0:
        display_default_page()
    else:
        search_env = SearchEnv(web_params)
        display_search_result(search_env)

