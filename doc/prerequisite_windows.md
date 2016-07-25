Please open with Chrome. The following steps has been confirmed on **Windows 7**.

# Install Python
1. Goto [Python official website](https://www.python.org/downloads/release), download *"Windows x86 MSI installer"*. Do not recommend *"Windows x86-64 MSI installer"*, since some python modules only have win32 version.
2. Execute the installer, the default installation path is *"C:\Python27\"*.

# Install MySQL
1. Goto [MySQL official website](http://dev.mysql.com/downloads/mysql/), select platform as *"Microsft Windows"*, and download the MSI Installer, get a file like *"mysql-installer-web-community-5.7.13.0.msi"*.
2. Execute the installer, choose MySQL Server on installing. On setting phase, enable it on system startup.

# Install Pip
Pip should have already been installed with Python. It's path is *C:\Python27\Scripts\pip.exe* (depending on where you have installed Python).

# Install Python Modules
1. Install bs4 with *"pip install bs4"*.
2. Install requests with *"pip install requests"*.
3. Install MySQLdb, vivist [pypi](https://pypi.python.org/pypi/MySQL-python/1.2.5), download the Win32 exe version. Then execute it.

# Apache server
1. Download *"Apache 2.4 VC9"* version from [Apache Haus](https://www.apachehaus.com/cgi-bin/download.plx), get a file like *"httpd-2.4.23-x86.zip"*.
2. Unzip the downloaded file, copy *"Apache24"* to *"C:\\"*.

# Start MySQL & Apache Server
1. For mysqld, should already run in backgroup after installation. Check task manager for "mysqld.exe".
2. Run *"C:\Apache24\bin\httpd.exe"* to start apache server.

# Clone lianjia_crawler git code
1. Run "*git clone https://github.com/nju04zq/lianjia_crawler*"
2. Change the first line in lianjia\_search.py from *"#!/usr/bin/env python"* to *"#!C:\Python27\python.exe"*.

# Change Apache Server Configuration
1. Copy all the files in project lianjia_crawler to *"C:\Apache24\cgi-bin"*.
3. Change httpd configuration file *"C:\Apache24\conf\httpd.conf"*, apply the following diff, then rerun *"C:\Apache24\bin\httpd.exe"*.

```diff
*** httpd_bk.conf	2016-07-20 15:40:36.360697400 +0800
--- httpd.conf	2016-07-25 11:44:26.904404600 +0800
***************
*** 244,248 ****
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "${SRVROOT}/htdocs"
  <Directory "${SRVROOT}/htdocs">
      #
--- 244,248 ----
  # symbolic links and aliases may be used to point to other locations.
  #
! DocumentRoot "${SRVROOT}/cgi-bin"
  <Directory "${SRVROOT}/htdocs">
      #
***************
*** 278,282 ****
  #
  <IfModule dir_module>
!     DirectoryIndex index.html
  </IfModule>
  
--- 278,282 ----
  #
  <IfModule dir_module>
!     DirectoryIndex lianjia_search.py index.html
  </IfModule>
  
***************
*** 379,383 ****
  <Directory "${SRVROOT}/cgi-bin">
      AllowOverride None
!     Options None
      Require all granted
  </Directory>
--- 379,384 ----
  <Directory "${SRVROOT}/cgi-bin">
      AllowOverride None
!     Options +ExecCGI
!     AddHandler cgi-script .py
      Require all granted
  </Directory>

```
