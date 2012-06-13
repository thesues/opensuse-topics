<meta http-equiv="content-type" content="text/html; charset=utf-8" />

HAE安装配置手册：虚拟机环境================

#环境构成

##HOST

	OS:	SLES11-SP2   
	Package: yast2-iscsi-server,虚拟机(qemu+kvm)   
	Partition: 至少一个分区,用作ISCSI-SERVER STORAGE   
	FILE： /etc/hosts文件中需要添加所有GUEST的信息

##GUEST(3个)

	OS:	SLES11-SP2   
	Package: yast2-iscsi-client, vm2-clvm   
	Partition: 至少一个分区,用作ISCSI-SERVER STORAGE   
	FILE： /etc/hosts文件中需要添加所有GUEST的信息
 
##iscsi配置

###HOST 

分配sda8，sda9，sda10三个分区用做iscsi storage, 分别映射为guest的sda/sdb/sdc.

yast2-iscsi-server安装： 

	zypper in yast2-iscsi-server

server配置： 

	yast2 iscsi-server
   
###Guest

共享磁盘构成如下

* sda(sda1: stonith/sbd分区)   
* sdb(sdb1: DRBD分区|sdb2: LVM的pv分区)   
* sdc(sdc1: DRBD分区|sdc2: LVM的pv分区)

yast2-iscsi-client安装：

	zypper in yast2-iscsi-client

client配置： 

Service->Service Start(when booting)    
Connected Targets->Add->iscsi Initiator Discovery->IP Address(hostserver ip)->connect->Startup(automatic)

确认共享资源设置正确: lsscsi

关于iscsi的配置请参见[Configuring iSCSI Initiator](http://www.linuxtopia.org/online_books/suse_linux_guides/SLES10/suse_enterprise_linux_server_installation_admin/sec_inst_system_iscsi_initiator.html)
  

#HA安装

   * 数据源安装（3个节点上都需要安装)

    命令行执行： 

	zypper in yast2-cluster

   * add-on安装

    详细请参见[Installation as Add-on](http://doc.opensuse.org/products/draft/SLE-HA/SLE-ha-guide_sd_draft/cha.ha.installation.html#sec.ha.installation.add-on)

#HA配置

   * HA资源配置图如下：

    ![构成图](./HA-Configuration.png)

   * 本文档描述了以下资源的配置过程

	SBD-->stonith_sbd   
	DLM-->dlm1   
	O2CB-->o2cb   
	CLVM-->clvm  
	LVM-->vg1   
	OCFS2-->ocfs2-1
 

##基础配置过程

* 配置文件一致化设定

在3个节点其中之一上执行一下操作(确认sshd服务已经启动并支持root远程访问)

	cd /etc/csync2
	scp csync2.cfg key_hagroup  srv2:/etc/csyc2   
	scp csync2.cfg key_hagroup  srv3:/etc/csyc2

* 打开csync2

命令行执行: 

	yast2 cluster

选择Configure Csync2配置页面:

	Turn csync2 ON

![Csync2设置图](./ha-csync2-configure.png)

* 同步配置文件

命令行执行：

	csync2 -xv

同步过程中如果出现文件冲突的error: Error file 。。。。文件不一致冲突

则手动强制同步冲突文件：

	csync2 -f filename（filename为冲突的文件）

* 启动cluster(建议使用手动启动方式)

打开所有节点的防火墙, cluster中打开防火墙对应的端口.

命令行执行：

	rcopenais start

* 管理cluster

使用crm_gui图形管理工具管理cluster

使用前需要在各个GUEST节点设置用户hacluster的密码（该用户在crm_gui图形管理工具连接ha时使用)

也可以通过执行命令行 crm 进行管理
   

##SBD配置

SBD详细配置参见以下链接：

