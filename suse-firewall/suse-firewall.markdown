#引言

凡是配过linux防火墙的同学都知道，干这个活很繁琐，而且容易出错。以前一直是自己手动配置iptables，把iptables放到一个sh文件里，开机运行。但是有2个缺点， 第一是如果很久没写过，语法可能都记得不太清楚，本来一个很简单的配置，还得折腾一会。外一个缺点是配置iptables的时候，如果不小心可能就把自己关在防火墙外面了，如果是用ssh远程登录的话，就只能重启服务器了。所以每次手动写iptables，总觉得心里没底。对于第二点， 倒是有简单的解决办法， 就是在crontab里搞个定时任务，每过半个小时就清空iptables一次， 这样就不用麻烦管理员重启了，或者写一个iptables命令

	iptables -A input establesd

，保证正在连接中的ssh不会被屏蔽掉，但是不管怎么处理，搞防火墙规则都不是一件
太容易的事情，并且通常干的事情又都很类似，无非是屏蔽ip，屏蔽端口什么的。

最近在自己的vps上装了一个pptpd， 在防火墙上需要做下面几个操作，只要是配置vpn，
这几个操作一般都是类似的

	#支持转发，比如从pptpd上来的ppp设备到eth0的转发
	$echo 1 >/proc/sys/net/ipv4/ip_forward	
	#打开pptpd需求的端口1723
	$iptables -A input -p tcp -m tcp --dport 1723 -j ACCEPT
	#打开iptables的MASQUERADE功能，由于在pptpd的配置文件中配置locale的ip
	#范围是192.168.0.0/24. 所以对来自192.168.0.0/24网段的请求都会转发
	$iptables -t nat -A POSTROUTING -s 192.168.0.0/24 -o eth0 -j MASQUERADE

