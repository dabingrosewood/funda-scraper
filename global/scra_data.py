import os


f=open('../gemeenten.txt','r')
lines=f.readlines()
count=0
for line in lines:
    count+=1
    place=line.strip('\n').replace(' ','-').lower()
    print('now starting to catch data of city: ',count,place)

    com='scrapy crawl funda_spider -a place='+place+' -o data/'+ place+'_for_sale.csv'
    print('com=',com)
    os.system(com)

