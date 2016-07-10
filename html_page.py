import cgi
import urllib

class HtmlPage(object):
    def __init__(self):
        self.head = HtmlHead()
        self.body = HtmlBody()

    def get_head(self):
        return self.head

    def get_body(self):
        return self.body

    def __str__(self):
        s = "Content-Type: text/html; charset=UTF-8\n\n"
        s += "<html>\n"
        s += "{}\n".format(self.head)
        s += "{}\n".format(self.body)
        s += "</html>"
        return s

class HtmlHead(object):
    def __init__(self):
        self.style = HtmlStyle()
        self.title = "default"

    def set_title(self, title):
        self.title = title

    def __str__(self):
        s = ""
        s += "<head>\n"
        s += "{}\n".format(self.style)
        s += "<title>{}</title>\n".format(cgi.escape(self.title))
        s += "</head>\n"
        return s

class HtmlStyle(object):
    def __init__(self):
        self.init_style_content()

    def init_style_content(self):
        self.content = \
'''table, th, td {
    border: 1px solid black;
    border-collapse: collapse;
}
table#t01 tr:nth-child(even) {
    background-color: #eee;
}
table#t01 tr:nth-child(odd) {
   background-color:#fff;
}
'''

    def __str__(self):
        s = ""
        s += "<style>\n{}\n</style>".format(self.content)
        return s

class HtmlBody(object):
    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)

    def __str__(self):
        s = ""
        s += "<body>\n"
        for element in self.elements:
            s += "{}\n".format(element)
        s += "</body>"
        return s

class HtmlAttrib(object):
    def __init__(self, name, value="none", is_url=False):
        self.name = name
        self.value = value
        self.is_url = is_url

    def set_value(self, value):
        self.value = value

    def compose_value(self):
        if self.is_url:
            if self.value.startswith("http://"):
                s = "http://"
                s += urllib.quote(self.value[len("http://"):])
            else:
                s = self.value
        else:
            s = cgi.escape(self.value, quote=True)
        return s

    def __str__(self):
        s = '{}="{}"'.format(self.name, self.compose_value())
        return s

class HtmlElement(object):
    def __init__(self, name, has_close_tag=True):
        self.name = name
        self.value = ""
        self.attrib_list = []
        self.sub_element_list = []

    def set_value(self, value, escape=True):
        if escape:
            self.value = cgi.escape(value)
        else:
            self.value = value

    def add_value(self, value, escape=True):
        if escape:
            self.value += cgi.escape(value)
        else:
            self.value += value

    def add_sub_element(self, sub_element):
        self.sub_element_list.append(sub_element)

    def add_attrib(self, attrib):
        self.attrib_list.append(attrib)

    def compose_open_tag(self):
        s = ""
        s += "<{}".format(self.name)
        for attrib in self.attrib_list:
            s += " {}".format(attrib)
        s += ">"
        return s

    def compose_close_tag(self):
        s = ""
        s += "</{}>".format(self.name)
        return s

    def compose_value_from_sub_elements(self):
        s = ""
        for element in self.sub_element_list:
            s += "{}\n".format(element)
        return s

    def compose_value(self):
        if len(self.sub_element_list) > 0:
            s = "\n"
            s += self.compose_value_from_sub_elements()
        else:
            s = self.value
        return s

    def __str__(self):
        s = ""
        s += "{}".format(self.compose_open_tag())
        s += "{}".format(self.compose_value())
        s += "{}".format(self.compose_close_tag())
        return s

class HtmlLiteral(object):
    def __init__(self, text=""):
        self.text = text

    def set_text(self, text):
        self.text = text

    def __str__(self):
        return self.text

class HtmlBr(HtmlElement):
    def __init__(self, br_cnt=1):
        super(HtmlBr, self).__init__("br")
        self.br_cnt = br_cnt

    def __str__(self):
        s = ""
        for i in xrange(self.br_cnt):
            s += "<br>"
        return s

class HtmlSpace(HtmlElement):
    def __init__(self, space_cnt=1):
        super(HtmlSpace, self).__init__("none")
        self.space_cnt = space_cnt

    def __str__(self):
        s = ""
        for i in xrange(self.space_cnt):
            s += "&nbsp;"
        return s

class HtmlParagraph(HtmlElement):
    def __init__(self):
        super(HtmlParagraph, self).__init__("p")
        self.attrib_color = None

    def set_color(self, color):
        if self.attrib_color is not None:
            return
        attrib = HtmlAttrib("style")
        attrib.set_value("color:{};".format(color))
        self.add_attrib(attrib)
        self.attrib_color = attrib

