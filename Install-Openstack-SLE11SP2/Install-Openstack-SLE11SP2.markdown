#准备软件源

下载suse cloud iso

	wget http://download.suse.de/install/SLE-11-SP2-CLOUD-GM/

升级python

	zypper ar -f http://download.suse.de/full/full-sle11-sp2-x86\_64/ full

check iptables version, not higher than 1.4.7
	
	rpm -q iptables 
       	

安装基本按照[这里](http://www.hastexo.com/resources/docs/installing-openstack-essex-20121-ubuntu-1204-precise-pangolin)的进行就可以,
文对其中没有提到的做补充
	
关闭susefirewall,防止冲突,不过目前并不确定一定冲突

#安装kvm支持

通过yast2安装

#网络规划

内网IP是192.168.3.0/24, 以后分配给虚拟机, 外网IP是147.2.207.XXX， 用yast2 network配置网络(在单网卡的情况下)


![网络配置](./config.png)


#安装rabbitmq-server

	zypper in rabbitmq-server

启动rabbitmq-server
	
	rcrabbitmq-server start

#安装 mysql

    zypper in mysql mysql-client python-mysql

启动mysql

    service mysql start    

建立用户（后面nova, glance会用到)

    mysql -u root <<EOF
    CREATE DATABASE nova;
    GRANT ALL PRIVILEGES ON nova.* TO 'novadbadmin'@'%' 
      IDENTIFIED BY 'suse';
    EOF

    mysql -u root <<EOF
    CREATE DATABASE glance;
    GRANT ALL PRIVILEGES ON glance.* TO 'glancedbadmin'@'%' 
      IDENTIFIED BY 'suse';
    EOF

#安装keystone

keystone是openstack的认证系统

	zypper in openstack-keystone  python-keystoneclient

keystone默认使用sqlite数据库, 这里不用修改. 

##修改keystone配置文件

修改/etc/keystone/keystone.conf, catalog部分改为（或保持不变)

	[catalog]
	driver = keystone.catalog.backends.templated.TemplatedCatalog
	template_file = /etc/keystone/default_catalog.templates

此外设置admin_token,以后于glance，nova连接,这里token写成*suse*

	admin_token=suse

/etc/keystone/default\_catalog.templates从相同文件夹下的samples文件得到，修改 %SERVICE\_HOST%为对外的IP
获得default_catalog.templates文件时，确保owner为openstack-keystone

	openstack01:/etc/keystone # head  default_catalog.templates
	# config for TemplatedCatalog, using camelCase because I don't want to do
	# translations for legacy compat
	catalog.RegionOne.identity.publicURL = http://147.2.207.105:$(public_port)s/v2.0
	catalog.RegionOne.identity.adminURL = http://147.2.207.105:$(admin_port)s/v2.0
	catalog.RegionOne.identity.internalURL = http://147.2.207.105:$(public_port)s/v2.0

	catalog.RegionOne.s3.publicURL = http://147.2.207.105:3333
	catalog.RegionOne.s3.adminURL = http://147.2.207.105:3333
	catalog.RegionOne.s3.internalURL = http://147.2.207.105:3333

启动keystone

	rcopenstack-keystone start

##建立admin用户

使用脚本keystone\_data.sh(来自项目devstack)注入数据[这里下载](./keystone_data.sh),修改其中的变量为

	ADMIN_PASSWORD=${ADMIN_PASSWORD:-suse}
	SERVICE_PASSWORD=${SERVICE_PASSWORD:-$ADMIN_PASSWORD}
	export SERVICE_TOKEN=suse
	export SERVICE_ENDPOINT=http://147.2.207.105:35357/v2.0

SERVICE_TOKEN与之前的admin_token对应，也是suse. ADMIN\_PASSWORD是以后admin用户登录
的密码。SERVICE\_ENDPOINT指向本机的外网IP. 以上配置完成后，运行

	keystone-manage db_sync
	rcopenstack-keystone start
	./keystone_data.sh

如果没有输出，表示一切正常.如果使用sqlite3有可能出现没有权限的问题，这时候

	chown keystone:keystone <your_sqlite3_file>

如果是用suse close iso安装的话，改为

  chown openstack-keystone:openstack-keystone /var/lib/keystone/keystone.db

##检查keystone运行正常

设置环境变量，keystone命令会使用一下的环境变量登录keystone,建议以后把这些命令写到bashrc中

	export OS_TENANT_NAME=admin
	export OS_USERNAME=admin
	export OS_PASSWORD=suse
	export OS_AUTH_URL="http://localhost:5000/v2.0/"

运行keystone user-list

	openstack01:~ # keystone user-list
	+----------------------------------+---------+--------------------+--------+
	|                id                | enabled |       email        |  name  |
	+----------------------------------+---------+--------------------+--------+
	| 238476bab62940ebb361ce3eaf970bc0 | True    | glance@example.com | glance |
	| 3bfbeb47f40248188cf414b5fe251c41 | True    | nova@example.com   | nova   |
	| ae7cc7026bc94389b49502a537aa823d | True    | demo@example.com   | demo   |
	| f1f701e2741046cba106ac4fc6275535 | True    | admin@example.com  | admin  |
	+----------------------------------+---------+--------------------+--------+

