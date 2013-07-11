#在sles下，build一个模块

##pre-requires

1. kernel-src
	 当然是源码
2. kernel-devel
   包含include/generated/autoconf.h, Module.symvers等重要文件,编译modules时需要．

##build

参考Document/kbuild/modules.txt

1. 修改源代码

2. 举例修改drivers/md/下代码

3. cd /usr/src/linux/drivers/md

4. make -C /lib/modules/\`uname -r\`/build M=\`pwd\` modules
	 #其中/lib/modules/\`uname -r\`/build/指向kernel-devel安装的一些objs

5. make -C /lib/modules/\`uname -r\`/build M=\`pwd\` modules\_install
	 #会安装到/lib/modules/\`uname -r\`/extra下面

6. #检查/lib/modules/\`uname -r\`/modules.dep, 如果没有更新
	 depmod

7. #如果需要更新initrd,
	 mkinitrd

这种方法充分利用了发行版提供的kernel-devel中的文件. 在保证使用相同kernel的情况下，
快速编译modules


#内部的repo

	yast2 -> support -> local auth server 

147.2.207.207/center/regsvc
本地repo, 比dist.suse.de/full快很多, 如果缺devel的包，到240找sdk的repo



#修复虚拟机文件

只在虚拟机镜像是本地文件时采用

1. kpart -a /var/lib/xen/linux-node1.img
   映射到本地loop设备上

2. mount分区, 一般在/dev/mapper下

3. 修复,(可以考虑用chroot)

4. umount分区

5. kpart -d /var/lib/xen/linux-node1.img


#localbuild的脚本

rpmbuild要求spec文件，src文件在/usr/src下，比较麻烦，下面的脚本做一个软链接，在任何源文件下都可以做rpmbuild了

用法:

	localbuild -bb file.spec

代码:

	#!/bin/bash
	#check local build system
	check_build_fs()
	{
		#exclude SOURCES
		for dir in ~/rpmbuild/{BUILD,RPMS,SPECS,SRPMS}
		do
			if [[ ! -d $dir ]]
			then
				echo "$dir not exsit"
				echo "mkdir -p $dir"
				mkdir -p $dir
			fi
		done
	}

	check_rpm_macro()
	{
		echo '%_topdir %(echo $HOME)/rpmbuild' > ~/.rpmmacros
	}

	mount_current_diretory()
	{
		src=~/rpmbuild/SOURCES
		if test -d $src -a -h $src
		then
			echo "delete previous link"
			rm $src
		elif test -f $src
		then
			echo "delete previous file"
			rm $src
		elif test -d $src
		then
			echo "$src is not a symlink,quit.."
			exit
		fi

		echo "create link $src"
		rm -rf $src
		ln -s \`pwd\` $src
	}

	check_build_fs
	check_rpm_macro
	mount_current_diretory
	args=$*
	rpmbuild $args

#在local中增加debug-info

编辑spec文件, 加入 %debug\_package



# git发patch

基本流程就三步

## 修改git配置文件

	[sendemail]
		smtpencryption = tls
		smtpserver = smtp.novell.com
		smtpuser = dmzhang@suse.com
		smtpserverport = 25
		smtppass = XXXXX

## 生成patch
	
	git format-patch HEAD~2 -o ./patches --cover-letter -M 

注意参数

HEAD~2 表示最近的2个commits

-o ./patches 表示输出patch的位置

编辑生成的0000-cover-letter,总要吹嘘一下

## 发邮件	

	git send-email ./patches --to=maillist@maillist.com


# systemtap 

* suse doc for systemtap
https://www.suse.com/documentation/sles11/singlehtml/book\_sle\_tuning/book\_sle\_tuning.html

* begin guide
http://sourceware.org/systemtap/SystemTap\_Beginners\_Guide/index.html

* library 
http://sourceware.org/systemtap/tapsets/index.html

* taobao script
http://blog.yufeng.info/archives/tag/systemtap

我的一个脚本

	global times, each_bio_time, each_sync_time

	global stat, timestamps

	global start_record_cpu_flag = 0

	probe module("dm_log_userspace").function("userspace_in_sync") {
					times["userspace_sync"] = gettimeofday_ns()
	}

	probe module("dm_log_userspace").function("userspace_in_sync").return {
					if(times["userspace_sync"])
					each_sync_time <<< gettimeofday_ns() - times["userspace_sync"]
	}

	probe module("dm_mirror").function("mirror_map") {
					times["bio"] = gettimeofday_ns()
					if (start_record_cpu_flag == 0)
									start_record_cpu_flag = 1
	}

	probe module("dm_mirror").function("mirror_end_io").return {
					if(times["bio"])
									each_bio_time <<< gettimeofday_ns() - times["bio"]
	}



	probe scheduler.cpu_on {
					if(start_record_cpu_flag)
					timestamps[cpu(), execname()] = gettimeofday_ns()
	}

	probe scheduler.cpu_off{
					if (start_record_cpu_flag && timestamps[cpu(), execname()]) {
									stat[execname()] += gettimeofday_ns() - timestamps[cpu(), execname()]
									delete(timestamps[cpu(), execname()])
					}
	}

	probe end {
					sum_time = 0

					foreach( execname in stat- limit 20) {
									printf("%s run %d ns\n",execname, (stat[execname]))
									sum_time += stat[execname]
					}

					printf("======== sum ==================")
					printf("\ncpu run time    : %d ns", sum_time)
					printf("\ntotal sync time : %d ns", @sum(each_sync_time))
					printf("\ntotal bio  time : %d ns\n" ,@sum(each_bio_time))
					printf("===============================\n")
	}