关于linux防火墙的基本概念，推荐[鸟哥的私房菜](http://linux.vbird.org/linux_server/0250simple_firewall.php)， 和
[Linux Home Server HOWTO](http://www.brennan.id.au/06-Firewall_Concepts.html)， 简单的说MASQUERADE和SNAT基本一样，
就是在POSTROUTING阶段，把用户传过来的数据包的源ip地址改为pptpd服务器的地址，相当于隐藏了真实的vpn客户端ip的地址。

个人比较懒，不想再一条一条的写iptables命令了，开始的时候用yast搞防火墙， 可是yast的功能有限，满足不了上述的要求。郁闷了半天， 重新google到[opensue-wiki](http://en.opensuse.org/SuSEfirewall2)， 读完恍然大悟，原来SuSEfirewall支持手动配置， 并且非常灵活方便。之前冤枉它了...


#SuSEfirewall2

##一些概念

SuSEfirewall2是一个脚本，根据配置文件*/etc/sysconfig/SuSEfirewall2*生成iptables规则。同时它也是一个服务，如果把SuSEfirewall2打开，就相当于打开的linux防火墙，规则自然是根据配置文件生成的。

SuSEfirewall2支持高级配置，提供3个不同的*zones*， 在*zone*里指定interface，比如eth0，eth1，ppp1这些网络接口(network interface，比如eth0，ppp0)，提供不同的安全级别。

##启动，关闭，开机自动启动

* 启动
	$SuSEfirewall2
* 关闭
	$SuSEfirewall2 stop
* 开机自动启动
	$chkconfig SuSEfirewall2_init on
* 配置SuSEfirewall2的方法
	$vi /etc/sysconfig/SuSEfirewall2
* yast和SuSEfirewall2的关系
	yast提供了SuSEfirewall2的简单接口，在yast里面修改，其实也是在修改SuSEfirewall2的配置文件，如果手动修改配置文件，也可以被yast读入识别

##正题

在前面说了，SuSEfirewall2支持3个不同的zones，

* EXT  External Zone(不信任的，比如internet)
* INT  Interanl Zone(完全信任的， 没有过滤， 比如家庭网络，lan)
* DMZ  Demilitarized Zone(在防火墙后的服务器， 比如apache需要被外部internet访问)

External Zone一般都是外部地址，有公网ip，Interanl和Demilitarized Zone都是内部网络的地址，是私有地址。Demilitarized Zone直译应该是非军事化区，从字面上很难理解，它相当于位于防火墙之后的一个服务器，为了安全性考虑，并不和外界
的internet直接相连，当internet用户访问你的服务器时，请求会先到防火墙，防火墙对到Demilitarized Zone区的请求， 做一个DNAT操作，就是修改ip数据包的目的地址，把目的地址题换成Demilitarized zone的内部ip地址，再发到Demilitarized zone区的服务器，这和SNAT正好相反。 

做一个简单的总结就是:

1. Interanl Zone和Demilitarized Zone都属于内网，External Zone属于外网， 在内网区域(Interanl Zone和Demilitarized Zone)默认不做过滤，在外网区域(External Zone)默认过滤规则全过滤
2. Interanl Zone要通过防火墙访问外网，需要防火墙做一个SNAT(或者是MASQUERADE)。
3. Demilitarized Zone允许外网用户访问自己，在防火墙上要做一个DNAT，允许外部用户访问。

在区分了*zones*之后，建立防火墙规则时，就可以根据不同的*zones*，提过不同的过滤规则，比老是的用iptables -i参数
指定网络接口(network interface)方便不少.
root用户可以直接编辑文件*/etc/sysconfig/SuSEfirewall2*， 配置文件的注释很全
根据里面的注释配置适合自己的防火墙参数

###SuSEfirewall2参数说明

* [suse91](http://www.novell.com/documentation/suse91/suselinux-adminguide/html/ch19.html)
* [opensuse wiki](http://en.opensuse.org/SuSEfirewall2)

不一一列出的原因是在后面一张会结合实例说明，并且配置文件上的注释已经足够清楚了

###我的笔记本SuSEfirewall2参数举例

我的笔记本有2块网卡，一个有线(eth0)，一个无线(wlan0)， 并且开启了sshd服务。
所以SuSEfirewall2配置文件是这样的

	#我的笔记本， eth0和无线wlan0，都有防火墙规则
	FW_DEV_EXT="eth0 wlan0"
	#无内部接口
	FW_DEV_INT=""
	#无DMZ接口
	FW_DEV_DMZ=""

yast也可以配置网络接口(network interace，比如eth0，ppp0) 属于哪个*zone*，

![yast配置zone](interface.png)

EXT允许访问的接口

	#打开ssh接口
	#ssh的软件包额外安装了文件/etc/sysconfig/SuSEfirewall2.d/services/sshd
	#sshd文件里面只有一行
	#TCP="ssh"，说明sshd服务打开*ssh*端口，*ssh*对应于/etc/services下的22
	FW_CONFIGURATIONS_EXT="sshd"

在软件包没有安装service文件的情况下，比如pptpd就没有提供service文件，也可以用下面的参数直接配置

	FW_SERVICES_EXT_TCP="22"

手动配置好以后，也可以从yast里面看到

![yast配置allowd service](allowed_service.png)

#SuSEfirewall2使用实例

本文的精华在这里， SuSEfirewall2里有一个纯文本文档EXAMPLS帮助，里面从简单到复杂列举了多个场景。

是学习使用SuSEfirewall2最快最好的方式（因为大部分情况差不多），有兴趣的同学可以好好看看，会很有收获.

##场景:家庭网络

家里有多台PC，一台SUSE linux PC通过ADSL连接到运营商。家庭的其他PC要通过SUSE Linux PC连接互联网，并且本地的局域网的网段是192.168.10.0/24. SUSE Linux PC通过eth0连接内网。

	#外网接口是dsl0，默认打开过滤
	FW_DEV_EXT="dsl0"
	#eth0连接到其他电脑，如果其他电脑多于1台，eth0就应该是
	#连接到交换机上
	FW_DEV_INT="eth0"
	#打开ip_forward
	FW_ROUTE="yes"
	#打开MASQUERADE功能
	FW_MASQUERADE="yes"
	#来自内网的数据包，都做MASQUERADE
	FW_MASQ_NETS="192.168.10.0/24"

##场景:配置pptpd对应的防火墙规则
现在回到最开始的问题，如果手动配置SuSEfirewall2解决我的问题？其实现在已经水到渠成了

	#eth0相当于外网，与internet连接，ppp0相当于内网，连接vpn客户端。
	FW_DEV_EXT="eth0"
	#ppp0相当于内网，但是我想多个设备同时连接vpn服务器，就需要多个ppp连接，
	#用any表示除了已经列出的以外所有的设备，保证有多个设备同时连接的话，也不会被
	#防火墙过滤，如果设备不多的话，可以都写出来
	#FW_DEV_INT="ppp0 ppp1"
	FW_DEV_INT="any"
	#打开ip_forward
	FW_ROUTE="yes"
	FW_MASQUERADE="yes"
	FW_MASQ_NETS="192.169.0.0/24"

测试一下，一切OK!如果还是不能连接的话，可以去检查/var/log/message， 上面记录防火墙的过滤信息包

#参考资料
