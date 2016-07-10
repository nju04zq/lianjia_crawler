#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import cgi
import sys
import logging
import traceback
import collections
from html_page import *
from lianjia_crawler_conf import *
from lianjia_crawler import SQLDB, \
                            get_region_data_table_name, \
                            get_region_change_table_name

lianjia_ershoufang_aid = "http://sh.lianjia.com/ershoufang/{}.html"

class Emoji(object):
    up = "\xf0\x9f\x94\xbc"
    down = "\xf0\x9f\x94\xbd"

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

def compose_html_filter_inactive(form):
    c = HtmlCheckBox()
    c.set_value("仅在售房源")
    c.set_attrib_name(SearchEnv.s_active)
    c.set_attrib_value(str(1))
    if search_env.only_active:
        c.set_checked()
    form.add_entry(c)

def compose_html_range(form, label, val_max, step, 
                       key_min, key_max, default_min, default_max):
    form.add_entry(HtmlLiteral(label))
    n = HtmlNumber()
    n.set_attrib_name(key_min)
    if default_min > 0:
        n.set_attrib_value(str(default_min))
    n.set_min(0)
    n.set_max(val_max)
    n.set_step(step)
    form.add_entry(n)

    form.add_entry(HtmlLiteral("~"))
    n = HtmlNumber()
    n.set_attrib_name(key_max)
    if default_max > 0:
        n.set_attrib_value(str(default_max))
    n.set_min(0)
    n.set_max(val_max)
    n.set_step(step)
    form.add_entry(n)

def compose_html_price_range(form):
    compose_html_range(form, "单价/w", 99.9, 0.1,
                       SearchEnv.s_price_min, SearchEnv.s_price_max,
                       float(search_env.price_min)/10000,
                       float(search_env.price_max)/10000)

def compose_html_size_range(form):
    compose_html_range(form, "面积/㎡", 9999, 1,
                       SearchEnv.s_size_min, SearchEnv.s_size_max,
                       search_env.size_min, search_env.size_max)

def compose_html_total_range(form):
    compose_html_range(form, "总价/w", 9999, 1,
                       SearchEnv.s_total_min, SearchEnv.s_total_max,
                       search_env.total_min, search_env.total_max)

def compose_html_filter(form, do_filter_inactive=True):
    compose_html_price_range(form)
    form.add_entry(HtmlSpace(2))
    compose_html_size_range(form)
    form.add_entry(HtmlSpace(2))
    compose_html_total_range(form)
    if do_filter_inactive:
        form.add_entry(HtmlBr(2))
        compose_html_filter_inactive(form)

def compose_error_paragraph(body, error_msg):
    p = HtmlParagraph()
    body.add_element(p)
    p.set_color("red")
    lines = error_msg.split("\n")
    for line in lines:
        p.add_value(line)
        p.add_value(str(HtmlBr()), escape=False)

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

class Column(object):
    def __init__(self, order, padding, cid, cname, sql, show):
        self.order = order
        self.padding = padding
        self.cid = cid
        self.cname = cname
        self.sql = sql
        self.show = show

