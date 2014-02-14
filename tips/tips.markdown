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
		if test -d $src -o -h $src
		then
			echo "delete previous link"
			rm -rf $src
		elif test -f $src
		then
			echo "delete previous file"
			rm -rf $src
		elif test -d $src
		then
			echo "$src is not a symlink,quit.."
			exit
		fi

		echo "create link $src"
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
	
	git format-patch HEAD~2 -o ./patches --cover-letter -M -n --thread=shallow

注意参数

HEAD~2 表示最近的2个commits

-o ./patches 表示输出patch的位置

编辑生成的0000-cover-letter,总要吹嘘一下

## 发邮件	

	git send-email --thread --no-chain-reply-to --suppress-from ./patches --to=maillist@maillist.com


# systemtap 

* suse doc for systemtap
https://www.suse.com/documentation/sles11/singlehtml/book\_sle\_tuning/book\_sle\_tuning.html

* begin guide
http://sourceware.org/systemtap/SystemTap\_Beginners\_Guide/index.html

* library 
http://sourceware.org/systemtap/tapsets/index.html

* taobao script
http://blog.yufeng.info/archives/tag/systemtap

* ibm redbook
http://www.redbooks.ibm.com/redpapers/pdfs/redp4469.pdf

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


## 读crash文件

	crash> bt 6559
	PID: 6559   TASK: ffff8818262c85c0  CPU: 0   COMMAND: "lvs"
	 #0 [ffff881a100f7ab8] schedule at ffffffff8139c604
	 #1 [ffff881a100f7b70] io_schedule at ffffffff8139c9d2
	 #2 [ffff881a100f7ba0] sync_page at ffffffff810b6565
	 #3 [ffff881a100f7bb0] __wait_on_bit at ffffffff8139cf20
	 #4 [ffff881a100f7bf0] wait_on_page_bit at ffffffff810b6a4c
	 #5 [ffff881a100f7c40] wait_on_page_writeback_range at ffffffff810b7a54
	 #6 [ffff881a100f7d20] filemap_write_and_wait_range at ffffffff810b7bcf
	 #7 [ffff881a100f7d50] generic_file_aio_read at ffffffff810b7fda
	 #8 [ffff881a100f7de0] do_sync_read at ffffffff810ff703
	 #9 [ffff881a100f7f10] vfs_read at ffffffff810ffe77
	#10 [ffff881a100f7f40] sys_read at ffffffff810fffe3
	#11 [ffff881a100f7f80] system_call_fastpath at ffffffff81002f7b
	    RIP: 00002b233f0ac560  RSP: 00007fff0e96bb28  RFLAGS: 00010206
	    RAX: 0000000000000000  RBX: ffffffff81002f7b  RCX: 00007fff0e96bb4f
	    RDX: 0000000000001000  RSI: 00007fff0e96a000  RDI: 0000000000000004
	    RBP: 00007fff0e96bbd0   R8: fffffffffffff000   R9: 0000000000001000
	    R10: 0000000000000001  R11: 0000000000000246  R12: 0000000000000004
	    R13: 0000000000000000  R14: 00007fff0e96a000  R15: 00000000006abdc8
	    ORIG_RAX: 0000000000000000  CS: 0033  SS: 002b