class HtmlFont(HtmlElement):
    def __init__(self, color = None):
        super(HtmlFont, self).__init__("font")
        self.attrib_color = None
        if color is not None:
            self.set_color(color)

    def set_color(self, color):
        if self.attrib_color is not None:
            return
        attrib = HtmlAttrib("color")
        attrib.set_value(color)
        self.add_attrib(attrib)
        self.attrib_color = attrib

class HtmlAnchor(HtmlElement):
    def __init__(self):
        super(HtmlAnchor, self).__init__("a")
        self.attrib_href = None
        self.attrib_target = None

    def set_href(self, href_value):
        if self.attrib_href is not None:
            return
        attrib = HtmlAttrib("href", is_url=True)
        attrib.set_value(href_value)
        self.add_attrib(attrib)
        self.attrib_href = attrib

    def set_target_new_page(self):
        if self.attrib_target is not None:
            return
        attrib = HtmlAttrib("target", is_url=True)
        attrib.set_value("_blank")
        self.add_attrib(attrib)
        self.attrib_target = attrib

class HtmlLi(HtmlElement):
    def __init__(self):
        super(HtmlLi, self).__init__("li")

class HtmlOrderedList(HtmlElement):
    def __init__(self):
        super(HtmlOrderedList, self).__init__("ol")
        self.value = ""

    def add_entry(self, entry):
        self.add_sub_element(entry)

class HtmlUnorderedList(HtmlElement):
    def __init__(self):
        super(HtmlUnorderedList, self).__init__("ul")
        self.value = ""

    def add_entry(self, entry):
        self.add_sub_element(entry)

class HtmlTableCell(HtmlElement):
    def __init__(self):
        super(HtmlTableCell, self).__init__("td")
        self.value = ""
        self.attrib_align = None
        self.attrib_bg_color = None

    def set_align(self, align_value):
        if self.attrib_align is not None:
            return
        attrib = HtmlAttrib("align", align_value)
        self.add_attrib(attrib)
        self.attrib_align = attrib

    def set_bg_color(self, bg_color):
        if self.attrib_bg_color is not None:
            return
        attrib = HtmlAttrib("bgcolor", bg_color)
        self.add_attrib(attrib)
        self.attrib_bg_color = attrib

class HtmlTableHeader(HtmlElement):
    def __init__(self):
        super(HtmlTableHeader, self).__init__("th")
        self.value = ""

class HtmlTableRow(HtmlElement):
    def __init__(self):
        super(HtmlTableRow, self).__init__("tr")
        self.value = ""

    def add_cell(self, cell):
        self.add_sub_element(cell)

class HtmlTable(HtmlElement):
    def __init__(self):
        super(HtmlTable, self).__init__("table")
        self.value = ""
        self.attrib_tid = None
        self.header = None
        self.row_list = []

    def set_tid(self, tid):
        if self.attrib_tid is not None:
            return
        attrib = HtmlAttrib("id")
        attrib.set_value(tid)
        self.add_attrib(attrib)
        self.attrib_tid = attrib

    def set_header(self, header):
        self.header = header

    def add_row(self, row):
        self.add_sub_element(row)

    def compose_header(self):
        if self.header is None:
            s = ""
        else:
            s = "\n{}".format(self.header)
        return s

    def __str__(self):
        s = ""
        s += "{}".format(self.compose_open_tag())
        s += "{}".format(self.compose_header())
        s += "{}".format(self.compose_value())
        s += "{}".format(self.compose_close_tag())
        return s

class HtmlInput(HtmlElement):
    def __init__(self):
        super(HtmlInput, self).__init__("input")
        self.value = ""
        self.attrib_type = None
        self.attrib_name = None
        self.attrib_value = None

    def set_attrib_type(self, type_value):
        if self.attrib_type is not None:
            return
        attrib = HtmlAttrib("type")
        attrib.set_value(type_value)
        self.add_attrib(attrib)
        self.attrib_type = attrib

    def set_attrib_name(self, name_value):
        if self.attrib_name is not None:
            return
        attrib = HtmlAttrib("name")
        attrib.set_value(name_value)
        self.add_attrib(attrib)
        self.attrib_name = attrib

    def set_attrib_value(self, value_value):
        if self.attrib_value is not None:
            return
        attrib = HtmlAttrib("value")
        attrib.set_value(value_value)
        self.add_attrib(attrib)
        self.attrib_value = attrib

