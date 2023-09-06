import logging
import random
import urllib.request

from selenium.webdriver.chrome.service import Service
import requests
import json
from bs4 import BeautifulSoup
import time
from pprint import pprint
import os

from selenium.webdriver.common.by import By

from lib_ import agents
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeOptions
import undetected_chromedriver as uc
from requests.exceptions import RequestException

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
    while True:
        try:
            r = requests.get(link, headers=headers, timeout=(3.05, 27))
            if r.status_code == 200:
                return r
            else:
                print(f"Server returned status code {r.status_code}, retrying...")
                count += 1
        except RequestException as e:
            print(f"An error occurred: link {link}, \n {e} \n retrying...")
            count += 1

        if count > 10:
            print("Max retry attempts reached, exiting.")
            break


def get_all_brands():
    url_link = 'https://www.cardekho.com/newcars'
    r = check_status(url_link)
    print(f'func get_all_brands check {url_link}')
    soup = BeautifulSoup(r.content, 'html.parser')
    all_brands = [i.find('a') for i in soup.find("ul", class_="listing").find_all('li', class_='gsc_col-xs-4')]
    links = ['https://www.cardekho.com' + a.get_attribute_list('href')[0] for a in all_brands]
    return links

def get_image_path(url, val):
    persona = {
        'user-agent': person
    }
    options = webdriver.ChromeOptions()
    options.add_argument(f"user-agent={persona['user-agent']}")
    options.add_argument('--headless')
    driver_ = Service(executable_path='web_driver_for_selenium\\chromedriver.exe')
    driver = webdriver.Chrome(options=options, service=driver_)
    driver.get(url)
    time.sleep(1)
    search_id = driver.find_element(By.ID, 'brands')
    image_element = search_id.find_element(By.CLASS_NAME, 'tabTitle')
    div_element = image_element.find_element(By.XPATH, f"//div[@data-track-section='Current']")
    image_path = div_element.find_element(By.XPATH, f"//a[@title='{val} Cars' and @class='BrIconNewCar' and @href='/cars/{val}']")
    print(image_path.get_attribute("outerHTML"))

    img_src = image_path.get_attribute('data-lazy-src') or image_path.get_attribute('src')
    driver.close()
    return img_src


