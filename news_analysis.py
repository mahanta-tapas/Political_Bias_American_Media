import pandas as pd
import socks
import socket
from bs4 import BeautifulSoup
import requests
from pandas import DataFrame
from newsapi import NewsApiClient
import re
import sqlite3
from itertools import cycle
import os

# Anonymous Scraping Using Tor
# Open 4 SOCKS ports, each providing a new Tor circuit.

'''
https://levelup.gitconnected.com/anonymous-web-scrapping-with-node-js-tor-apify-and-cheerio-3b36ec6a45dc
https://stackoverflow.com/questions/35133200/scraping-in-python-preventing-ip-ban
Open /etc/tor/torrc
SocksPort 9050
SocksPort 9052
SocksPort 9053
SocksPort 9054

Using gnews api 
https://github.com/nikhilkumarsingh/gnewsclient

Scraping google news with express vpn
https://github.com/philipperemy/google-news-scraper/blob/master/core.py

Original Google news API
https://stackoverflow.com/questions/7806200/what-to-use-now-google-news-api-is-deprecated
http://web.archive.org/web/20150204025359/http://blog.slashpoundbang.com/post/12975232033/google-news-search-parameters-the-missing-manual
'''

#https://github.com/mattlisiv/newsapi-python
proxies = ['http://125.27.251.206:50817', 'http://191.100.24.251:21776', 'http://186.0.176.147:8080', 'http://163.172.119.53:3838',
 'http://93.185.96.60:41003', 'http://110.44.133.135:3128', 'http://45.123.42.146:40852', 'http://132.255.92.34:53281', 'http://186.225.45.13:45974', 'http://3.14.120.193:3838']
proxy_pool = cycle(proxies)

finished_list = []

def write_to_files(news_df,path):
	try:
		os.mkdir(path)
		print ("Successfully created the directory %s " % path)
		for i in range(0,len(news_df)):
			file_name = path + '/'+'news_analyis_'+'content_' + str(i) 
			news_df.iloc[i,0:5].to_csv(file_name,header=False)
	except OSError:
		print ("Creation of the directory %s failed" % path)



def valid_url(url):
	if url in finished_list:
		print ("Duplicate url ",url)
		return False
	finished_list.append(url)
	if re.search('\.com\/(media|video)',url):
		print("not a valid url ",url)
		return False
	else:
		return True 

def get_content(url):
	if valid_url(url):
		print('Extracting content for the url ',str(url))
		#proxy = next(proxy_pool)

		#response = requests.get(url,proxies={"http": proxy, "https": proxy})
		response = requests.get(url)

		print("response status ",response.status_code)
		
		if response.status_code != 200:
			print('url fetching failed with http error ',response.status_code)
			html = ''
		else:
			html = response.content

		soup = BeautifulSoup(html, 'html.parser')


		div_tag = soup.find_all('div', class_='article-body')
		div_tag_2 = soup.find_all('div', class_='article-content')
		div_tag_3 = soup.find_all("p",class_="gnt_ar_b_p") #for USAToday

		if div_tag:
			return collect_content(div_tag)
		elif div_tag_2:
			return collect_content(div_tag_2)
		elif div_tag_3:
			return collect_content_2(div_tag_3)
	
		else:
			c_list = [v.text for v in soup.find_all('p') if len(v.text) > 0]
			words_to_bans = ['<', 'javascript']
			for word_to_ban in words_to_bans:
				c_list = list(filter(lambda x: word_to_ban not in x.lower(), c_list))
			c_list = [t for t in c_list if len(re.findall('[a-z]', t.lower())) / (len(t) + 1) < 0.8]
			content = ' '.join(c_list)
			content = content.replace('\n', ' ')
			content = re.sub('\s\s+', ' ', content)  # remove multiple spaces.
			#print("Test content ",str(content))
			return content
	


def collect_content(parent_tag):
    """Collects all text from children p tags of parent_tag"""
    content = ''
    for tag in parent_tag:
        p_tags = tag.find_all('p')
        for tag in p_tags:
            content += tag.text + '\n'
    return content 

def collect_content_2(parent_tag):
	# for USA Today
	content = ''
	for tag in parent_tag:
		content += tag.text + '\n'
	return content		


api = NewsApiClient(api_key='0fc2ffe7f6384c10a7833a2a8ce6d1f6')
conn = sqlite3.connect('news_articles_all_keywords.sqlite')

# result = api.get_top_headlines(q='George Flyod', sources='bbc-news')

#result = api.get_everything(q='voting by mail',language='en', from_param='2020-05-07',to='2020-06-07',page_size=100,sort_by='popularity')

#result = api.get_everything(q='voting by mail',language='en',page_size=100,domains='washingtonpost.com,foxnews.com')
#keywords = ['voting by mail','vote by mail','mail-in voting','defund','defund the police','abortion','statues','statue','CHOP','supreme court','mask','masks']
#keywords = ['abortion','statue','CHOP','supreme court']

keywords = ['bolton book','bolton\'s book']
sources = []
title = []
url = []
content = []

for keyword in keywords:
	result = api.get_everything(qintitle=keyword,language='en',page_size=90,domains='washingtonpost.com,foxnews.com,usatoday.com',from_param='2020-06-11')

	for art in result['articles']:
		sources.append(art['source']['id'])
		title.append(art['title'])
		url.append(art['url'])
		content.append(art['content'])
		#print('url :',url)
	news_dict = {'source_id':sources,'title':title,'url':url,'content':content}
	news_df = pd.DataFrame(news_dict)

	print(news_df[['url','title']])
	news_df['content_full'] = news_df.apply(lambda x: get_content(x.url),axis=1)
	db_name = "news_" + "bolton_book"
	news_df.to_sql(db_name, conn, if_exists='append', index=False)

	path = "/Users/tapas/Documents/Repos/news_articles_all_keywords/" + "bolton_book"

	if not os.path.exists(path):
		write_to_files(news_df,path)
	else:
		path = path + "_"
		write_to_files(news_df,path)




'''
for i, row in news_df.iterrows():
	file_name = '/Users/tapas/Documents/Repos/news_analyis_'+'content_' + str(i)
	row['content_full'].to_csv(file_name)
'''





