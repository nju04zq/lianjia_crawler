Please open with Chrome. The following steps has been confirmed on **Mac OS X**.

# Install Python
1. Goto [Python official website](https://www.python.org/downloads/release), download source code from *"Gzipped source tarball"*, get a file like *"Python-2.7.12.tgz"*.
2. Run *"tar zxf \<Python-2.x.tgz\>"*. In the decompressed directory, run *"./configure --prefix=/usr/"*, *"make"*, *"sudo make install"* one by one.
3. Run *"python -V"*, make sure the right python version is installed.

# Install MySQL
1. Install MySQL with *"brew install mysql"*.

# Install Pip
1. Goto [pip official website](https://pip.pypa.io/en/stable/installing/), and download *get-pip.py*.
2. Run *"python get-pip.py"*.

# Install Python Modules
1. Install bs4 with *"pip install bs4"*.
2. Install requests with *"pip install requests"*.
3. Install mysql-connector with *"brew install mysql-connector-c"*.
3. Install MySQLdb with *"pip install MySQL-python"*.
NOTE1: If see *"IndexError: string index out of range"* error, then change */usr/local/bin/mysql_config*, `libs="$libs  -l"` to `libs="$libs -lmysqlclient -lssl -lcrypto"`.
NOTE2: Tool pip install modules from official site. It might be slow in China mainland. In that case, try a domestic mirror site. Run *"pip install xxx -i https://mirrors.tuna.tsinghua.edu.cn/pypi/web/simple/"*.

# Apache server
1. Mac should already have apache server installed. Run *"httpd -v"* to check the version. If failed, check step 2. Otherwise jump to next section.
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
*** /etc/apache2/httpd.conf_bk	Sat Oct  8 13:28:10 2016
--- /etc/apache2/httpd.conf	Sat Oct  8 13:28:41 2016
***************
*** 154,160 ****
  LoadModule autoindex_module libexec/apache2/mod_autoindex.so
  #LoadModule asis_module libexec/apache2/mod_asis.so
  #LoadModule info_module libexec/apache2/mod_info.so
! #LoadModule cgi_module libexec/apache2/mod_cgi.so
  #LoadModule dav_fs_module libexec/apache2/mod_dav_fs.so
  #LoadModule dav_lock_module libexec/apache2/mod_dav_lock.so
  #LoadModule vhost_alias_module libexec/apache2/mod_vhost_alias.so
--- 154,160 ----
  LoadModule autoindex_module libexec/apache2/mod_autoindex.so
  #LoadModule asis_module libexec/apache2/mod_asis.so
  #LoadModule info_module libexec/apache2/mod_info.so
! LoadModule cgi_module libexec/apache2/mod_cgi.so
  #LoadModule dav_fs_module libexec/apache2/mod_dav_fs.so
  #LoadModule dav_lock_module libexec/apache2/mod_dav_lock.so
  #LoadModule vhost_alias_module libexec/apache2/mod_vhost_alias.so
***************
*** 233,239 ****
  # documents. By default, all requests are taken from this directory, but
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "/Library/WebServer/Documents"
  <Directory "/Library/WebServer/Documents">
      #
      # Possible values for the Options directive are "None", "All",
--- 233,239 ----
  # documents. By default, all requests are taken from this directory, but
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "/Library/WebServer/CGI-Executables"
  <Directory "/Library/WebServer/Documents">
      #
      # Possible values for the Options directive are "None", "All",
***************
*** 268,274 ****
  # is requested.
  #
  <IfModule dir_module>
!     DirectoryIndex index.html
  </IfModule>
  
  #
--- 268,275 ----
  # is requested.
  #
  <IfModule dir_module>
! #    DirectoryIndex index.html
!      DirectoryIndex search.py
  </IfModule>
  
  #
***************
*** 379,385 ****
  #
  <Directory "/Library/WebServer/CGI-Executables">
      AllowOverride None
!     Options None
      Require all granted
  </Directory>
  
--- 380,387 ----
  #
  <Directory "/Library/WebServer/CGI-Executables">
      AllowOverride None
!     Options +ExecCGI
!     AddHandler cgi-script .py
      Require all granted
  </Directory>
  
```
