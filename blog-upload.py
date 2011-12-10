import sys
import os.path
import shutil
from HTMLParser import HTMLParser
import xmlrpclib
import mimetypes
import cPickle
import hashlib

class parseHtml(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.images=[]
        self.titletag=False
    def handle_starttag(self,tag,attrs):
        if tag=='img':
            img=[v for k,v in attrs if k=='src']
            self.images.append(img[0])
        if tag=='title':
            self.titletag=True
    def handle_data(self,data):
        if self.titletag:
            self.title=data
            self.titletag=False
    def getImages(self):
        return self.images
    def getTitle(self):
        return self.title

class CleanArtical:
    def __init__(self,filename):
        """
        
        Arguments:
        - `self`:
        - `filename`:
        """
        try:
            self.htmlname=os.path.join('blog',filename.split('.')[0]+'.html')
            f=open(self.htmlname,'r')
            self.data=f.read()
            f.close()
            self.images=[]
        except IOError:
            print "%s not find" % filename
            raise
    def process(self):
         """
         """
         #remove vsftpd.html name
         self.data=self.data.replace(os.path.basename(self.htmlname),'')
         #get all images to be upload
         x=parseHtml()
         x.feed(self.data)
         self.images=x.getImages()
         self.title=x.getTitle()

    def replaceImage(self,old_image,new_image):
        self.data=self.data.replace(old_image,new_image)
    def getData(self):
        return self.data
    def getImages(self):
        return self.images
    def gethtmlname(self):
        return self.htmlname
    def getTitle(self):
        return self.title
 
def checkUlr(url):
    try:
        urllib2.urlopen(url)
    except HTTPError:
        return False
    return True
 

class Publish:
    def __init__(self,*args):
        """
        
        Arguments:
        - `self`:
        - `*args`:
        """
        self.methods=args

    def publish(self,texfilename):
        """
        
        Arguments:
        - `self`:
        """
        for i in self.methods:
            i.publish(texfilename)
        
class MetaBlog:
    def  __init__(self,appurl,username,password):
        self.appurl=appurl
        self.username=username
        self.password=password
        self.server=xmlrpclib.ServerProxy(appurl)
        self.postidFile='./.'+hashlib.sha1(appurl).hexdigest()+'_'+username+'.postid'
        self.postid=''
    def publish(self,texfilename):
        #generate html
        os.system("make blog")
        parser=CleanArtical(texfilename)
        parser.process()
        #find whether changed or first update
        if os.path.isfile(self.postidFile):
            f=open(self.postidFile,'r')
            self.postid=cPickle.load(f)
            f.close()
            #todo upload images although
            for i in parser.getImages():
                new_image_name=self.new_image("blog/"+i)
                print new_image_name
                parser.replaceImage(i,new_image_name)            
            self.edit_post(self.postid,parser.getTitle(),parser.getData())
        else:
            #upload images
            for i in parser.getImages():
                new_image_name=self.new_image("blog/"+i)
                print new_image_name
                parser.replaceImage(i,new_image_name)
            self.postid=self.new_post(parser.getTitle(),parser.getData())
            print self.postid
            #TODO write postid
            f=open(self.postidFile,'w')
            cPickle.dump(self.postid,f)
            f.close()

    def edit_post(self,postid,title,content,publish=True):
        newpost={}
        newpost['title']=unicode(title,'utf8')
        newpost['description']=unicode(content,'utf8')
        return self.server.metaWeblog.editPost(postid,self.username,self.password,newpost,publish)


    def get_post(self,postid):
        #server.metaWeblog.getRecentPosts('',user,passw)
        return self.server.metaWeblog.getPost(postid,self.username,self.password)

    def new_post(self,title,content,publish=True):
        #newPost("", account[0], account[1], struct, True)
        newpost={}
        newpost['title']=unicode(title,'utf8')
        newpost['description']=unicode(content,'utf8')
        print newpost['title']
        return self.server.metaWeblog.newPost('',self.username,self.password,newpost,publish)

    def get_recent_posts(self):
        return self.server.metaWeblog.getRecentPosts('',self.username,self.password)

    def new_image(self,new_image):
        try:
            img=open(new_image)
            data=img.read()
            img.close()
        except IOError:
            raise
        new_object={}
        new_object['name']=os.path.basename(new_image)
        new_object['type']=mimetypes.guess_type(new_image)[0] or 'application/octet-stream'
        new_object['bits']=xmlrpclib.Binary(data)
        print new_object
        return self.server.metaWeblog.newMediaObject('',self.username,self.password,new_object)['url']

class Wiki:
    def __init__(self):
        pass
    def publish(self,texfilename):
        pass

class CodeGoogle:
    def __init__(self):
        pass
    def publish(self,texfilename):
        pass
        
if __name__=='__main__':
#    artical=CleanArtical(sys.argv[1])
 #   artical.process()
    b=MetaBlog('http://deanraccoon.is-programmer.com/xmlrpc','deanraccoon','89714942')
#########    suse_china=MetaBlog('http://upload.move.blog.sina.com.cn/blog_rebuild/blog/xmlrpc.php','cn.suse@gmail.com','3s8sanihc')
    localhost_wordpress=MetaBlog('http://localhost/wp/xmlrpc.php','admin','admin')
    wiki=Wiki()
    codegoogle=CodeGoogle()
    pp=Publish(b)
    pp.publish(sys.argv[1])