显示刚刚脚本导入的用户

#安装glance

	zypper in openstack-glance python-glanceclient

##添加keystone密码

配置glance连接keystone的密码,同时修改*2*个文件/etc/glance/glance-api-paste.ini, /etc/glance/glance-registry-paste.ini,

	admin_tenant_name = %SERVICE_TENANT_NAME%
	admin_user = %SERVICE_USER%
	admin_password = %SERVICE_PASSWORD%
改为
	admin_tenant_name = admin
	admin_user = admin
	admin_password = suse

其中suse是keystone\_data.sh配置的admin用户密码

##配置glance

之前配置了keystone的密码，现在要同时修改文件/etc/glance/glance-registry.conf, /etc/glance/glance-api.conf,
增加

	[paste_deploy]
	flavor = keystone

##编辑sql连接

编辑文件/etc/glance/glance-registry.conf

    sql_connection = mysql://glancedbadmin:suse@147.2.207.105/glance

##启动检查glance

	rcopenstack-glance-api start
	rcopenstack-glance-registry start

运行glance index, 检查是否正确连接keystone,如果没有报错, 表示正常, 可以进行下一步了
	
	glance index

##上传虚拟机镜像

	glance --os-username=admin --os-password=suse --os-tenant-name=admin --os-auth-url=http://127.0.0.1:5000/v2.0 image-create --name="sles11-sp2" --is-public=true --container-format=ovf --disk-format=qcow2 < SLES\_11\_SP2.x8\6_64-0.0.1.raw
	glance --os-username=admin --os-password=suse --os-tenant-name=admin --os-auth-url=http://127.0.0.1:5000/v2.0 image-list

#安装nova
	
nova是openstack的核心, 

	zypper in openstack-nova

add openstack-nova to sudo list

	visudo
	add line "openstack-nova  ALL=(ALL) NOPASSWD:ALL"

##nova的配置文件

nova的配置文件比较简单，只有2个配置文件需要修改, 打开/etc/nova/nova.conf, 用下面覆盖

	# example nova.conf
	# replace the values 
	#--allow_admin_api
	--auth_strategy=keystone
	--compute_scheduler_driver=nova.scheduler.filter_scheduler.FilterScheduler
	--daemonize=1
	--dhcpbridge_flagfile=/etc/nova/nova.conf
	--dhcpbridge=/usr/bin/nova-dhcpbridge
	--logdir=/var/log/nova
	--state_path=/var/lib/nova
	--lock_path=/var/lock/nova
	--my_ip=147.2.207.105
	--verbose=True
	--public_interface=eth0
	--instance_name_template=instance-%08x
	#--osapi_extension=nova.api.openstack.v2.contrib.standard_extensions
	#--osapi_extension=extensions.admin.Admin
	--osapi_compute_extension=nova.api.openstack.compute.contrib.standard_extensions
	--api_paste_config=/etc/nova/api-paste.ini
	--image_service=nova.image.glance.GlanceImageService
	--ec2_dmz_host=147.2.207.105
	--rabbit_host=localhost
	--glance_api_servers=147.2.207.105:9292
	--force_dhcp_release=True
	--flat_network_bridge=br0
	--firewall_driver=nova.virt.libvirt.firewall.IptablesFirewallDriver
	--sql_connection=mysql://novadbadmin:suse@192.168.3.1/nova
	--s3_host=147.2.207.105
	--s3_port=3333
	--ec2_url=http://147.2.207.105:8773/services/Cloud
	--network_manager=nova.network.manager.FlatDHCPManager
	--fixed_range=192.168.3.0/24
	--network_size=256
	--connection_type=libvirt
	--libvirt_type=kvm
	#--bridge_interface=br0
	--vnc_enabled=true
	--novncproxy_base_url=http://147.2.207.105:6080/vnc_auto.html
	--xvpvncproxy_base_url=http://147.2.207.105:6081/console
	--vncserver_listen=0.0.0.0
	--vncserver_proxyclient_address=147.2.207.105
	#--multi_host=True
	#--send_arp_for_ha=True

修改对应的ip,就可以了

修改文件/etc/nova/api-paste.ini, 因为nova也需要知道keystone的密码,加入如下行

	admin_tenant_name = admin
	admin_user = admin
	admin_password = suse
	admin_token = suse

数据库配置见参考资料

##同步数据库，启动nova

同步数据库

	nova-manage db sync

建立fixed的IP(相当于内网IP)

	nova-manage network create private --fixed_range_v4=192.168.3.1/24 --bridge=br0 

启动nova

	for i in nova-cert nova-network nova-compute nova-api nova-objectstore \
		 nova-scheduler nova-volume nova-consoleauth novncproxy nova-vncproxy;\
	do \
	  rcopenstack-${i} restart; \
	  sleep 1; \
	done


