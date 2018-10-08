import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from funda.items import FundaItem

class FundaSpider(CrawlSpider):

    name = "funda_spider"
    allowed_domains = ["funda.nl"]

    def __init__(self, place='heel-nederland'):
        self.start_urls = ["https://www.funda.nl/koop/%s/p%s/" % (place, page_number) for page_number in range(1,301)]
        self.base_url = "https://www.funda.nl/koop/%s/" % place
        self.le1 = LinkExtractor(allow=r'%s+(huis|appartement)-\d{8}' % self.base_url)

    def parse(self, response):
        links = self.le1.extract_links(response)
        print(links)
        for link in links:
            if link.url.count('/') == 6 and link.url.endswith('/'):
                item = FundaItem()
                item['url'] = link.url
                if re.search(r'/appartement-',link.url):
                    item['property_type'] = "apartment"
                elif re.search(r'/huis-',link.url):
                    item['property_type'] = "house"
                yield scrapy.Request(link.url, callback=self.parse_dir_contents, meta={'item': item})

    def parse_dir_contents(self, response):
        new_item = response.request.meta['item']
        title = response.xpath('//title/text()').extract()[0]   #从title中获取信息
        postal_code = re.search(r'\d{4} [A-Z]{2}', title).group(0) #正则获取邮编 !!存在错误信息 如只有四位数字
        city = '-'.join(re.search(r'\d{4} [A-Z]{2} [\w,\s]+',title).group(0).split()[2:]) #处理城市名称存在多个单词的情况使用-相连
        address = re.findall(r'te koop: (.*) \d{4}',title)[0]
        price_dd = response.xpath("//dt[contains(.,'Vraagprijs')]/following-sibling::dd[1]/text()").extract()[0]
        price = re.findall(r' \d+.\d+', price_dd)[0].strip().replace('.','')
        year_built_dd = response.xpath("//dt[contains(.,'Bouwjaar') or contains(.,'Bouwperiode')]/following-sibling::dd[1]/text()").extract()[0] #有些是construction year
        year_built = re.findall(r'\d+', year_built_dd)[0]
        # area_dd = response.xpath("//dt[contains(.,'Woonoppervlakte')]/following-sibling::dd[1]/text()").extract()[0]
        # area = re.findall(r'\d+', area_dd)[0]
        rooms_dd = response.xpath("//dt[contains(.,'Aantal kamers')]/following-sibling::dd[1]/text()").extract()[0]
        rooms = re.findall('\d+ kamer',rooms_dd)[0].replace(' kamer','')
        # bedrooms = re.findall('\d+ slaapkamer',rooms_dd)[0].replace(' slaapkamer','') #有部分房子没有标注卧室

        new_item['postal_code'] = postal_code
        new_item['address'] = address
        new_item['price'] = price
        new_item['year_built'] = year_built
        # new_item['area'] = area
        new_item['rooms'] = rooms
        # new_item['bedrooms'] = bedrooms
        new_item['city'] = city
        yield new_item
