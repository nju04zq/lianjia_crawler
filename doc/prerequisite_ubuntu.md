Please open with Chrome. The following steps has been confirmed on **Ubuntu 14.10**.

# Install Python
1. Goto [Python official website](https://www.python.org/downloads/release), download source code from *"Gzipped source tarball"*, get a file like *"Python-2.7.12.tgz"*.
2. Run *"tar zxf \<Python-2.x.tgz\>"*. In the decompressed directory, run *"./configure --prefix=/usr/"*, *"make"*, *"sudo make install"* one by one.
3. Run *"python -V"*, make sure the right python version is installed.

# Install MySQL
1. Run *"sudo apt-get install mysql-server libmysqlclient-dev"*.

# Install Pip
1. Goto [pip official website](https://pip.pypa.io/en/stable/installing/), and download *get-pip.py*.
2. Run *"python get_pip.py"*.

# Install Python Modules
1. Install bs4 with *"pip install bs4"*.
2. Install requests with *"pip install requests"*.
3. Install MySQLdb with *"pip install MySQL-python"*.
NOTE: Tool pip install modules from official site. It might be slow in China mainland. In that case, try a domestic mirror site. Run *"pip install xxx -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"*.

# Apache server
1. Run *"sudo apt-get install apache2"*.

# Start MySQL & Apache Server
1. Run *"sudo service mysql start"* to start MySQL server.
2. Run *"sudo service apache2 start"* to start apache server.

# Clone lianjia_crawler git code
1. Run *"git clone https://github.com/nju04zq/lianjia_crawler"*.

# Change Apache Server Configuration
1. Create directory with *"sudo mkdir /var/www/cgi-bin"*, and *"sudo chmod a+x /var/www/cgi-bin"*.
2. Copy all the files in project lianjia_crawler to *"/var/www/cgi-bin"*.
3. Change httpd configuration file *"/etc/apache2/sites-enabled/000-default.conf"*, apply the following diff, then restart httpd with *"sudo service apache2 restart"*.

```diff
*** /etc/apache2/sites-enabled/000-default.conf_bk    2016-07-21 20:44:31.092783821 +0800
--- /etc/apache2/sites-enabled/000-default.conf    2016-07-21 22:55:40.688824072 +0800
***************
*** 1,3 ****
--- 1,9 ----
  <VirtualHost *:80>
+     <Directory /var/www/cgi-bin>
+         Options +ExecCGI
+         DIrectoryIndex lianjia_search.py
+     </Directory>
+     AddHandler cgi-script .py
+ 
      # The ServerName directive sets the request scheme, hostname and port that
      # the server uses to identify itself. This is used when creating
***************
*** 10,14 ****
  
      ServerAdmin webmaster@localhost
!     DocumentRoot /var/www/html
  
      # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
--- 16,20 ----
  
      ServerAdmin webmaster@localhost
!     DocumentRoot /var/www/cgi-bin
  
      # Available loglevels: trace8, ..., trace1, debug, info, notice, warn,
```
