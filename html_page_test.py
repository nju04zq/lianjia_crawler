from html_page import *

page = HtmlPage()

head = page.get_head()
head.set_title("<test page>")

body = page.get_body()

p = HtmlParagraph()
body.add_element(p)
a = HtmlAnchor()
a.set_value("google")
a.set_href("http://www.google.com")
p.add_value("<text & in paragraph>")
p.add_value("<br><b>{}</b>".format(a), escape=False)

ul = HtmlOrderedList()
body.add_element(ul)
li = HtmlLi()
li.set_value("abc")
ul.add_entry(li)
li = HtmlLi()
li.set_value("xyz")
ul.add_entry(li)

ol = HtmlUnorderedList()
body.add_element(ol)
li = HtmlLi()
li.set_value("123")
ol.add_entry(li)
li = HtmlLi()
li.set_value("456")
ol.add_entry(li)

a = HtmlAnchor()
a.set_value("index")
a.set_href("/index.html")
body.add_element(a)

t = HtmlTable()
body.add_element(t)
attrib = HtmlAttrib("id", "t01", is_url=True)
t.add_attrib(attrib)
#row
row = HtmlTableRow()
t.add_row(row)
#one cell
header = HtmlTableHeader()
row.add_cell(header)
a = HtmlAnchor()
a.set_value("index1")
header.add_sub_element(a)
attrib = HtmlAttrib("href", is_url=True)
attrib.set_value("/index.html")
a.add_attrib(attrib)
#one cell
header = HtmlTableHeader()
row.add_cell(header)
header.set_value("index2")
#one cell
header = HtmlTableHeader()
row.add_cell(header)
header.set_value("index3")
#row
row = HtmlTableRow()
t.add_row(row)
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("1")
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("a")
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("A")
#row
row = HtmlTableRow()
t.add_row(row)
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("2")
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("b")
#one cell
cell = HtmlTableCell()
row.add_cell(cell)
cell.set_value("B")

body.add_element(HtmlBr())

form = HtmlForm()
body.add_element(form)
form.add_entry(HtmlLiteral("Select size:"))
r = HtmlRadioButton()
r.set_attrib_name("size")
r.set_attrib_value("small")
r.set_value("small")
form.add_entry(r)
r = HtmlRadioButton()
r.set_attrib_name("size")
r.set_attrib_value("medium")
r.set_value("medium")
r.set_checked()
form.add_entry(r)
r = HtmlRadioButton()
r.set_attrib_name("size")
r.set_attrib_value("large")
r.set_value("large")
form.add_entry(r)

form.add_entry(HtmlBr())

form.add_entry(HtmlLiteral("Select accessories:"))
r = HtmlCheckBox()
r.set_attrib_name("accessories")
r.set_attrib_value("cow bell")
r.set_value("cow bell")
r.set_checked()
form.add_entry(r)
r = HtmlCheckBox()
r.set_attrib_name("accessories")
r.set_attrib_value("horns")
r.set_value("horns")
r.set_checked()
form.add_entry(r)
r = HtmlCheckBox()
r.set_attrib_name("accessories")
r.set_attrib_value("noise ring")
r.set_value("noise ring")
form.add_entry(r)

form.add_entry(HtmlBr())

form.add_entry(HtmlLiteral("Select color:"))
popup = HtmlPopupMenu()
form.add_entry(popup)
popup.set_attrib_name("color")
opt = HtmlOption()
popup.add_entry(opt)
opt.set_value("black")
opt.set_attrib_value("black")
opt = HtmlOption()
popup.add_entry(opt)
opt.set_value("white")
opt.set_attrib_value("white")
opt = HtmlOption()
popup.add_entry(opt)
opt.set_value("black & white")
opt.set_attrib_value("black & white")

form.add_entry(HtmlBr())

form.add_entry(HtmlLiteral("Select state:"))
form.add_entry(HtmlBr())
scroll = HtmlScrollList()
form.add_entry(scroll)
scroll.set_attrib_name("state")
scroll.set_attrib_size(2)
opt = HtmlOption()
scroll.add_entry(opt)
opt.set_value("Alabama")
opt.set_attrib_value("AL")
opt.set_selected()
opt = HtmlOption()
scroll.add_entry(opt)
opt.set_value("California")
opt.set_attrib_value("CA")
opt = HtmlOption()
scroll.add_entry(opt)
opt.set_value("Wisconsin")
opt.set_attrib_value("WI")

form.add_entry(HtmlBr(2))

form.add_entry(HtmlLiteral("Type description:"))
form.add_entry(HtmlBr())
text = HtmlText()
form.add_entry(text)
text.set_attrib_name("desc")

submit = HtmlSubmit()
form.add_entry(submit)

print page

