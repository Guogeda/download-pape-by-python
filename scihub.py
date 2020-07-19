# -*- coding: utf-8 -*-

"""
Sci-API Unofficial API
[Search|Download] research papers from [get doi from crossref|sci-hub.io].

@author geda 
"""

import re
import argparse
import hashlib
import logging
import os
import sys 




import requests
import urllib3
from bs4 import BeautifulSoup
from retrying import retry

from title2bib.crossref import get_bib_from_title
import bibtexparser

# log config
logging.basicConfig()
logger = logging.getLogger('Sci-Hub')
logger.setLevel(logging.DEBUG)

#
urllib3.disable_warnings()

# constants
HEADERS = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:27.0) Gecko/20100101 Firefox/27.0'}

class SciHub(object):
    """
    SciHub class can search for papers by  crossref
    and fetch/download papers from sci-hub.io
    """
    def __init__(self,title=None,doi=None, path=None):
        self.sess = requests.Session()
        self.sess.headers = HEADERS

        self.doi = doi
        self.title = title
        self.path = path
        self.flag = False

        self.available_base_url_list = self._get_available_scihub_urls()
        self.base_url = None
        try :
            
            self.base_url = self.available_base_url_list[0] + '/'
        except IndexError as e: 
            self.flag = False 
            raise IndexError ("get availbel_sci_url faile")
            # sys.exit()
            

        
        # self.identifier = identifier

    def _get_available_scihub_urls(self):
        '''
        Finds available scihub urls via https://sci-hub.now.sh/
        '''
        urls = []
        res = requests.get('https://sci-hub.now.sh/')
        s = self._get_soup(res.content)
        for a in s.find_all('a', href=True):
            if 'sci-hub.' in a['href']:
                urls.append(a['href'])
        return urls

    def set_proxy(self, proxy):
        '''
        set proxy for session
        :param proxy_dict:
        :return:
        '''
        if proxy:
            self.sess.proxies = {
                "http": proxy,
                "https": proxy, }

    def _change_base_url(self):
        if not self.available_base_url_list:
            raise Exception('Ran out of valid sci-hub urls')
        del self.available_base_url_list[0]
        self.base_url = self.available_base_url_list[0] + '/'
        logger.info("I'm changing to {}".format(self.available_base_url_list[0]))

    def search(self,get_first=False):
        """
        get doi from crossref 
        """
        new_paper = {}
        found, bib_string = get_bib_from_title(self.title,get_first =get_first)
        # print((bib_string))
        if found:
            try:
                if bibtexparser.loads(bib_string).entries:
                    bib = bibtexparser.loads(bib_string).entries[0]
                    # return bib
                    
                    new_paper['title'] = bib['title'] 
                    self.title = bib['title']
                    new_paper['doi'] = bib['doi']
                    self.doi = bib['doi'] 
                else :
                    self.doi = re.search(r'doi = {(.*?)}',bib_string,re.S).group(1)
                    # self.title = re.search(r'title = {(.*?)}',bib_string,re.S).group(1)

            except :
                raise IndexError("no doi find")


    # @retry(wait_random_min=100, wait_random_max=3000, stop_max_attempt_number=10)
    def download(self, destination='.'):
        """
        Downloads a paper from sci-hub given an indentifier (DOI, PMID, URL).
        Currently, this can potentially be blocked by a captcha if a certain
        limit has been reached.
        """
        data = self.fetch()

        if not 'err' in data:
            
            self._save(data['pdf'])
            print("{} download success".format(self.title))
            self.flag = True
        else:
            self.flag = False
            print(data['err'])

        # return data

    def fetch(self):
        """
        Fetches the paper by first retrieving the direct link to the pdf.
        If the indentifier is a DOI, PMID, or URL pay-wall, then use Sci-Hub
        to access and download paper. Otherwise, just download paper directly.
        """
        if not self.doi :
            self.search()
        if not self.title:
            self.title = self.doi

        try:
            url = self._search_direct_url()
            
            res = self.sess.get(url, verify=False)

            if res.headers['Content-Type'] != 'application/pdf':
                self._change_base_url()
                logger.info('Failed to fetch pdf with identifier %s '
                                           '(resolved url %s) due to captcha' % (identifier, url))
                raise CaptchaNeedException('Failed to fetch pdf with identifier %s '
                                           '(resolved url %s) due to captcha' % (identifier, url))
                # return {
                #     'err': 'Failed to fetch pdf with identifier %s (resolved url %s) due to captcha'
                #            % (identifier, url)
                # }
            else:
                return {
                    'pdf': res.content,
                    'url': url,
                    'name': self._generate_name(res)
                }

        except requests.exceptions.ConnectionError:
            logger.info('Cannot access {}, changing url'.format(self.available_base_url_list[0]))
            self._change_base_url()

        except requests.exceptions.RequestException as e:
            logger.info('Failed to fetch pdf with identifier %s (resolved url %s) due to request exception.'
                       % (self.doi, url))
            self.flag = False
            return {
                'err': 'Failed to fetch pdf with identifier %s (resolved url %s) due to request exception.'
                       % (self.doi, url)
            }


    def _search_direct_url(self):
        """
        Sci-Hub embeds papers in an iframe. This function finds the actual
        source url which looks something like https://moscow.sci-hub.io/.../....pdf.
        """
        # while True:
        if self.doi:
            if self.base_url:
                res = self.sess.get(self.base_url + self.doi, verify=False)
                s = self._get_soup(res.content)
                iframe = s.find('iframe')
                if iframe:
                    return iframe.get('src') if not iframe.get('src').startswith('//') \
                        else 'http:' + iframe.get('src')
        else:
            self.search()



    def _save(self,data):
        """
        Save a file give data ,default "current filepath + title + pdf".
        """
        file_name = re.sub('[\/:*?"<>| \n]','_',self.title,re.S)
        if self.path :
            file_name = os.join(self.path,file_name+'.pdf')
        else:
            file_name = os.path.join(".",file_name+'.pdf')
        with open(file_name, 'wb') as f:
            f.write(data)

    def _get_soup(self, html):
        """
        Return html soup.
        """
        return BeautifulSoup(html, 'html.parser')

    def _generate_name(self, res):
        """
        Generate unique filename for paper. Returns a name by calcuating 
        md5 hash of file contents, then appending the last 20 characters
        of the url which typically provides a good paper identifier.
        """
        name = res.url.split('/')[-1]
        name = re.sub('#view=(.+)', '', name)
        pdf_hash = hashlib.md5(res.content).hexdigest()
        return '%s-%s' % (pdf_hash, name[-20:])



if __name__ == '__main__':
    pass 