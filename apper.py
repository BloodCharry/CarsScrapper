import random
import logging
import requests
import json
from bs4 import BeautifulSoup
import time
from pprint import pprint
import os
from lib_ import agents
from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
import undetected_chromedriver as uc

users = agents.USER_AGENTS_LIST
person = random.choice(users)
headers = {
    'accept': '*/*',
    'user-agent': person
}

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s]: %(message)s',
    handlers=[logging.FileHandler('C:\\Project\\cars\\scraperErr.log'), logging.StreamHandler()]
)


def check_status(link):
    count = 0
    r = requests.get(link, headers=headers, timeout=(3.05, 27))
    if r.status_code != 200:
        while r.status_code != 200:
            count += 1
            print(f'Reconnection.....{count}')
            r = requests.get(link, headers=headers, timeout=(3.05, 27))
            if r.status_code == 200:
                print('Successful connection!')
    return r


def get_all_brands():
    r = requests.get('https://www.cardekho.com/newcars', headers=headers, timeout=(3.05, 27))
    r = check_status('https://www.cardekho.com/newcars')
    print(f'check status get_all_brabds {r.status_code}')
    soup = BeautifulSoup(r.content, 'html.parser')


    all_brands = [i.find('a') for i in soup.find("ul", class_="listing").find_all('li', class_='gsc_col-xs-4')]
    links = ['https://www.cardekho.com' + a.get_attribute_list('href')[0] for a in all_brands]

    return links


