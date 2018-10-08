import re
import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from funda.items import FundaItem

class FundaSoldSpider(CrawlSpider):

    name = "funda_spider_sold"
    allowed_domains = ["funda.nl"]

    def __init__(self, place='amsterdam'):
        # self.start_urls = ["https://www.funda.nl/koop/verkocht/%s/p%s/" % (place, page_number) for page_number in range(1,1001)]

        self.start_urls = ["https://www.funda.nl/koop/verkocht/gemeente-%s/p%s/" % (place, page_number) for page_number in range(1,1001)]
        # self.start_urls = ["https://www.funda.nl/koop/verkocht/%s/p1/" % place]  # For testing, extract just from one page
        self.base_url = "https://www.funda.nl/koop/verkocht/%s/" % place
        # self.le1 = LinkExtractor(allow=r'%s+(huis|appartement)-\d{8}' % self.base_url)
        self.le1 = LinkExtractor(allow=r'https://www.funda.nl/koop/verkocht/(.*)/(huis|appartement)-\d{8}' )
        self.le2 = LinkExtractor(allow=r'%s+(huis|appartement)-\d{8}.*/kenmerken/' % self.base_url)

    def parse(self, response):
        # print('parse starft')
        links = self.le1.extract_links(response)
        slash_count = self.base_url.count('/')+1        # Controls the depth of the links to be scraped
        # print('link_lst=+',links,'+')
        for link in links:
            if link.url.count('/') == slash_count and link.url.endswith('/'):
                item = FundaItem()
                item['url'] = link.url
                if re.search(r'/appartement-',link.url):
                    item['property_type'] = "apartment"
                elif re.search(r'/huis-',link.url):
                    item['property_type'] = "house"
                yield scrapy.Request(link.url, callback=self.parse_dir_contents, meta={'item': item})

    def parse_dir_contents(self, response):
        new_item = response.request.meta['item']
        title = response.xpath('//title/text()').extract()[0]
        # postal_code = re.search(r'\d{4} [A-Z]{2}', title).group(0)

        postal_code = re.search(r'\d{4} ([A-Z]{2}|)', title).group(0) #能够适应无字母版本
        address = response.xpath('//h1/text()').extract()[0].strip()

        price_span = response.xpath("//dt[contains(.,'Laatste vraagprijs')]/following-sibling::dd[1]/text()").extract()[0]
        price = re.findall(r'(\d+.\d+.\d+|\d+.\d+)',price_span)[0].replace('.','')
        surface_span=response.xpath("//dt[contains(.,'Wonen') or contains(.,'Oppervlakte')]/following-sibling::dd[1]/text()").extract()[0]
        surface = re.findall(r'(\d+.\d+|\d+)',surface_span)[0].replace('.','')
        content_span = response.xpath(
            "//dt[contains(.,'Inhoud')]/following-sibling::dd[1]/text()").extract()[0]
        content = re.findall(r'(\d+.\d+|\d+)', content_span)[0].replace('.', '')


        posting_date = response.xpath("//dt[contains(.,'Aangeboden sinds')]/following-sibling::dd[1]/text()").extract()[0]
        sale_date = response.xpath("//dt[contains(.,'Verkoopdatum')]/following-sibling::dd[1]/text()").extract()[0]

        # print('extraction:postal_code=',postal_code,'\naddress=',address,'\nprice=',price,'\nposting_date=',posting_date,'\nsale_date=',sale_date)

        new_item['postal_code'] = postal_code
        new_item['address'] = address
        new_item['price'] = price
        new_item['posting_date'] = posting_date
        new_item['sale_date'] = sale_date
        new_item['surface'] = surface
        new_item['content'] = content

        # links = self.le1.extract_links(response)
        # slash_count = self.base_url.count('/') + 1
        #
        # # print('links and slash count =',slash_count,links)
        # proper_links = list(filter(lambda link: link.url.count('/')==slash_count and link.url.endswith('/'), links))
        # print('proper_links',proper_links[0].url)
        #
        # yield scrapy.Request(proper_links[0].url, callback=self.parse_details, meta={'item': new_item})


        year_built_td = response.xpath("//dt[contains(.,'Bouwjaar') or contains(.,'Bouwperiode')]/following-sibling::dd[1]/text()").extract()[0]
        year_built = re.findall(r'\d{4}', year_built_td)[0]
        rooms_td = response.xpath("//dt[contains(.,'Aantal kamers')]/following-sibling::dd[1]/text()").extract()[0]
        rooms = re.findall('\d+ kamer', rooms_td)[0].replace(' kamer', '')
        new_item['year_built'] = year_built
        # new_item['area'] = area
        new_item['rooms'] = rooms
        # new_item['bedrooms'] = bedrooms

        yield new_item


    # def parse_details(self, response):
    #     new_item = response.request.meta['item']
    #
    #     year_built_td = response.xpath("//th[contains(.,'Bouwjaar')]/following-sibling::td[1]/span/text()").extract()[0]
    #     year_built = re.findall(r'\d{4}',year_built_td)[0]
    #     # area_td = response.xpath("//th[contains(.,'woonoppervlakte')]/following-sibling::td[1]/span/text()").extract()[0]
    #     # area = re.findall(r'\d+',area_td)[0]
    #     rooms_td = response.xpath("//th[contains(.,'Aantal kamers')]/following-sibling::td[1]/span/text()").extract()[0]
    #     rooms = re.findall('\d+ kamer',rooms_td)[0].replace(' kamer','')
    #     # bedrooms = re.findall('\d+ slaapkamer',rooms_td)[0].replace(' slaapkamer','')
    #
    #     new_item['year_built'] = year_built
    #     # new_item['area'] = area
    #     new_item['rooms'] = rooms
    #     # new_item['bedrooms'] = bedrooms

        yield new_item