class HtmlText(HtmlInput):
    def __init__(self):
        super(HtmlText, self).__init__()
        self.set_attrib_type("text")

class HtmlNumber(HtmlInput):
    def __init__(self):
        super(HtmlNumber, self).__init__()
        self.set_attrib_type("number")
        self.attrib_min = None
        self.attrib_max = None
        self.attrib_step = None

    def set_min(self, min_val):
        if self.attrib_min is not None:
            return
        attrib = HtmlAttrib("min", str(min_val))
        self.add_attrib(attrib)
        self.attrib_min = attrib

    def set_max(self, max_val):
        if self.attrib_max is not None:
            return
        attrib = HtmlAttrib("max", str(max_val))
        self.add_attrib(attrib)
        self.attrib_max = attrib

    def set_step(self, step_val):
        if self.attrib_step is not None:
            return
        attrib = HtmlAttrib("step", str(step_val))
        self.add_attrib(attrib)
        self.attrib_step = attrib

class HtmlSubmit(HtmlInput):
    def __init__(self):
        super(HtmlSubmit, self).__init__()
        self.set_attrib_type("submit")

class HtmlRadioButton(HtmlInput):
    def __init__(self):
        super(HtmlRadioButton, self).__init__()
        self.set_attrib_type("radio")
        self.attrib_checked = None

    def set_checked(self):
        if self.attrib_checked is not None:
            return
        attrib = HtmlAttrib("checked", "checked")
        self.add_attrib(attrib)
        self.attrib_checked = attrib

class HtmlCheckBox(HtmlInput):
    def __init__(self):
        super(HtmlCheckBox, self).__init__()
        self.set_attrib_type("checkbox")
        self.attrib_checked = None

    def set_checked(self):
        if self.attrib_checked is not None:
            return
        attrib = HtmlAttrib("checked", "checked")
        self.add_attrib(attrib)
        self.attrib_checked = attrib

class HtmlOption(HtmlElement):
    def __init__(self):
        super(HtmlOption, self).__init__("option")
        self.value = ""
        self.attrib_value = None
        self.attrib_selected = None

    def set_attrib_value(self, value_value):
        if self.attrib_value is not None:
            return
        attrib = HtmlAttrib("value", value_value)
        self.add_attrib(attrib)
        self.attrib_value = attrib

    def set_selected(self):
        if self.attrib_selected is not None:
            return
        attrib = HtmlAttrib("selected", "selected")
        self.add_attrib(attrib)
        self.attrib_selected = attrib

class HtmlSelect(HtmlElement):
    def __init__(self):
        super(HtmlSelect, self).__init__("select")
        self.value = ""
        self.attrib_name = None

    def set_attrib_name(self, name_value):
        if self.attrib_name is not None:
            return
        attrib = HtmlAttrib("name")
        attrib.set_value(name_value)
        self.add_attrib(attrib)
        self.attrib_name = attrib

class HtmlPopupMenu(HtmlSelect):
    def __init__(self):
        super(HtmlPopupMenu, self).__init__()

    def add_entry(self, entry):
        self.add_sub_element(entry)

class HtmlScrollList(HtmlSelect):
    def __init__(self):
        super(HtmlScrollList, self).__init__()
        self.init_attrib_size()
#        self.attrib_multiple = None

    def init_attrib_size(self):
        self.attrib_size = HtmlAttrib("size", "1")
        self.add_attrib(self.attrib_size)

    def set_attrib_size(self, size):
        self.attrib_size.set_value("{}".format(size))

# On test, multiple doesn't work
#    def set_multiple(self):
#        if self.attrib_multiple is not None:
#            return
#        attrib = HtmlAttrib("multiple", "multiple")
#        self.add_attrib(attrib)
#        self.attrib_multiple = attrib

    def add_entry(self, entry):
        self.add_sub_element(entry)

class HtmlForm(HtmlElement):
    def __init__(self):
        super(HtmlForm, self).__init__("form")
        self.value = ""
        self.attrib_action = None
        self.attrib_method = None

    def add_entry(self, entry):
        self.add_sub_element(entry)

    def set_action(self, action_value):
        if self.attrib_action is not None:
            return
        attrib = HtmlAttrib("action", action_value, is_url=True)
        self.add_attrib(attrib)
        self.attrib_action = attrib

    def set_method(self, method_value):
        if self.attrib_method is not None:
            return
        attrib = HtmlAttrib("method", method_value)
        self.add_attrib(attrib)
        self.attrib_method = attrib