class SearchApartment(object):
    # define the columns
    columns = []
    rows_per_page = 20

    def __init__(self, show_column_indexes=[]):
        self.order = 0
        self.cur_page = 0
        self.max_page = 0
        self.rows = []
        self.table_style = ""
        self.get_column_show([])
        self.get_column_order()

    def get_column_from_cid(self, cid):
        for column in self.columns:
            if column.cid == cid:
                return column

    def get_column_order(self):
        a = sorted(self.columns, key=lambda x:abs(x.order), reverse=True)
        self.column_order = []
        if self.order != 0:
            for column in a:
                if abs(column.order) == abs(self.order):
                    self.column_order.append((column.cid, self.order))
        for column in a:
            if column.order == 0:
                break
            if column.cid not in self.column_order:
                self.column_order.append((column.cid, column.order))

    def get_column_show(self, show_column_indexes):
        if len(show_column_indexes) == 0:
            self.get_default_column_show()
            return

        self.column_show = []
        show_column_indexes.sort()
        for i in show_column_indexes:
            if i < 0 or i >= len(self.columns):
                continue
            self.column_show.append(self.columns[i].cid)
        if len(self.column_show) == 0:
            self.get_default_column_show()

    def get_default_column_show(self):
        self.column_show = []
        for column in self.columns:
            if column.show:
                self.column_show.append(column.cid)

    def make_sql_order_str(self):
        if len(self.column_order) == 0:
            return ""
        sql_s = []
        for cid, order in self.column_order:
            if order < 0:
                tmp = " DESC"
            else:
                tmp = ""
            sql_s.append(cid + tmp)
        s = "ORDER BY " + ",".join(sql_s)
        return s

    def make_sql_column_str(self):
        sql_s = []
        for cid in self.column_show:
            column = self.get_column_from_cid(cid)
            if column.sql != "":
                s = column.sql
            else:
                s = column.cid
            sql_s.append(s)
        column_str = ",".join(sql_s)
        return column_str

    def make_sql_range_str(self, cid, val_min, val_max):
        if 0 < val_max < val_min:
            s = ""
        elif 0 < val_min < val_max:
            s = " AND {} < {} AND {} < {}".format(val_min, cid, cid, val_max)
        elif val_min > 0:
            s = " AND {} < {}".format(val_min, cid)
        elif val_max > 0:
            s = " AND {} < {}".format(cid, val_max)
        else:
            s = ""
        return s

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
        # get row cnt
        self.row_cnt = 0

    def get_qualified_apartments(self, db):
        # get data in rows
        self.rows = []

    def search(self):
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
        table.set_tid(self.table_style)
        body.add_element(table)
        tr = self.make_html_table_header_row()
        table.add_row(tr)
        for row in self.rows:
            tr = self.make_html_table_row(row)
            table.add_row(tr)

    def make_html_header_href(self, order):
        new_params = {SearchEnv.s_order:[str(order)]}
        query_param_table = collections.OrderedDict()
        add_to_query_table_params(query_param_table, web_params)
        replace_query_table_params(query_param_table, new_params)
        if query_param_table.has_key(SearchEnv.s_page):
            query_param_table.pop(SearchEnv.s_page)
        s = generate_query_str(query_param_table)
        return s

    def make_html_header_value(self, column):
        if column.order == 0:
            return column.cname
        if column.cid == self.column_order[0][0]:
            order = -self.column_order[0][1]
            order_main = True
        else:
            order = column.order
            order_main = False

        a = HtmlAnchor()
        href_value = self.make_html_header_href(order)
        a.set_href(href_value)
        a.add_value(column.cname)
        if order_main:
            if order > 0:
                a.add_value(Emoji.down)
            else:
                a.add_value(Emoji.up)
        return a
    
    def make_html_table_header_row(self):
        tr = HtmlTableRow()
        for cid in self.column_show:
            column = self.get_column_from_cid(cid)
            header = HtmlTableHeader()
            if column.order == 0:
                header.add_value(column.cname)
            else:
                a = self.make_html_header_value(column)
                header.add_value(str(a), escape=False)
            if column.padding > 0:
                padding_space = HtmlSpace(column.padding)
                header.add_value(str(padding_space), escape=False)
            tr.add_cell(header)
        return tr

    def make_html_table_row(self, row):
        tr = HtmlTableRow()
        for i in xrange(len(row)):
            cell = self.make_html_table_cell(self.columns[i].cid, row[i])
            tr.add_cell(cell)
        return tr

    def make_html_table_cell(self, cid, cell_value):
        cell = HtmlTableCell()
        cell.set_value(str(cell_value))
        return cell

    def make_html_show_columns(self, form):
        column_index = 0
        for column in self.columns:
            if column.cid in self.column_show:
                is_show = True
            else:
                is_show = False
            c = self.make_html_show_column_option(column, column_index, is_show)
            form.add_entry(c)
            column_index += 1

    def make_html_show_column_option(self, column, column_index, is_show):
        c = HtmlCheckBox()
        c.set_attrib_name(SearchEnv.s_column)
        c.set_attrib_value("{}".format(column_index))
        c.set_value(column.cname)
        if is_show:
            c.set_checked()
        return c

    def get_page_list(self):
        page_list = []
        max_page, cur_page, more_page = self.max_page, self.cur_page, -1
        if max_page < 6:
            return range(0,max_page+1), -1, -1

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
            page_list.append(less_page)

        page_list.append(more_page)
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

