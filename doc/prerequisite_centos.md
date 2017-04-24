Please open with Chrome. The following steps has been confirmed on **CentOS 6.5**.

# Install Python
1. Goto [Python official website](https://www.python.org/downloads/release), download source code from *"Gzipped source tarball"*, get a file like *"Python-2.7.12.tgz"*.
2. Run *"tar zxf \<Python-2.x.tgz\>"*. In the decompressed directory, run *"./configure --prefix=/usr/"*, *"make"*, *"sudo make install"* one by one.
3. Run *"python -V"*, make sure the right python version is installed.
4. The tool **yum** might be affected if system default python2.6 was replaced by latest. Run *"yum --version"*, if everything OK, then no problem. Otherwise, edit *"/usr/bin/yum"*, and change python to python2.6 in the first line.

# Install MySQL
1. Run *"sudo yum install mysql mysql-server"*.

# Install Pip
1. Goto [pip official website](https://pip.pypa.io/en/stable/installing/), and download *get-pip.py*.
2. Run *"python get-pip.py"*.

# Install Python Modules
1. Install bs4 with *"pip install bs4"*.
2. Install requests with *"pip install requests"*.
3. Install MySQLdb with *"pip install MySQL-python"*.
NOTE: Tool pip install modules from official site. It might be slow in China mainland. In that case, try a domestic mirror site. Run *"pip install xxx -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"*.

# Apache server
1. CentOS should already have apache server installed. Run *"httpd -v"* to check the version. If failed, check step 2. Otherwise jump to next section.
2. Run *"sudo yum install httpd"*.

# Start MySQL & Apache Server
1. Run *"sudo service mysqld start"* to start MySQL server.
2. Run *"sudo service httpd start"* to start apache server.

# Clone lianjia_crawler git code
1. Run *"git clone https://github.com/nju04zq/lianjia_crawler"*.

# Change Apache Server Configuration
1. Copy all the files in project lianjia\_crawler to *"/var/www/cgi-bin"*.
2. Change httpd configuration file *"/etc/apache2/httpd.conf"*, apply the following diff, then restart httpd with *"sudo httpd restart"*.

```diff
*** /etc/httpd/conf/httpd.conf_bk	Thu Jul 21 10:29:18 2016
--- /etc/httpd/conf/httpd.conf	Thu Jul 21 14:47:53 2016
***************
*** 290,294 ****
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "/var/www/html"

  #
--- 290,294 ----
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "/var/www/cgi-bin"

  #
***************
*** 400,404 ****
  # same purpose, but it is much slower.
  #
! DirectoryIndex index.html index.html.var

  #
--- 400,405 ----
  # same purpose, but it is much slower.
  #
! #DirectoryIndex index.html index.html.var
! DirectoryIndex lianjia_search.py

  #
***************
*** 582,586 ****
  <Directory "/var/www/cgi-bin">
      AllowOverride None
!     Options None
      Order allow,deny
      Allow from all
--- 583,588 ----
  <Directory "/var/www/cgi-bin">
      AllowOverride None
!     Options +ExecCGI +FollowSymLinks
!     AddHandler cgi-script .py
      Order allow,deny
      Allow from all
```