* [SBD_Fencing](http://www.linux-ha.org/wiki/SBD_Fencing)

* [Storage Protection](http://doc.opensuse.org/products/draft/SLE-HA/SLE-ha-guide_sd_draft/cha.ha.storage.protect.html)

###配置问题
   
* sbd -d /dev/XXX create失败   

解决办法：升级sbd(升级cluster-glue至小版本(35.17))   
其中clone的那台guest仍然报错
解决办法：fdisk 删除用做sbd的分区，重新创建分区后所有节点上都OK

	~# which sbd
	/usr/sbin/sbd
	~# rpm -qf /usr/sbin/sbd    
	cluster-glue-1.0.9-0.31.7
	~# zypper in cluster-glue

##DLM和O2CB配置

1. 命令行执行：

	crm configure

2. 输入以下内容：

	primitive dlm ocf:pacemaker:controld \
		op monitor interval="60" timeout="60"
	primitive o2cb ocf:ocfs2:o2cb \
		op monitor interval="60" timeout="60"
	group base-group dlm o2cb
	clone base-clone base-group \
	meta interleave="true"   

3. 查看配置是否正确

	show

4. 提交配置：

	commit

详细配置参照以下link

[Procedure 14.1. Configuring DLM and O2CB Resources](http://doc.opensuse.org/products/draft/SLE-HA/SLE-ha-guide_sd_draft/cha.ha.ocfs2.html)

##CLVM和LVM配置

###创建CLVM资源

1. 命令行执行：

	crm configure

2. 输入以下内容：

	primitive clvm ocf:lvm2:clvmd \
		params daemon_timeout="30"
	edit base-group

	在编辑模式下修改group为   
    
	group base-group dlm o2cb clvm

3. 确认修改正确

	show

4. 提交配置

	commit

###启动CLVM资源

通过crm\_gui或者crm命令行可以执行启动CLVM资源的操作.

###配置LVM卷组

####创建PV

	pvcreate /dev/sdb2   
	pvcreate /dev/sdc2

PV成功创建标志：

	Physical volume "/dev/sdb2" successfully created
	Physical volume "/dev/sdc2" successfully created

创建完成可以使用pvdisplay进行查看

####创建VG

	vgcreate -c cluster-vg /dev/sdb2 /dev/sdc2

####LVM配置详细参见以下link

[LVM配置](http://hengdao.blog.51cto.com/2631450/585318)

[LVM Configuration](http://www.suse.com/documentation/sles11/stor_admin/?page=/documentation/sles11/stor_admin/data/bookinfo.html)

###创建LVM资源

1. 命令行执行：

	crm configure

2. 输入以下内容：

	primitive vg1 ocf:heartbeat:LVM \
		params volgrpname="cluster-vg" \
		op monitor interval="60" timeout="60"
	edit base-group

	在编辑模式下修改group为   
	
	group base-group dlm o2cb clvm vg1

3. 确认修改正确

	show

4. 提交配置

	commit

##OCFS2配置
    
###创建LV

启动LVM资源后，创建LV

	lvcreate -l 65000  -n /dev/cluster-vg/test-lv cluster-vg

###mkfs

选择vg1逻辑分区做OCFS2分区，执行mkfs

	mkfs.ocfs2 -N 32 /dev/cluster-vg/test-lv

###配置OCFS2资源

1. 命令行执行：

	crm configure

2. 输入以下内容：

	primitive ocfs2-1 ocf:heartbeat:Filesystem \
		params device="/dev/cluster-vg/test-lv" directory="/mnt/shared" fstype="ocfs2" options="acl" \
		op monitor interval="20" timeout="40"
	edit base-group

	在编辑模式下修改group为   

	group base-group dlm o2cb clvm vg1 ocfs2-1
	
注：配置中的mountpoint:/mnt/shared, 需要在各个节点上手动创建.
      
3. 确认修改正确

	show

4. 提交配置

	commit

5. 退出

	quit 
  
详细配置参见[OCFS2: Procedure 14.3. Creating and Formatting an OCFS2 Volume](http://doc.opensuse.org/products/draft/SLE-HA/SLE-ha-guide_sd_draft/cha.ha.ocfs2.html)
