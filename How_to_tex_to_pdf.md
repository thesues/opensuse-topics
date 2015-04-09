# Xetex简介 #

什么事xetex？ http://en.wikipedia.org/wiki/XeTeX
简单的说，xetex是一种支持unicode编码的，支持opentype字体的一种tex引擎。
这2点说明它可以很好的支持中文，直接使用本地字体生成pdf。

这个特点主要是为了和之前tex的中文方案作对比，以前是采用中文宏包的方式，
我记得以前用latex2pdf生成一个pdf后，发现文件中字体粗细不一，非常难看，还需要先用latex生成dvi文件，然后再转成pdf。这样才可以
用之前中文方案的tex文件有一个鲜明的特征，就是里面有一句话
\usepackage{CJK}。所以你要是看到还有的文档在讲之前的中文方案，就可以不用看了,
以后大家都会转成使用xetex（tex论坛上都这么说），也是以后的趋势

现在有xelatex命令，工作就简单很多了。写完tex文件，一条命令xelatex，就能生成可打印的pdf文件。还有tex2pdf，latex等等命令都可以不管了，反正我们现在也用不到
# 常见问题！！ #
## 不会安装texlive ##
windows去http://ctex.org下载ctex套装，打开winedit就可以用了

opensuse 11.4 用命令`zypper in texlive-xetex`安装

ubuntu的源中不包括ctex，最好去官网下载texlive安装

## xelatex编译的时候出错！ ##
仔细看一下一般是缺少某个宏包，是sty结尾的,在ubuntu下用texlive会有这个问题
，因为包没有装全

用命令tlmgr安装缺省的包！

## pdf文件打开不显示中文！ ##
缺少adobe字体，从http://get.adobe.com/cn/reader/下载pdf阅读器

adobereader有windows版有linux版，安装就可以了



# 安装texlive #

## opensuse安装texlive ##
```
zypper in texlive-xetex
zypper in texlive-xetex-2010-4.6.noarch
zypper in latex2html
```
latex2html不属于texlive，但是我们也需要它生成html
## ubuntu安装texlive ##
我在使用的ubuntu11.04，对ctex的支持一般，建议还是不要从源下载tex，直接从官方网站
选择网络安装texlive，http://www.tug.org/texlive/acquire-netinstall.html，
http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz，
下载完成后解压缩，在安装前最好先安装perl-tk，支持一个简单的图形界面
在解压缩的包中运行
```
sudo ./install-tl --gui
```
在图形界面中，安装方案选media，语言选择安装中文包就可以了，这样最多是只安装700m的文件，比全安装少很多。

安装完成以后，配置环境变量，运行tlmgr安装ctex和xecjk和其他依赖的sty，由于tlmgr自动识别依赖不完善，下面的依赖是一个一个找的
```
sudo tlmgr install xecjk ctex savesym framed enumitem etoolbox etoolbox
```
如果以后还缺任何包，用tlmgr install命令就可以了，ubuntu自己的deb包并没有tlmgr，很不方便，我在ppa上看到有人提了这个bug，并且已经接受，希望以后会更新

## windows安装texlive ##
可以以选择直接从官网下载texlive的光盘
http://www.tug.org/texlive/,下载完后安装
也可以从http://ctex.org下载包,强烈推荐使用ctex.org的包，它为中文用户做过优化，
也去掉了不需要的语言。

## 安装adobe字体 ##

这个项目用的字体是adobe的中文字体,主要包括
AdobeFangsongStd，AdobeHeitiStd，AdobeKaitiStd，
AdobeSongStd。
这些字体只要安装完acrobat reader中文版（acrobat reader也有linux平台的），一般都会有，如果还是没有的话，可以从这里下载http://code.google.com/p/opensuse-topics/downloads/detail?name=fonts.zip&can=2&q=,这些字体是可以免费使用的。
google一下，很多地方也都可以下到


# 第一个tex文件 #
检查安装环境是否正确，用一个文本编辑器编辑一个test.tex的文件
里面的内容如下
```
\documentclass[adobefonts]{ctexart}
\begin{document}
\section{第一章}
第一章内容
\end{document}
```
运行命令
```
xelatex test.tex
```
生成中文显示正常的pdf文件，说明已经安装正确，可以编辑自己的文档了！！

# 编辑tex文件 #
tex文件很像html文件，文件头部是一些meta，列举引用的宏包
文章内容从\begin{document}开始。写法与wiki类似。

\section是一个章节

\subsection是子章节

## 分段，强制分行 ##
一般的回车是不会分段的，用空行强制分段，用\\强制分行
## 插入图片 ##
插入图片需要用宏包graphicx
在开头
```
\usepackage{graphicx}
```
插入图片的的格式是eps,eps格式是一种用于打印的格式，
一般如photoshop，gimp，imagemagick,inkscape都支持导出为eps，
如matlab之类工具的截图功能，可以直接导出eps文件
插入图片

```
\begin{figure}[htbp]
  \includegraphics[width=6cm]{图片.eps}
\end{figure}
```
一般的参数都会选择[htbp](htbp.md),完全适用于一般情况,具体的更详细内容请
参考[latex图形指南](http://www.ctex.org/documents/latex/graphics/)
## 插入表格 ##
[详细说明](http://en.wikibooks.org/wiki/LaTeX/Tables)

tabular非常聪明，可以容易的生成复杂的表格，你只需要关注内容，最好latex一定会帮你生成宽度合适的表格。
## 插入公式 ##
插入公式是tex的杀手特性

## 转义字符 ##
在写latex文件的时候，有一些字符是有特殊含义的比如%，\,
如果要在文本中使用，要加上转义符
$ &  % # _{ }_

需要写成

\$ \& \% \# \_\{ \}_

强制断行\\

分段 空一行




# 生成HTML文件 #

在工程中,makefile中用latex2html把tex文件转换成html，请参看latex2html文档，
用命令
```
make html
```
可以生成html文件


# 上传pdf文件 #

在工程中，用命令
```
make download
```
把生成的pdf文件上传到code.google.com提供下载