class SearchApartmentBase(SearchApartment):
    # order/padding/cid/cname/sql/show
    columns = [
        Column(0,  0, "aid", "房源编号", "", True),
        Column(0,  0, "location", "小区", "", True),
        Column(8,  4, "price", "单价", "", True),
        Column(7,  2, "size", "面积", "ROUND(size) AS size", True),
        Column(6,  2, "total", "总价", "", True),
        Column(-9, 1, "uts", "更新日期", "DATE(uts) AS uts", True),
        Column(0,  0, "days", "上架天数", "DATEDIFF(uts, nts) AS days", False)]

    def __init__(self, search_env):
        self.table_style = "t01"
        self.region_id = search_env.region_id
        self.cur_page = search_env.page
        self.order = search_env.order
        self.only_active = search_env.only_active
        self.only_inactive = False
        self.price_min = search_env.price_min
        self.price_max = search_env.price_max
        self.size_min = search_env.size_min
        self.size_max = search_env.size_max
        self.total_min = search_env.total_min
        self.total_max = search_env.total_max
        self.get_column_show(search_env.show_column_indexes)
        self.get_column_order()

    def make_sql_where_str(self):
        table_name = get_region_data_table_name(self.region_id)
        s = "WHERE 1"
        a = " AND DATE(uts) {} "\
             "(SELECT DATE(MAX(uts)) FROM {})"
        if self.only_active:
            s += a.format("=", table_name)
        elif self.only_inactive:
            s += a.format("<>", table_name)
        s += self.make_sql_range_str("price", self.price_min, self.price_max)
        s += self.make_sql_range_str("size", self.size_min, self.size_max)
        s += self.make_sql_range_str("total", self.total_min, self.total_max)
        return s

    def get_qualified_apartment_count(self, db):
        table_name = get_region_data_table_name(self.region_id)
        where_str = self.make_sql_where_str()
        sql_cmd = "SELECT COUNT(*) FROM {} {};"\
                  .format(table_name, where_str)
        result = db.select(sql_cmd)
        self.row_cnt = result[0][0]

    def get_qualified_apartments(self, db):
        if self.row_cnt == 0:
            self.rows = []
            return
        column_str = self.make_sql_column_str()
        order_str = self.make_sql_order_str()
        where_str = self.make_sql_where_str()
        limit_str = self.make_sql_limit_str()
        table_name = get_region_data_table_name(self.region_id)
        sql_cmd = "SELECT {} FROM {} {} {} {}; "\
                   .format(column_str, table_name, where_str,
                           order_str, limit_str)
        logging.debug(sql_cmd)
        self.rows = db.select(sql_cmd)

    def search_all(self):
        db = SQLDB()
        self.get_qualified_apartment_count(db)
        self.get_qualified_apartments(db)
        db.close()

    def search_sold(self):
        self.only_inactive = True
        self.only_active = False
        db = SQLDB()
        self.get_qualified_apartment_count(db)
        self.get_qualified_apartments(db)
        db.close()

    def make_html_table_cell(self, cid, cell_value):
        cell = HtmlTableCell()
        escape = True
        if isinstance(cell_value, float): #ROUND(size) still gets x.0, why
            cell_value = int(round(cell_value))
        elif cid == "aid":
            cell_value = compose_href_aid(cell_value)
            escape = False
        cell.set_value(str(cell_value), escape)
        if cid == "days":
            cell.set_align("center")
        return cell