检查nova的所有服务

	openstack01:/var/lib/glance # nova-manage service list
	2012-05-23 04:01:26 DEBUG nova.utils [req-d26844ba-8755-479b-b433-a3b2692ee5bf None None] backend <module 'nova.db.sqlalchemy.api' from '/usr/lib64/python2.6/site-packages/nova/db/sqlalchemy/api.pyc'> from (pid=25527) __get_backend /usr/lib64/python2.6/site-packages/nova/utils.py:658
	2012-05-23 04:01:26 WARNING nova.utils [req-d26844ba-8755-479b-b433-a3b2692ee5bf None None] /usr/lib64/python2.6/site-packages/sqlalchemy/pool.py:639: SADeprecationWarning: The 'listeners' argument to Pool (and create_engine()) is deprecated.  Use event.listen().
	  Pool.__init__(self, creator, **kw)

	2012-05-23 04:01:26 WARNING nova.utils [req-d26844ba-8755-479b-b433-a3b2692ee5bf None None] /usr/lib64/python2.6/site-packages/sqlalchemy/pool.py:145: SADeprecationWarning: Pool.add_listener is deprecated.  Use event.listen()
	  self.add_listener(l)

	Binary           Host                                 Zone             Status     State Updated_At
	nova-compute     openstack01                          nova             enabled    :-)   2012-05-23 08:01:23
	nova-network     openstack01                          nova             enabled    :-)   2012-05-23 08:01:20
	nova-scheduler   openstack01                          nova             enabled    :-)   2012-05-23 08:01:20
	nova-volume      openstack01                          nova             enabled    :-)   2012-05-23 08:01:20
	nova-consoleauth openstack01                          nova             enabled    :-)   2012-05-23 08:01:20
	nova-cert        openstack01                          nova             enabled    :-)   2012-05-23 08:01:2

waring可以忽略


显示所有的虚拟机

	nova list

显示所以的镜像

	nova image-list

##配置nova-volumes

创建vg nova-volumes, 这里/dev/sda9是一个pv
	
	pvcreate /dev/sda9
	vgcreate nova-volumes /dev/sda9

在control节点，也就是vg所在的节点打开iscsi-target
	
	rciscsitarget start	

在所有的计算节点， 打开open-iscsi
	
	rcopen-iscsi start

这样这些volumes就可以动态的添加到虚拟机中,参见[文档](http://docs.openstack.org/trunk/openstack-compute/admin/content/managing-volumes.html)



#第一台虚拟机

显示可用的镜像
	
	nova image-list

显示可以用的flavor, flaver表示给虚拟机分配资源的多少，如cpu，内存等等
	
	nova flavor-list

启动虚拟机

	nova boot --flavor <ID> --image <Image-UUID> --key_name <key-name> <vm_name>

<ID>, <Image-UUID>, <key_name>, <vm_name> 填入对应值, 如我的例子
	
	nova boot --flavor m1.tiny --image e504c1b5-da5b-42e2-bcd5-2e229175b46c --key_name key1 sles-hello

显示虚拟机详细信息

	nova show sles-hello

登录虚拟机

	ssh <sles-hello的内网IP>

#安装dashboard

dashboard是openstack的web管理端,用django实现

	zypper in openstack-dashboard, apache2-mod_wsgi

##修改dashboard配置文件

编辑/var/lib/openstack-dashboard/openstack_dashboard/local/local_settings.py, 可以在这里修改默认的数据库,
不过在非生产环境，不用修改.

同步dashboard数据库

	cd /var/lib/openstack-dashboard
	./manage.py syncdb

如果没有修改过配置文件，sqlite3的数据库文件名称是dashboard\_openstack.sqlite,修改权限

	chown wwwrun:www /var/lib/openstack-dashboard/openstack_dashboard/local/dashboard_openstack.sqlite3
	chown -R wwwrun:www /var/lib/openstack-dashboard/

##修改apache配置文件

apache插入wsgi模块

	a2enmod wsgi

在/etc/apache2/vhosts.d/下加入文件apache-horizon.conf

	<VirtualHost *:80>
	    WSGIScriptAlias / /var/lib/openstack-dashboard/openstack_dashboard/wsgi/django.wsgi
	    WSGIDaemonProcess horizon user=wwwrun group=root processes=3 threads=10 home=/var/lib/openstack-dashboard

	    SetEnv APACHE_RUN_USER wwwrun
	    SetEnv APACHE_RUN_GROUP root
	    WSGIProcessGroup horizon

	    DocumentRoot /var/lib/openstack-dashboard/.blackhole/
	    Alias /media /var/lib/openstack-dashboard/openstack_dashboard/static

	    <Directory />
		Options FollowSymLinks
		AllowOverride None
	    </Directory>

	    <Directory /var/lib/openstack-dashboard/>
		Options Indexes FollowSymLinks MultiViews
		AllowOverride None
		Order allow,deny
		allow from all
	    </Directory>

	    ErrorLog /var/log/apache2/horizon_error.log
	    LogLevel warn
	    CustomLog /var/log/apache2/horizon_access.log combined
	</VirtualHost>
	WSGISocketPrefix /var/run/apache2

##启动apache

	rcapache2 start

访问http://localhost/可以看到管理端, 用户名admin，密码suse， 大功告成！


#参考文档

*	http://www.hastexo.com/resources/docs/installing-openstack-essex-20121-ubuntu-1204-precise-pangolin
