#参考文档

请一定先阅读一下文档

* [osc文档](http://en.opensuse.org/openSUSE:Build_Service_Collaboration)
* [quilt](http://suse.de/~agruen/quilt.pdf)
* [如何build一个rpm包](http://http://www.google.com.hk/search?sugexp=chrome,mod=8&sourceid=chrome&ie=UTF-8&q=rpm+guide)

#Build Service

##什么是build service？

在本地用rpmbuild命令build软件包缺点明显，比如没有工程的概念，不方便多人同时操作源代码，build service主要完成
以下2个功能

* 类似svn的软件版本管理(包括用户管理)
* 自动build出rpm包


登录[build service](http://build.suse.de/), 这是build service的web管理界面。 
在客户端使用osc工具访问，osc也是操作build service的主要方式

suse的rpm包都由build service自动build, 所以修bug的话，也需要把自己的patch
提交到build service上面。

##build service上面的工程

常用的到build service上的工程

* SUSE:SLE-11-SP1:GA
* SUSE:SLE-11-SP1:Update:Test 
* SUSE:SLE-11-SP2:GA
* SUSE:SLE-11-SP2:Update:Test 

LE-11-SP1:GA这个工程包括了sles-11-sp1发行版上所有的package.
而SLE-11-SP1:Update:Test代表了sles-11-sp1发行版的maintenance update的package。在GM版出来以后，
所有的update都只会提交到Update:Test的工程里.

以此类推,SLE-11-SP2:GA里就是sp2所有的package， SLE-11-SP2:Update:Test就maintenance update.
Update:Test的包是GA的包的子集，如果GA的package做了修改,就会出现在Update:Test


rpm包就是从package中build出,典型的package的结构是这样:

	~/SUSE:SLE-11-SP2:Update:Test/csync2> ls -tr
	csync2-1.34.tar.gz        csync2-fix-xinetd.patch  csync2.changes  fix-missing-sentinels.diff
	csync2-README.quickstart  csync2-rm-ssl-cert       csync2.spec     force-debug-stderr-off-inetd.patch

csync2-1.34.tar.gz是源代码包, .patch和.diff都是以前修bug的patch，.changes是changelog文件r,  用rpm --changelog
可以看到这个文件, .spec文件描述了如果build一个rpm包。 spec的参考文档
要是想提一个patch，一般要修改3个文件

1. 添加你的patch文件
2. 修改spec文件
3. 修改changelog

package对应与rpm包，一般package和rpm包是一对一关系，比如device-mapper的package就会build出
device-mapper的rpm包, 也有一对多的情况，就是一个package可以build出多个rpm包，这些都由spec控制

#使用osc

osc类似与svn之类的工具,[osc用法](http://en.opensuse.org/openSUSE:Build_Service_Collaboration)

osc连接build.suse.de的命令

	osc -A https://api.suse.de

举例lvm在sle11-sp2上有一个bug，需要fix

##osc list

首先是找到有bug的rpm包对应的package，

	osc -A https://api.suse.de list SUSE:SLE-11-SP2:Update:Test | grep lvm

##osc branch

fork工程SUSE:SLE-11-SP2:Update:Test, 这样就有了你自己的一份package的拷贝，可以任意修改，当patch可以工作后，
再提给SUSE:SLE-11-SP2:Update:Test.

	osc -A https://api.suse.de branch SUSE:SLE-11-SP2:Update:Test lvm2

建立工程home:dmzhang:branches:SUSE:SLE-11-SP2:Update:Test, dmzhang是我的用户名


##osc checkout

建立了自己的工程以后，就可以checkout下来

	osc -A https://api.suse.de checkout home:deanraccoon:branches:SUSE:SLE-11-SP2:Update:Test/lvm2

这样，无论读lvm2的代码，还是修lvm2的代码，都可以了

##osc bco

bco = branch + checkout

上面2步操作可以一起进行

##修改patch


###解压源码

quilt工具, [quilt用法](http://suse.de/~agruen/quilt.pdf)

###quilt setup

	quilt setup lvm2.spec

quilt命令读spec文件，把spec文件中提到的source包解压缩，把spec文件中提到的patch文件建立一个series,方便之后的打包


###进入解压后的文件夹

运行完quilt setup之后，出现新文件夹LVM2.2.02.84

	cd LVM2.2.02.84


###操作patch

注意这些操作一定要在LVM2.2.02.84目录下进行

	#检查所有patch
	quilt serise
	#打上所有patch
	quilt push -a
	#检查正在操作的patch
	quilt top

###创建你的patch

	#创建	
	quilt new my_patch_bug.patch
	#file是你打算修改的文件
	quilt edit file
	#检查修改结果
	quilt diff
	#把diff的结构刷到my_patch_bug.patch中
	quilt refresh
	

quilt可以自动跟踪你的修改结果，可以根据quilt的文档，多练习一下.
等最会quilt refresh做完，你的patch文件就产生了. 如果你还要继续修改，
只要重复quilt edit 和quilt refesh就可以产生新的patch文件了

产生的patch文件出现在上层目录，因为quilt会做一个软连接patches指向上层目录


	
#修改spec文件,changelog,加入新patch

###修改spec文件
现在有了新的patch，需要修改spec文件，让build service在build你的rpm包时，加如这个patch,
只需要2行

	patch46:  my_patch_bug.patch

和
	patch46 -p1

细节见spec的参考文档

###修改changelog

	osc -A https://api.suse.de vc

###加入新的patch

	osc -A https://api.suse.de add my_patch_bug.patch

#commit patch

检查修改情况
	
	osc -A https://api.suse.de diff

提交修改到你自己的branch
	
	osc -A https://api.suse.de commit -m"your comment"

检查build log

	osc -A https://api.suse.de buildlog standard i586

获得rpm包

	osc -A https://api.suse.de getbinaries standard i586

#submit request patch

检查rpm正确,最后一步也是最重要的一步，就是把你的工作成果提交的maintenance update中

	osc -A https://api.suse.de submitrequest  -m"bnc@11111, I have fixed" \ 
	SUSE:SLE-11-SP2:Update:Test 







	