def save_all_brands():
    soup = get_url_html('https://www.cardekho.com/newcars')

    all_brands = [i.find('a') for i in soup.find("ul", class_="listing").find_all('li', class_='gsc_col-xs-4')]
    links = ['https://www.cardekho.com' + a.get_attribute_list('href')[0] for a in all_brands]
    pprint(links)

    brands = []

    if os.path.exists('brands.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'
    with open('brands.json', reading_mode, encoding='utf-8') as f:
        for a in all_brands:
            value = a.text
            link = 'https://www.cardekho.com/newcars#'
            try:
                # Get image path for brand
                image_url = get_image_path(link, value)
                brand = {
                    "_id": a.get_attribute_list('href')[0].rsplit('/', 1)[-1],
                    "slug": a.get_attribute_list('href')[0].rsplit('/', 1)[-1],
                    "brandName": a.find('img').get_attribute_list('alt')[0],
                    "type": "CAR",
                    "imageDtos": [
                        {
                            "hostUrl": "https://www.cardekho.com/newcars",
                            "imagePath": image_url,
                            "title": a.get_attribute_list('title')[0]
                        }
                    ],
                    "verified": False,
                    "dateCreated": int(time.time()),
                    "lastModified": int(time.time()),
                    "deleted": False
                }
                pprint(brand)
                brands.append(brand)
                f.write(json.dumps(brand) + '\n')

                print(brand['brandName'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping save_all_brands in err: %s", e)

    return brands


def save_all_models(brand_link, brand):
    try:
        r = requests.get(brand_link, headers=headers)
    except RequestException as e:
        print(f"An error occurred: link {brand_link}, \n {e} \n retrying...")
    finally:
        r = check_status(brand_link)
        print(f'Success connect link: {brand_link} \n')
    print(f'check func save_all_models status brand_link {brand_link}')

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
                try:
                    r = requests.get(model_link, headers=headers)
                except RequestException as e:
                    print(f"An error occurred: link {model_link}, \n {e} \n retrying...")
                finally:
                    r = check_status(model_link)
                    print(f'Success connect link: {model_link} \n')
                print(f'check func save_all_models status model_link {model_link}')

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
                try:
                    r = requests.get(specs_link, headers=headers)
                except RequestException as e:
                    print(f"An error occurred: link {specs_link}, \n {e} \n retrying...")
                finally:
                    r = check_status(specs_link)
                    print(f'Success connect link: {specs_link} \n')
                print(f'check func save_all_models status specs_link {specs_link}')

                model_specs_soup = BeautifulSoup(r.content, 'html.parser')

                specsData = [[i.find('td').text, i.text.replace(i.find('td').text, '')] for i in
                             model_specs_soup.find('table', class_='keyfeature').find_all('tr')]
                try:
                    mileage = [i[1] for i in specsData if 'Mileage' in i[0]][0]
                except IndexError:
                    print('Error: the specsData list is empty or contains no elements that match the condition')
                finally:
                    print('retrying...')
                    mileage = [i[1] for i in specsData if 'Mileage' in i[0]]
                    if mileage:
                        mileage = mileage[0]
                        print(f'Success: {mileage} ')
                    else:
                        mileage = None
                fuelType = [i[1] for i in specsData if 'Fuel' in i[0]][0]
                transmissionType = [i[1] for i in specsData if 'Transmission' in i[0]][0]
                engine = [i[1] for i in specsData if 'Engine' in i[0]][0]

                price_link = 'https://www.cardekho.com' + \
                             model_soup.find('ul', class_='modelNavUl').find_all('li')[1].find('a').get_attribute_list(
                                 'href')[0]
                try:
                    r = requests.get(price_link, headers=headers)
                    if r.status_code != 200:
                        r = check_status(price_link)
                except RequestException as e:
                    print(f"An error occurred: link {price_link}, \n {e} \n retrying...")
                finally:
                    r = check_status(price_link)
                    print(f'Success connect link: {price_link} \n')
                print(f'check func save_all_models status brand_link {price_link}')

                model_price_soup = BeautifulSoup(r.content, 'html.parser')

                ex_show_room_price = model_price_soup.find_all('td', class_='gsc_col-xs-4')[0].text.replace('Rs.', '')

                colour_link = 'https://www.cardekho.com' + \
                              [i for i in model_soup.find('ul', class_='modelNavUl').find_all('li') if
                               'Colour' in i.text][0].find('a').get_attribute_list('href')[0]

                model_colour_soup = get_url_html(colour_link)

                all_colours_images = [i.find('img') for i in
                                      model_colour_soup.find('div', class_='posR').find('ul').find_all('li')]
                try:
                    if model_colour_soup is not None:
                        all_colours_images = [i.find_all('img') for i in
                                              model_colour_soup.find('div', class_='posR').find('ul').find_all('li')]
                    else:
                        print("Failed parse all_colours_images model_color_soup is None.")
                except:
                    print('No images in find --div --class_--posS --ul --li')

                all_colours_divs = [i.find('a') for i in
                                    model_colour_soup.find('ul', class_='gscr_lSPager gscr_lSGallery').find_all('li')]
                all_hexcodes = [i.get_attribute_list('style')[0].split(':')[1] for i in
                                model_colour_soup.find_all('i', class_='coloredIcon')]
                all_colours = []

                for index, a in enumerate(all_colours_divs):
                    colour_link = a.get_attribute_list('href')[0]
                    try:
                        r = requests.get(colour_link, headers=headers)
                    except RequestException as e:
                        print(f"An error occurred: link {colour_link}, \n {e} \n retrying...")
                    finally:
                        r = check_status(colour_link)
                        print(f'Success connect link: {colour_link} \n')
                    print(f'check func save_all_models status colour_link {colour_link}')

                    model_colour_soup = BeautifulSoup(r.content, 'html.parser')

                    colour_name = model_colour_soup.find('span', class_='galleryName').text

                    colour = {
                        "title": a.get_attribute_list('title')[0],
                        "hexcode": all_hexcodes[index],
                        "imageDto": {
                            "hostUrl": "https://www.cardekho.com/newcars",
                            "imagePath": all_colours_images[index][0].get_attribute_list('src')[0],
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

                print(model['modelName'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping save_all_models in err: %s", e)
    return models


def get_all_models(brand_link):
    try:
        r = requests.get(brand_link, headers=headers)
        if r.status_code != 200:
            r = check_status(brand_link)
    except RequestException as e:
        print(f"An error occurred: link {brand_link}, \n {e} \n retrying...")
    finally:
        r = check_status(brand_link)
        print(f'Success connect link: {brand_link} \n')
    print(f'check func getl_all_models status brand_link {brand_link}')

    soup = BeautifulSoup(r.content, 'html.parser')

    all_models = [i for i in soup.find_all("li", class_='gsc_col-xs-12 gsc_col-sm-6 gsc_col-md-12 gsc_col-lg-12') if
                  i.get_attribute_list('id')[0]]

    model_links = ['https://www.cardekho.com' + img.find('a').get_attribute_list('href')[0] for img in all_models]

    return model_links


def save_all_variants(model_link, model, brand):
    try:
        r = requests.get(model_link, headers=headers)
        if r.status_code != 200:
            r = check_status(model_link)
    except RequestException as e:
        print(f"An error occurred: link {model_link}, \n {e} \n retrying...")
    finally:
        r = check_status(model_link)
        print(f'Success connect link: {brand_link} \n')
    print(f'check func getl_all_models status model_link {model_link}')

    model_soup = BeautifulSoup(r.content, 'html.parser')

    variants_links = ['https://www.cardekho.com' + i.find_all('td')[0].find('a').get_attribute_list('href')[0] for i in
                      model_soup.find('table', class_='allvariant contentHold').find('tbody').find_all('tr')]

    images_link = 'https://www.cardekho.com' + \
                  model_soup.find('ul', class_='modelNavUl').find_all('li')[3].find('a').get_attribute_list('href')[0]
    print(f'link images {images_link}')
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

                print(variant['_id'], 'was scraped...')
            except Exception as e:
                logger.exception(f"problem scraping save_all_variants in err: %s", e)

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
    try:
        r = requests.get(main_link, headers=headers)
    except RequestException as e:
        print(f"An error occurred: link {main_link}, \n {e} \n retrying...")
    finally:
        r = check_status(main_link)
        print(f'Success connect link: {main_link} \n')
    print(f'check func scrape_all_reviews status main_link {main_link}')

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
        try:
            r = requests.get(scraping_link, headers=headers)
        except RequestException as e:
            print(f"An error occurred: link {scraping_link}, \n {e} \n retrying...")
        finally:
            r = check_status(scraping_link)
            print(f'Success connect link: {scraping_link} \n')
        print(f'check func scrape_all_reviews status scraping_link {main_link}')

        soup = BeautifulSoup(r.content, 'html.parser')

    reviews = []

    if os.path.exists('reviews.json'):
        reading_mode = 'a+'
    else:
        reading_mode = 'w+'

    with open('reviews.json', reading_mode, encoding='utf-8') as f:
        for link in all_reviews_links:

            try:
                r = requests.get(link, headers=headers)
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
    # browser = uc.Chrome(options=options)
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
                print('scraping', models[index_m]['modelName'], 'reviews')
                try:
                    r = requests.get(model_link, headers=headers)
                except RequestException as e:
                    print(f"An error occurred: link {model_link}, \n {e} \n retrying...")
                finally:
                    r = check_status(model_link)
                    print(f'Success connect link: {model_link} \n')
                print(f'check out status model_link {model_link}')

                reviews_soup = BeautifulSoup(r.content, 'html.parser')
                model_reviews_page = 'https://www.cardekho.com' + \
                                     reviews_soup.find('ul', class_='modelNavUl').find_all('li')[5].find(
                                         'a').get_attribute_list('href')[0]

                scrape_all_reviews(model_reviews_page, model_link)

                print('reviews scraped')
            except Exception as e:
                logger.exception(f"problem scraping for index_m, model_link err: %s", e)

            try:
                # variants
                variants_links = save_all_variants(model_link, models[index_m], brands[index_b])
            except Exception as e:
                logger.exception(f"problem scraping problem scraping for index_m, model_link err: %s", e)
    except Exception as e:
        logger.exception(f"problem scraping as index_b, brand_link err: %s", e)
