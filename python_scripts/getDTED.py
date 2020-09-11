# -*- coding: utf-8 -*-
#"""
#Created on Wed Jul 23 19:58:44 2014
#
#@author: Russ
#"""

from bs4 import BeautifulSoup
import urllib2
import re
import zipfile
import glob, os

def get_data():
    # site details
    #urls = {'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Africa/',
    #        'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Australia/',
    #        'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Eurasia/',
    #        'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/Islands/',
    #        'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/South_America/',
    #        'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/'}

    urls = {'http://dds.cr.usgs.gov/srtm/version2_1/SRTM3/North_America/'}
    
    for url in urls:
    
        html_data = urllib2.urlopen(url)
        soup = BeautifulSoup(html_data)
        for link in soup.findAll('a'):
            file_link = url + link.get('href')
            file_name = file_link.split('/')[-1]
            if not file_name:
                continue
            f = open(file_name,'wb')
            u = urllib2.urlopen(file_link)
            meta = u.info()
            file_size = int(meta.getheaders("Content-Length")[0])
            print "Downloading: %s Bytes: %s" % (file_name, file_size)
            
            file_size_dl = 0
            block_sz = 8192
            while True:
                buffer = u.read(block_sz)
                if not buffer:
                    break
                
                file_size_dl += len(buffer)
                f.write(buffer)
                status = r"%10d  [%3.2f%%]" % (file_size_dl, file_size_dl * 100. / file_size)
                status = status + chr(8)*(len(status)+1)
                print status,
                
            f.close()

def unpack_data():
    file_list = glob.glob("*.zip")
    for myfile in file_list:
        file_parts = myfile.split('.')
        latlonval = re.split('E|W',file_parts[0])        
        if not os.path.exists(latlonval[0]):
            os.makedirs(latlonval[0])
        f = open(myfile,'rb')
        z= zipfile.ZipFile(f)
        outpath = os.curdir + os.sep + latlonval[0]
        z.extractall(outpath)
        f.close()


#get_data()
unpack_data()        
        