class SearchApartmentChange(SearchApartment):
    # order/padding/cid/cname/sql/show
    columns = [
        Column(0,  0, "aid", "房源编号", "t1.aid", True),
        Column(0,  0, "location", "小区", "", True),
        Column(0,  2, "size", "面积", "ROUND(t1.size) AS size", True),
        Column(0,  4, "old_price", "旧单价", "", True),
        Column(0,  4, "new_price", "新单价", "", True),
        Column(0,  0, "new_total", "新总价", "", True),
        Column(8,  1, "diff", "差价", "(new_total-old_total) as diff", True),
        Column(-9, 1, "ts", "变更日期", "DATE(ts) AS ts", True)]

    def __init__(self, search_env):
        self.table_style = "t01"
        self.region_id = search_env.region_id
        self.cur_page = search_env.page
        self.order = search_env.order
        self.get_column_show([])
        self.get_column_order()

    def get_changed_apartment_count(self, db):
        table_name = get_region_change_table_name(self.region_id)
        sql_cmd = "SELECT COUNT(*) FROM {} WHERE old_total <> new_total;"\
                  .format(table_name)
        result = db.select(sql_cmd)
        self.row_cnt = result[0][0]

    def get_changed_apartments(self, db):
        if self.row_cnt == 0:
            self.rows = []
            return
        column_str = self.make_sql_column_str()
        order_str = self.make_sql_order_str()
        limit_str = self.make_sql_limit_str()
        data_table_name = get_region_data_table_name(self.region_id)
        change_table_name = get_region_change_table_name(self.region_id)
        sql_cmd = "SELECT {} FROM {} AS t1 INNER JOIN {} AS t2 "\
                  "ON t1.aid = t2.aid "\
                  "WHERE old_total <> new_total {} {}; "\
                   .format(column_str, data_table_name, change_table_name,
                           order_str, limit_str)
        logging.debug(sql_cmd)
        self.rows = db.select(sql_cmd)

    def search_change(self):
        db = SQLDB()
        self.get_changed_apartment_count(db)
        self.get_changed_apartments(db)
        db.close()

    def compose_diff_value(self, val):
        if val > 0:
            s = "+{}".format(val)
            color = "green"
        else:
            s = str(val)
            color = "red"

        f = HtmlFont(color)
        f.set_value(s)
        return str(f)

    def make_html_table_cell(self, cid, cell_value):
        cell = HtmlTableCell()
        escape = True
        if isinstance(cell_value, float): #ROUND(size) still gets x.0, why
            cell_value = int(round(cell_value))
        elif cid == "aid":
            cell_value = compose_href_aid(cell_value)
            escape = False
        elif cid == "diff":
            cell_value = self.compose_diff_value(cell_value)
            escape = False
        cell.set_value(str(cell_value), escape)
        return cell

