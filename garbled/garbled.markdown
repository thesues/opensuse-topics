#问题好像不少

第一次接触 linux 的同学, 如果碰到中文乱码,往往会不知所措, 从而认为开源系统的易用性很差,
或者 linux 很差 (其实 linux 就只是一个内核,跟文件乱码的关系不大).

我认为出现这种问题主要是因为软件开发者一开始就没有考虑到国际化的问题, 如果出现这种情
况,就只能先用英文了,export LANG=c. 要不就是读源代码, 写一个 patch, 让它支持多字节字符或
者 utf8。

##桌面系统乱码

现在的 linux 桌面默认使用 utf8,大部分使用 gtk,或者 qt 的程序基本不会出现中文乱码的问题,
如果还有老的程序,比如 xmms,推荐换别的软件吧。没有必要还用过时的软件

##java乱码

java server端的乱码一般是因为mysql的连接器，jsp输出的页面，servlet的输入等等默认都是8859-1, 如果处理中文的话，一定是乱码，
所以都要显式地指定编码方式。

java桌面的乱码一般是因为本地的字体不匹配什么的，需要到JRE里面修改字体的配置文件


##远程登录中文乱码

最常见乱码的情况是,远程登录服务器时出现乱码
原则是远程locale能改成utf-8的尽量用utf-8的编码, 如果远程必须是ANIS-C的话，bash也会出现半个字符的情况，但为了保证
像cat,less这些命令不出现乱码，只能先把本地的编码改为GBK(GBK兼容ANIS-C)

term 都可以设置编码,只要把当前 xterm 的编码设置成与目标机器的 locale 基本一致就可以了。

----------   ---------
远程服务器    本地终端
utf8          utf8
GBK           GBK
ANSI-C        GBK
----------   ---------


	linux-ircx:~> locale
	LANG=zh_CN.utf8
	LC_CTYPE=zh_CN.utf8
	LC_NUMERIC="zh_CN.utf8"
	LC_TIME="zh_CN.utf8"
	LC_COLLATE="zh_CN.utf8"
	LC_MONETARY="zh_CN.utf8"
	LC_MESSAGES="zh_CN.utf8"
	LC_PAPER="zh_CN.utf8"
	LC_NAME="zh_CN.utf8"
	LC_ADDRESS="zh_CN.utf8"
	LC_TELEPHONE="zh_CN.utf8"
	LC_MEASUREMENT="zh_CN.utf8"
	LC_IDENTIFICATION="zh_CN.utf8"
	LC_ALL=

这样gnome console一定要选成utf-8,否则肯定会出现半个字符,中文乱码的问题。
所以原则是在远程登录时，只要term的编码和应用程序的编码一致，就不会出现中文乱码。
term的编码可以自己选择,如图

![gnome console选择编码](./choose-char.png)

下一个问题是应用程序如何选择编码,(因为GBK和utf8冲突，所以只能选择一种编码方式), 也就是说
只要知道了应用程序选择的编码,让term与应用程序保持一致就万事大吉了

* 一部分linux程序会读LC\_CTYPE确定本地的编码,比如GTK的应用程序
* 有的程序不会去读本地locale, 只根据配置文件或命令行参数确定编码,比如mysql的客户端,vim都是这样.
* 有的程序也不读locale, 但会在处理字符串时注意处理utf-8字符。由于统一使用utf-8是未来的趋势, 也不必支持多字节字符集(如GBK), 这种处理办法，在绝大多数情况下都是合适的
* 再有的程序就根本不支持utf-8或者多字节字符, 就比较难办了。


#解决方案举例

##vim 的乱码

vim不依赖读locale知道当前的字符编码, 它会根据vimrc配置文件，和打开文件的编码选择编码方式


关于编码的配置，有下面的4个

* encoding 

设置vim的内部编码，与文件的具体编码也没有关系。通常是改成utf-8就不用再动了

* termencoding 

在命令行模式的情况下，设置编码，\textbf{一定要与term的编码一致},比如term是utf-8,那么termencoding也应该是utf-8.同样如果term是GBK编码，那termencoding也要是GBK编码. 这个问题通常会在远程登录时出现，比如putty和securyCRT都可以改自己的编码,主要要和termencoding一致. 如果是用gvim的话，这个参数不起作用

* fileencoding  

有2个用途。1,配置新建一个文件时，文件的默认编码。 2.打开一个已有的文件，通过设置一个与源文件编码不同的fileencoding,再保存。达到iconv的效果。一般情况下fileencoding最好和本地的locale一致. 我以前犯一个错误，发现文件乱码时，用fileencoding修改成别的编码，再保存。这样就把文件越改越乱了。

* fileencodings

打开的文件会不会乱码，主要靠这个设置了！vim根据fileencodings的顺序判断文件的编码，当encoding设置成utf-8时，默认的顺序是ucs-bom,utf-8,default,latin1,其中"default"表示当前locale的配置. 可以看出这个默认的设置有点儿问题。当default是latin1的时候，而你的文件又是GBK编码的方式，那么就会显示乱码了。如果只对中文而言改成ucs-bom,utf-8,gbk就可以了。删去default，在
这种情况下，即使locale是8859-15也不会影响中文. 缺点是如果文件是8859-15编码的话，那打开就成乱码了。因为GBK不和8859-15兼容。所以最完整的解决方案还是在所有的地方都使用utf-8编码，就没有问题了

总的来说打开文件能不能正确显示中文，就只需要了检查encoding, fileencodings, termencoding(fileencoding与打开文件时无关, 只说明保存文件时的编码)。检查可以分3步。

1. encoding只要设置成utf-8就不用管了。与乱码无关

2. 保证termencoding与term的编码一致，并且都支持中文,比如utf-8,GBK,utf-16

3. 检查fileencodings的编码顺序。一般要求是先ucs-bom,utf-8 然后其他可能的编码，比如GBK。

linux,默认utf-8环境

	set encoding=utf-8
	set fileencodings=ucs-bom,utf-8,GBK,latin1
	set fileencoding=utf-8
	set termencoding=utf-8

windows7, 默认GBK环境, 

	set encoding=utf-8
	set fileencodings=ucs-bom,utf-8,GBK,latin1
	set fileencoding=GBK
	set termencoding=GBK
	set langmenu=zh_CN.GBK

##mysql 命令操作乱码

##python 程序中的乱码

##c程序中的乱码

