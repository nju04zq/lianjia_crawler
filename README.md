# What's this for?
In 2016 summer I planed to buy an apartment in Shanghai. At that time lianjia.com is popular for viewing apartments info online. So I want to keep track of apartments' price changes from lianjia, with a tool. Then comes this crawler.

BTW, before the crawler was finished and came to use, I've bought one in three days...

# Installation guide

### Prerequisites
1. Install Python 2.7
2. Install MySQL
3. Install Python module bs4, requests, MySQLdb with "pip install xxx"

### Change crawler configurations
In lianjia_crawler.py, find comment section "Crawl Configurations". Do configuration changes according to comments.

+ MySQL configurations in **MySQL\_conf**, set connection parameters. Remember to create a database named lianjia in MySQL with command *"CREATE DATABASE lianjia"*.

+ The regions you are caring about in **region_def**. It's a key-value pair for region name and its abbreviation. The abbreviation should be unique among defined regions. Before adding the region, confirm the search result on [sh.lianjia.com](sh.lianjia.com), to make sure it's the one you want. 

   For each region in **region_def**, two corresponding tables will be created in MySQL. For example, if region abbreviation is *ly*, then table *ly_data* is created to record all apartments/houses found on lianjia for this region, and table *ly_change* is for price/size changes on all crawled apartments/houses.

### Run crawler
+ In shell, run *"chmod u+x lianjia\_crawler.py"* and *"./lianjia\_crawler.py"*.
+ Use cron to schedule the crawler running every day. Here is an example.
 - Create a shell script, setting the Python path. Like file name *lianjia_crawler.sh*, with content,
 
```sh
#!/bin/bash
export PATH=/opt/local/Library/Frameworks/Python.framework/Versions/2.7/bin:$PATH
/Users/xyz/lianjia/lianjia_crawler.py >> /Users/xyz/lianjia/lianjia_crawler.log 2>&1
```
 - Install task in cron with *"crontab -e"*, run the script 12:00 every day.
 
 ```
 00 12 * * * /Users/xyz/lianjia/lianjia_crawler.sh
 ```

### Check lianjia data in MySQL
You need to run various SQL command to check crawled data in MySQL. If you are familar with MySQL, just skip this section.

#### List all crawled apartments/houses

```sql
SELECT * FROM ly_data;
```
#### List price changes for all crawled apartments/houses

```sql
SELECT * FROM ly_change;
```
### List detailed price changes
Do the create view only once.

```sql
CREATE VIEW ly_change_view AS
SELECT aid AS `房源编号`
      ,size AS `面积`
      ,old_price AS `旧单价`
      ,new_price AS `新单价`
      ,CONCAT(IF(new_total>old_total, "+", "-"), ABS(ROUND((new_total-old_total)/10000))) AS `差价`
      ,DATE(ts) AS `变更日期`
FROM ((SELECT p1.aid
             ,size
             ,old_price
             ,(real_size * old_price) AS old_total
             ,new_price
             ,(real_size * new_price) AS new_total
             ,p2.ts AS ts
       FROM ly_data AS p1 INNER JOIN
            ly_change AS p2
            ON p1.aid = p2.aid
       WHERE p2.old_price > 2000) #don't care about size change
      AS tmp)
ORDER BY `变更日期`, `面积`;
```
Check with following each time,

```sql
SELECT * FROM ly_change_view;
```

### List apartments/houses having price change more than once
Do the create view only once.

```sql
CREATE VIEW ly_multi_change_view AS
SELECT *
FROM ly_change_view
WHERE `房源编号` IN (SELECT `房源编号`
                     FROM ly_change_view
                     GROUP BY `房源编号`
                     HAVING COUNT(*) > 1)
ORDER BY `房源编号`, `变更日期`;
```
Check with following each time,

```sql
SELECT * FROM ly_multi_change_view;
```

### List sold/withdrawn apartments/houses
Do the create view only once.

```sql
CREATE VIEW ly_sold_view AS
SELECT aid AS `房源编号`
      ,LEFT(location, 5) AS `小区`
      ,size AS `面积`
      ,price AS `单价`
      ,ROUND((real_size * price)/10000) AS `总价`
      ,DATE(ts) AS `下架日期`
FROM ly_data,
     (SELECT MAX(ts) AS latest
      FROM ly_data) AS tmp
WHERE DATE(latest) != DATE(ts)
ORDER BY `下架日期`, `面积`;
```
Check with following each time,

```sql
SELECT * FROM ly_sold_view;
```

# What's coming next?
It's boring to check data in MySQL each time. It's also tedious to see the data on console. So I plan to create a simple webiste to render the collected data on a web page.