class SearchApartmentMultiChange(SearchApartmentChange):
    # order/padding/cid/cname/sql/show
    columns = [
        Column(0,  0, "aid", "房源编号", "t1.aid", True),
        Column(0,  0, "location", "小区", "", True),
        Column(0,  2, "size", "面积", "ROUND(t1.size) AS size", True),
        Column(0,  4, "old_price", "旧单价", "", True),
        Column(0,  4, "new_price", "新单价", "", True),
        Column(0,  0, "new_total", "新总价", "", True),
        Column(0,  1, "diff", "差价", "(new_total-old_total) as diff", True),
        Column(0,  1, "ts", "变更日期", "DATE(ts) AS ts", True)]

    def __init__(self, search_env):
        super(SearchApartmentMultiChange, self).__init__(search_env)
        self.table_style = ""
        pass

    def get_multi_changed_apartment_count(self, db):
        data_table_name = get_region_data_table_name(self.region_id)
        change_table_name = get_region_change_table_name(self.region_id)
        sql_cmd = "SELECT COUNT(*) FROM "\
                  "(SELECT aid FROM {} WHERE old_total <> new_total "\
                  "GROUP BY aid HAVING COUNT(*) > 1) AS t;".\
                  format(change_table_name)
        result = db.select(sql_cmd)
        self.row_cnt = result[0][0]

    def get_multi_changed_apartments(self, db):
        if self.row_cnt == 0:
            self.rows = []
            return
        column_str = self.make_sql_column_str()
        order_str = self.make_sql_order_str()
        data_table_name = get_region_data_table_name(self.region_id)
        change_table_name = get_region_change_table_name(self.region_id)
        sql_cmd = "SELECT {} FROM {} AS t1 INNER JOIN {} AS t2 "\
                  "ON t1.aid = t2.aid "\
                  "WHERE old_total <> new_total AND "\
                  "t2.aid IN (SELECT aid FROM {} WHERE old_total <> new_total "\
                  "GROUP BY aid HAVING COUNT(*) > 1) ORDER BY t1.aid, ts".\
                  format(column_str, data_table_name, change_table_name,
                         change_table_name)
        logging.debug(sql_cmd)
        self.rows = db.select(sql_cmd)

    def search_multi_change(self):
        db = SQLDB()
        self.get_multi_changed_apartment_count(db)
        self.get_multi_changed_apartments(db)
        db.close()

    def make_html_table(self, body):
        colors = ["#ccc", "#fff"]
        color_idx = 0

        table = HtmlTable()
        table.set_tid(self.table_style)
        body.add_element(table)
        tr = self.make_html_table_header_row()
        table.add_row(tr)
        for i in xrange(len(self.rows)):
            if i != 0 and self.rows[i][0] != self.rows[i-1][0]:
                color_idx += 1
            color = colors[color_idx % len(colors)]
            tr = self.make_html_table_row(self.rows[i], color)
            table.add_row(tr)

    def make_html_table_row(self, row, color):
        tr = HtmlTableRow()
        for i in xrange(len(row)):
            cell = self.make_html_table_cell(self.columns[i].cid, row[i])
            cell.set_bg_color(color)
            tr.add_cell(cell)
        return tr

def display_search_all(search_env):
    s = SearchApartmentBase(search_env)
    s.search_all()
    page = create_html_page()
    body = page.get_body()
    form = compose_html_search(body, search_env)
    form.add_entry(HtmlBr(2))
    compose_html_filter(form)
    form.add_entry(HtmlBr())
    #s.make_html_show_columns(form)
    s.make_html_table_brief(body)
    s.make_html_table(body)
    body.add_element(HtmlBr())
    s.make_html_table_page_list(body)
    print page

def display_search_sold(search_env):
    s = SearchApartmentBase(search_env)
    s.search_sold()
    page = create_html_page()
    body = page.get_body()
    form = compose_html_search(body, search_env)
    form.add_entry(HtmlBr(2))
    compose_html_filter(form, do_filter_inactive=False)
    form.add_entry(HtmlBr())
    #s.make_html_show_columns(form)
    s.make_html_table_brief(body)
    s.make_html_table(body)
    body.add_element(HtmlBr())
    s.make_html_table_page_list(body)
    print page

def display_search_change(search_env):
    s = SearchApartmentChange(search_env)
    s.search_change()
    page = create_html_page()
    body = page.get_body()
    form = compose_html_search(body, search_env)
    form.add_entry(HtmlBr())
    s.make_html_table_brief(body)
    s.make_html_table(body)
    body.add_element(HtmlBr())
    s.make_html_table_page_list(body)
    print page

def display_search_multi_change(search_env):
    s = SearchApartmentMultiChange(search_env)
    s.search_multi_change()
    page = create_html_page()
    body = page.get_body()
    form = compose_html_search(body, search_env)
    form.add_entry(HtmlBr())
    s.make_html_table_brief(body)
    s.make_html_table(body)
    body.add_element(HtmlBr())
    print page

