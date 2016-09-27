Please open with Chrome. The following steps has been confirmed on **Mac OS X**.

# Install Python
1. Goto [Python official website](https://www.python.org/downloads/release), download source code from *"Gzipped source tarball"*, get a file like *"Python-2.7.12.tgz"*.
2. Run *"tar zxf \<Python-2.x.tgz\>"*. In the decompressed directory, run *"./configure --prefix=/usr/"*, *"make"*, *"sudo make install"* one by one.
3. Run *"python -V"*, make sure the right python version is installed.

# Install MySQL
1. Goto [MySQL official website](http://dev.mysql.com/downloads/mysql/), select platform as *"Mac OS X"*, and download *"DMG Archive"*, get a file like *"mysql-5.7.13-osx10.11-x86_64.dmg"*.
2. Double click the dmg file to install MySQL.

# Install Pip
1. Goto [pip official website](https://pip.pypa.io/en/stable/installing/), and download *get-pip.py*.
2. Run *"python get-pip.py"*.

# Install Python Modules
1. Install bs4 with *"pip install bs4"*.
2. Install requests with *"pip install requests"*.
3. Install MySQLdb with *"pip install MySQL-python"*.

# Apache server
1. Mac should already have apache server installed. Run *"http -v"* to check the version. If failed, check step 2. Otherwise jump to next section.
2. Goto [apache httpd official website](https://httpd.apache.org/download.cgi#apache24), download the _"*.tar.gz"_ source code file.
3. Install as python source code.

# Start MySQL & Apache Server
1. Run "*/usr/local/bin/mysql.server start*" to start MySQL server. Do not run with "*sudo*", or you will see this msg "*ERROR! The server quit without updating PID file*". In that case, you need to goto directory */usr/local/var/mysql/*, remove the _"*.err"_ file, and rerun the command to start MySQL server.
2. Run *"sudo apachectl start"* to start apache server.

# Clone lianjia_crawler git code
1. Run *"git clone https://github.com/nju04zq/lianjia_crawler"*.

# Change Apache Server Configuration
1. Goto lianjia_crawler's root directory.
2. Run *"sudo ln -s \<lianjia\_crawler\_absolute\_path\>/lianjia_search.py /Library/WebServer/CGI-Executables/search.py"*.
3. Change httpd configuration file *"/etc/apache2/httpd.conf"*, apply the following diff, then restart httpd with *"sudo apachectl restart"*.

```diff
*** /etc/apache2/httpd.conf_bk	Wed Jun 29 21:30:52 2016
--- /etc/apache2/httpd.conf	Sun Jul  3 20:41:20 2016
***************
*** 156,158 ****
  #LoadModule info_module libexec/apache2/mod_info.so
! #LoadModule cgi_module libexec/apache2/mod_cgi.so
  #LoadModule dav_fs_module libexec/apache2/mod_dav_fs.so
--- 156,158 ----
  #LoadModule info_module libexec/apache2/mod_info.so
! LoadModule cgi_module libexec/apache2/mod_cgi.so
  #LoadModule dav_fs_module libexec/apache2/mod_dav_fs.so
***************
*** 235,237 ****
  #
! DocumentRoot "/Library/WebServer/Documents"
  <Directory "/Library/WebServer/Documents">
--- 235,237 ----
  #
! DocumentRoot "/Library/WebServer/CGI-Executables"
  <Directory "/Library/WebServer/Documents">
***************
*** 270,272 ****
  <IfModule dir_module>
!     DirectoryIndex index.html
  </IfModule>
--- 270,273 ----
  <IfModule dir_module>
! #    DirectoryIndex index.html
!      DirectoryIndex search.py
  </IfModule>
***************
*** 380,384 ****
  <Directory "/Library/WebServer/CGI-Executables">
      AllowOverride None
!     Options None
      Require all granted
  </Directory>
--- 381,386 ----
  <Directory "/Library/WebServer/CGI-Executables">
      AllowOverride None
!     Options +ExecCGI
!     AddHandler cgi-script .py
      Require all granted
  </Directory>
```