def save_all_brands():
    soup = get_url_html('https://www.cardekho.com/newcars')

    all_brands = [i.find('a') for i in soup.find("ul", class_="listing").find_all('li', class_='gsc_col-xs-4')]
    links = ['https://www.cardekho.com' + a.get_attribute_list('href')[0] for a in all_brands]

    brands = []

    if os.path.exists('brands.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'

    with open('brands.json', reading_mode, encoding='utf-8') as f:
        for a in all_brands:

            try:
                brand = {
                    "_id": a.get_attribute_list('href')[0].rsplit('/', 1)[-1],
                    "slug": a.get_attribute_list('href')[0].rsplit('/', 1)[-1],
                    "brandName": a.find('img').get_attribute_list('alt')[0],
                    "type": "CAR",
                    "imageDtos": [
                        {
                            "hostUrl": "https://www.cardekho.com/newcars",
                            "imagePath": a.find('img').get_attribute_list('src')[0],
                            "title": a.get_attribute_list('title')[0]
                        }
                    ],
                    "verified": False,
                    "dateCreated": int(time.time()),
                    "lastModified": int(time.time()),
                    "deleted": False
                }

                brands.append(brand)
                pprint(brand)
                f.write(json.dumps(brand) + '\n')

                # print(brand['brandName'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping save_all_brands in err: %s", e)

    return brands


def save_all_models(brand_link, brand):
    print(f'scrap link - {brand_link}')
    r = check_status(brand_link)
    print(f'brand_link status {r.status_code}')

    soup = BeautifulSoup(r.content, 'html.parser')

    all_models = [[i.get_attribute_list('id')[0], i] for i in
                  soup.find_all("li", class_='gsc_col-xs-12 gsc_col-sm-6 gsc_col-md-12 gsc_col-lg-12') if
                  i.get_attribute_list('id')[0]]

    models = []

    if os.path.exists('models.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'

    with open('models.json', reading_mode, encoding='utf-8') as f:
        for id, img in all_models:
            try:
                model_link = 'https://www.cardekho.com' + img.find('a').get_attribute_list('href')[0]
                r = check_status(model_link)

                model_soup = BeautifulSoup(r.content, 'html.parser')

                ratings = model_soup.find('div', class_='startRating')

                stars = ratings.find_all('span')[0].find_all('span')

                all_stars = [i.get_attribute_list('class') for i in stars]
                stars_rating = sum([1 if 'icon-star-full-fill' in stars else 0 for stars in all_stars]) + sum(
                    [0.5 if 'icon-star-half-empty' in stars else 0 for stars in all_stars])

                review_count = int(ratings.find('span', class_='reviews').text.split()[0])

                price = model_soup.find('div', class_='price')

                minPrice, _, maxPrice = price.text.replace('Rs.', '').split()[:3]
                minPrice = minPrice.replace('.', ',')
                maxPrice = maxPrice.replace('.', ',')
                priceRange = minPrice + ' - ' + maxPrice

                labels = [i.text for i in model_soup.findAll('td', class_='gsc_col-xs-12')]

                keySpecs = [{'label': labels[index * 2], 'value': labels[index * 2 + 1]} for index in
                            range(len(labels) // 2)]

                specs_link = 'https://www.cardekho.com' + \
                             model_soup.find('div', class_='BottomLinkViewAll').find('a').get_attribute_list('href')[0]

                r = check_status(specs_link)
                print(f'specs_link status {r.status_code}')

                model_specs_soup = BeautifulSoup(r.content, 'html.parser')

                specsData = [[i.find('td').text, i.text.replace(i.find('td').text, '')] for i in
                             model_specs_soup.find('table', class_='keyfeature').find_all('tr')]

                mileage = [i[1] for i in specsData if 'Mileage' in i[0]][0]
                fuelType = [i[1] for i in specsData if 'Fuel' in i[0]][0]
                transmissionType = [i[1] for i in specsData if 'Transmission' in i[0]][0]
                engine = [i[1] for i in specsData if 'Engine' in i[0]][0]

                price_link = 'https://www.cardekho.com' + \
                             model_soup.find('ul', class_='modelNavUl').find_all('li')[1].find('a').get_attribute_list(
                                 'href')[0]

                r = check_status(price_link)
                print('price_link status =', r.status_code)

                model_price_soup = BeautifulSoup(r.content, 'html.parser')

                ex_show_room_price = model_price_soup.find_all('td', class_='gsc_col-xs-4')[0].text.replace('Rs.', '')

                colour_link = 'https://www.cardekho.com' + \
                              [i for i in model_soup.find('ul', class_='modelNavUl').find_all('li') if
                               'Colour' in i.text][0].find('a').get_attribute_list('href')[0]

                model_colour_soup = get_url_html(colour_link)

                all_colours_images = [i.find('img') for i in
                                      model_colour_soup.find('div', class_='posR').find('ul').find_all('li')]
                all_colours_divs = [i.find('a') for i in
                                    model_colour_soup.find('ul', class_='gscr_lSPager gscr_lSGallery').find_all('li')]
                all_hexcodes = [i.get_attribute_list('style')[0].split(':')[1] for i in
                                model_colour_soup.find_all('i', class_='coloredIcon')]
                all_colours = []

                for index, a in enumerate(all_colours_divs):
                    colour_link = a.get_attribute_list('href')[0]

                    r = check_status(all_colours_divs)
                    print('colour_link status = ', r.status_code)

                    model_colour_soup = BeautifulSoup(r.content, 'html.parser')

                    colour_name = model_colour_soup.find('span', class_='galleryName').text

                    colour = {
                        "title": a.get_attribute_list('title')[0],
                        "hexcode": all_hexcodes[index],
                        "imageDto": {
                            "hostUrl": "https://www.cardekho.com/newcars",
                            "imagePath": all_colours_images[index].get_attribute_list('src')[0],
                            "title": a.get_attribute_list('title')[0]
                        },
                        "parentColor": a.get_attribute_list('title')[0]
                    }

                    all_colours.append(colour)

                variants_links = [
                    'https://www.cardekho.com' + i.find_all('td')[0].find('a').get_attribute_list('href')[0] for i in
                    model_soup.find('table', class_='allvariant contentHold').find('tbody').find_all('tr')]

                model = {
                    "_id": id,
                    "slug": img.find('a').get_attribute_list('href')[0].rsplit('/', 1)[-1],
                    "modelName": img.find('img').get_attribute_list('alt')[0],
                    "type": "CAR",
                    "verified": False,
                    "brandId": brand['_id'],
                    "brandSlug": brand['slug'],
                    "brandName": brand['imageDtos'][0]['title'],
                    "avgRating": stars_rating,
                    "reviewCount": review_count,

                    "minPrice": minPrice,
                    "maxPrice": maxPrice,
                    "minPriceAbsolute": minPrice,
                    "maxPriceAbsolute": maxPrice,
                    "priceRange": priceRange,

                    "mileage": mileage,
                    "fuelType": fuelType,
                    "transmissionType": transmissionType,
                    "modelImage": brand['imageDtos'][0],
                    "safetyScore": 0,
                    "vehicleType": "CAR",
                    "engine": engine,
                    "exShowRoomPrice": ex_show_room_price,
                    "noOfVariants": len(variants_links),
                    "keySpecs": keySpecs,
                    "colorGalleries": all_colours,
                    "exteriorImages": [],
                    "deleted": False,
                }

                models.append(model)
                f.write(json.dumps(model) + '\n')

                # print(model['modelName'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping in save_all_models err: %s", e)

    return models


def get_all_models(brand_link):
    print(f'scrap link - {brand_link}')

    r = check_status(brand_link)
    print(f'check status get_all_models {brand_link}')

    soup = BeautifulSoup(r.content, 'html.parser')

    all_models = [i for i in soup.find_all("li", class_='gsc_col-xs-12 gsc_col-sm-6 gsc_col-md-12 gsc_col-lg-12') if
                  i.get_attribute_list('id')[0]]

    model_links = ['https://www.cardekho.com' + img.find('a').get_attribute_list('href')[0] for img in all_models]

    return model_links


def save_all_variants(model_link, model, brand):

    r = check_status(model_link)
    print(f'check save_all_variants status model_link {model_link}')

    model_soup = BeautifulSoup(r.content, 'html.parser')

    variants_links = ['https://www.cardekho.com' + i.find_all('td')[0].find('a').get_attribute_list('href')[0] for i in
                      model_soup.find('table', class_='allvariant contentHold').find('tbody').find_all('tr')]

    images_link = 'https://www.cardekho.com' + \
                  model_soup.find('ul', class_='modelNavUl').find_all('li')[3].find('a').get_attribute_list('href')[0]

    exteriorImages_soup = get_url_html(images_link)

    div = exteriorImages_soup.find('div', {'data-track-section': "Exterior"}).find('div', {'data-pager': "Exterior"})

    exteriorImages = []

    for img in div.find_all('img'):
        exteriorImages.append(
            {
                "hostUrl": "https://www.cardekho.com",
                "imagePath": img.get_attribute_list('src')[0],
                "title": img.get_attribute_list('title')[0]
            })

    variants = []

    if os.path.exists('variants.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'

    with open('variants.json', reading_mode, encoding='utf-8') as f:

        for link in variants_links:

            try:
                variant_soup = get_url_html(link)

                ratings = variant_soup.find('div', class_='startRating')

                stars = ratings.find_all('span')[0].find_all('span')

                all_stars = [i.get_attribute_list('class') for i in stars]
                stars_rating = sum([1 if 'icon-star-full-fill' in stars else 0 for stars in all_stars]) + sum(
                    [0.5 if 'icon-star-half-empty' in stars else 0 for stars in all_stars])

                review_count = int(ratings.find('span', class_='reviews').text.split()[0])

                specsData = [[i.find('td').text, i.text.replace(i.find('td').text, '')] for i in
                             variant_soup.find('table', class_='keyfeature').find_all('tr')]

                try:
                    mileage = [i[1] for i in specsData if 'Mileage' in i[0]][0]
                except:
                    mileage = ''
                try:
                    fuelType = [i[1] for i in specsData if 'Fuel' in i[0]][0]
                except:
                    fuelType = ''
                try:
                    transmissionType = [i[1] for i in specsData if 'Transmission' in i[0]][0]
                except:
                    transmissionType = ''
                try:
                    engine = [i[1] for i in specsData if 'Engine' in i[0]][0]
                except:
                    engine = ''

                labels = [i.text for i in model_soup.findAll('td', class_='gsc_col-xs-12')]

                keySpecs = [{'label': labels[index * 2], 'value': labels[index * 2 + 1]} for index in
                            range(len(labels) // 2)]

                fetures_div = variant_soup.find('div', {'id': 'scrollDiv'})

                titles = [i.text for i in fetures_div.find_all('h3')]

                tables = [i for i in fetures_div.find_all('table')]

                all_tables = []

                for table in tables:
                    labels_spans = [i for i in table.find_all('tr')]

                    labels = []

                    for i in labels_spans:
                        tds = i.find_all('td')
                        if len(tds) != 2:
                            continue
                        tds[0] = tds[0].text
                        if tds[1].find('i'):
                            if 'icon-check' == tds[1].find('i').get_attribute_list('class')[0]:
                                tds[1] = 'Yes'
                            else:
                                tds[1] = 'No'
                        else:
                            tds[1] = tds[1].text

                        labels.append(tds)

                    all_tables.append(labels)

                detailed_specs = []

                for index, title in enumerate(titles):
                    labels = all_tables[index]

                    keySpecs = [{'label': labels[index][0], 'value': labels[index][1]} for index in range(len(labels))]

                    spec = {
                        'title': title,
                        'specItems': keySpecs
                    }

                    detailed_specs.append(spec)

                ex_show_room_price = variant_soup.find_all('td', class_='gsc_col-xs-4')[0].text.replace('Rs.', '')
                on_road_price = variant_soup.find_all('td', class_='gsc_col-xs-4')[-1].text.replace('Rs.', '')[:-1]

                price = variant_soup.find('div', class_='price')

                price = price.text.replace('Rs.', '').split()[0].replace('.', ',') + ',000'

                variant = {
                    "_id": link.rsplit('/', 1)[1].replace('.htm', ''),
                    "slug": link.rsplit('/', 1)[1].replace('.htm', ''),
                    "modelId": model['_id'],
                    "modelSlug": model['slug'],
                    "brandId": brand['_id'],
                    "brandSlug": brand['slug'],
                    "verified": False,
                    "type": "CAR",
                    "name": variant_soup.find('h1', class_='tooltip').text,
                    "brandName": brand['brandName'],
                    "modelName": model['modelName'],

                    "exShowRoomPrice": ex_show_room_price,
                    "onRoadPrice": on_road_price,
                    "shortDesc": "",
                    "priceRange": ' - '.join([ex_show_room_price, on_road_price]),

                    "rating": stars_rating,
                    "reviewCount": review_count,

                    "modelPriceRange": model['priceRange'],

                    "fuelType": fuelType,
                    "variantImage": {
                        "hostUrl": "https://www.cardekho.com",
                        "imagePath":
                            variant_soup.find('div', class_='LazyLoadUpperDiv').find('img').get_attribute_list('src')[
                                0],
                        "title": variant_soup.find('h1', class_='tooltip').text
                    },
                    "mileage": mileage,
                    "transmissionType": transmissionType,
                    "keySpecs": keySpecs,
                    "detailSpecifications": detailed_specs,
                    "exteriorImages": exteriorImages,
                    "price": price,
                    "bodyType": "cars",
                    "colorGalleries": model['colorGalleries'],
                    "deleted": False
                }

                variants.append(variant)
                f.write(json.dumps(variant) + '\n')

                # print(variant['_id'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping in save_all_variants {link} err: %s", e)

    return variants_links


def scrape_review(review, link, model_link):
    ratings = review.find('div', class_='starRating')

    stars = ratings.find_all('span')[0].find_all('span')

    all_stars = [i.get_attribute_list('class') for i in stars]
    stars_rating = sum([1 if 'icon-star-full-fill' in stars else 0 for stars in all_stars]) + sum(
        [0.5 if 'icon-star-half-empty' in stars else 0 for stars in all_stars])

    title = review.find('h3').text
    content = review.find('p', class_='contentheight').text
    author = review.find('div', class_='name').text
    date = review.find('div', class_='date').text

    review = {
        'modelSlug': model_link.rsplit('/', 1)[1],
        'rating': stars_rating,
        'title': title,
        'content': content,
        'author': author,
        'date': date
    }

    return review


def scrape_all_reviews(main_link, model_link):

    r = check_status(main_link)
    print(f'check scrap_all_reviews status main_link {main_link}')

    soup = BeautifulSoup(r.content, 'html.parser')

    try:
        maxPage = int(soup.find('div', class_='pagination').find_all('p')[-1].text.split()[3])
    except:
        maxPage = 1

    all_reviews_links = []
    scraping_link = main_link

    for index in range(2, maxPage + 2):

        for i in [i.find('div', class_='contentspace') for i in soup.find('ul', class_='reviewList').find_all('li')]:
            try:
                link = 'https://www.cardekho.com' + i.find('a').get_attribute_list('href')[0]
                all_reviews_links.append(link)
            except:
                pass

        scraping_link = main_link + '/' + str(index)
        r = check_status(scraping_link)
        print(f'check status get_all_models {scraping_link}')

        soup = BeautifulSoup(r.content, 'html.parser')

    reviews = []

    if os.path.exists('reviews.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'

    with open('reviews.json', reading_mode, encoding='utf-8') as f:
        for link in all_reviews_links:

            try:

                r = check_status(link)
                print(f'check status get_all_models {link}')

                soup = BeautifulSoup(r.content, 'html.parser')

                review_block = soup.find('section', class_='clearfix userDetail shadow24 marginBottom20')

                review = scrape_review(review_block, main_link, model_link)

                reviews.append(review)
                f.write(json.dumps(review) + '\n')
            except:
                pass


def get_url_html(url):
    persona = {
        'user-agent': person
    }
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={persona['user-agent']}")
    options.add_argument('--headless')
    driver_ = Service(executable_path='web_driver_for_selenium\\chromedriver.exe')
    browser = webdriver.Chrome(options=options, service=driver_)
    # browser = uc.Chrome()
    browser.get(url)
    time.sleep(5)
    html = browser.page_source
    soup = BeautifulSoup(html, 'html.parser')
    browser.close()

    return soup


with open('brands.json', 'w+') as f:
    f.write("")
with open('models.json', 'w+') as f:
    f.write("")
with open('variants.json', 'w+') as f:
    f.write("")
with open('reviews.json', 'w+') as f:
    f.write("")

# brands
brands = save_all_brands()
brand_links = get_all_brands()

# models
for index_b, brand_link in enumerate(brand_links):
    try:
        models = save_all_models(brand_link, brands[index_b])
        model_links = get_all_models(brand_link)

        # variants and reviews
        for index_m, model_link in enumerate(model_links):
            # reviews
            try:
                # print('scraping', models[index_m]['modelName'], 'reviews')
                r = check_status(model_link)
                print(f'status output {r}')

                reviews_soup = BeautifulSoup(r.content, 'html.parser')
                model_reviews_page = 'https://www.cardekho.com' + \
                                     reviews_soup.find('ul', class_='modelNavUl').find_all('li')[5].find(
                                         'a').get_attribute_list('href')[0]

                scrape_all_reviews(model_reviews_page, model_link)

                # print('reviews scraped')
            except Exception as e:
                logger.exception(f"problem scraping for index_m, model_link err: %s", e)

            try:
                # variants
                variants_links = save_all_variants(model_link, models[index_m], brands[index_b])
            except Exception as e:
                logger.exception(f"problem scraping problem scraping for index_m, model_link err: %s", e)
    except Exception as e:
        logger.exception(f"problem scraping as index_b, brand_link err: %s", e)