def display_search_result(search_env):
    if search_env.search_type == SearchEnv.type_all:
        display_search_all(search_env)
    elif search_env.search_type == SearchEnv.type_change:
        display_search_change(search_env)
    elif search_env.search_type == SearchEnv.type_multi_change:
        display_search_multi_change(search_env)
    elif search_env.search_type == SearchEnv.type_sold:
        display_search_sold(search_env)
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
    s_order = "o"
    s_active = "active"
    s_price_min = "p0"
    s_price_max = "p1"
    s_size_min = "s0"
    s_size_max = "s1"
    s_total_min = "t0"
    s_total_max = "t1"

    type_all = "all"
    type_change = "change"
    type_multi_change = "mchange"
    type_sold = "sold"
    search_types = [type_all, type_change, type_multi_change, type_sold]

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
        self.search_type = SearchEnv.type_all
        self.show_column_indexes = []
        self.page = 0
        self.order = 0
        self.only_active = False
        self.price_min = 0
        self.price_max = 0
        self.size_min = 0
        self.size_max = 0
        self.total_min = 0
        self.total_max = 0

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
        self.show_column_indexes = []
        column_indexes = web_params[SearchEnv.s_column]
        for column_index in column_indexes:
            try:
                column_index = int(column_index)
                self.show_column_indexes.append(column_index)
            except:
                pass

    def parase_param_int(self, web_params, key):
        val = 0
        if not web_params.has_key(key):
            return val
        val = web_params[key][0]
        try:
            val = int(val)
        except:
            val = 0
        return val

    def parase_param_uint(self, web_params, key):
        val = 0
        if not web_params.has_key(key):
            return val
        val = web_params[key][0]
        try:
            val = int(val)
            if val < 0:
                val = 0
        except:
            val = 0
        return val

    def parase_param_float(self, web_params, key):
        val = 0
        if not web_params.has_key(key):
            return val
        val = web_params[key][0]
        try:
            val = float(val)
            if val < 0:
                val = 0
        except:
            val = 0
        return val

    def init_from_web_params(self, web_params):
        self.init_as_default()
        keys = web_params.keys()
        if SearchEnv.s_region in keys:
            self.parse_param_region(web_params)
        if SearchEnv.s_type in keys:
            self.parse_param_search_type(web_params)
        if SearchEnv.s_column in keys:
            self.parse_param_column(web_params)
        self.page = self.parase_param_uint(web_params, SearchEnv.s_page)
        self.order = self.parase_param_int(web_params, SearchEnv.s_order)
        self.only_active = self.parase_param_int(web_params, SearchEnv.s_active)
        self.only_active = bool(self.only_active)
        self.size_min=self.parase_param_uint(web_params,SearchEnv.s_size_min)
        self.size_max=self.parase_param_uint(web_params,SearchEnv.s_size_max)
        self.total_min=self.parase_param_uint(web_params,SearchEnv.s_total_min)
        self.total_max=self.parase_param_uint(web_params,SearchEnv.s_total_max)
        self.price_min=self.parase_param_float(web_params,SearchEnv.s_price_min)
        self.price_max=self.parase_param_float(web_params,SearchEnv.s_price_max)
        self.price_min = int(self.price_min*10000)
        self.price_max = int(self.price_max*10000)
        if 0 < self.size_max < self.size_min:
            self.size_max, self.size_min = 0, 0
        if 0 < self.total_max < self.total_min:
            self.total_max, self.total_min = 0, 0
        if 0 < self.price_max < self.price_min:
            self.price_max, self.price_min = 0, 0

    @staticmethod
    def get_search_type_desc(search_type):
        if search_type == SearchEnv.type_all:
            return "所有房源"
        elif search_type == SearchEnv.type_change:
            return "调价记录"
        elif search_type == SearchEnv.type_multi_change:
            return "多次调价"
        elif search_type == SearchEnv.type_sold:
            return "下架房源"
        else:
            raise Exception("Unknown search type {}".format(search_type))

test_web_param = {
"region":["sjdxc"],
"type":["mchange"],
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
        try:
            display_search_result(search_env)
        except Exception as e:
            s = traceback.format_exc()
            display_error_page(s)
