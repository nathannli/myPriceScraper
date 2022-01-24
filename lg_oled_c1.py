import csv
import re
from datetime import datetime
import os

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


def main():
    the_date = datetime.today().strftime('%Y-%m-%d')
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    clean_csv(the_date)
    amazon(the_date, driver)
    canadacomputers(the_date, driver)
    visions(the_date, driver)


def get_url(search_term, url_template, delimiter):
    search_term = search_term.replace(" ", delimiter)
    return url_template.format(search_term)


def visions(the_date, driver):
    url_template = "https://www.visions.ca/catalogue/category/ProductResults.aspx?categoryId=0&searchText={}"
    url = get_url('lg oled c1', url_template, "%20")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find('div', {'id': 'result-container-kg874'})
    results_list = results.find_all('div', {'class': 'prodlist-itembox'})

    records = []
    for item in results_list:
        record = extract_visions_record(the_date, item)
        if record:
            records.append(record)

    write_csv(records)


def extract_visions_record(the_date, item):
    description = item.find('div', {'class': 'prodlist-title'}).a.text
    if "c1" not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = ''
    else:
        inches = regex.group().strip().replace('"', "").replace("”", "")
    try:
        rating = item.find('div', {'class': 'pr-snippet-rating-decimal'}).text
    except AttributeError:
        rating = 0
    try:
        review_count_string = item.find('div', {'class': 'pr-category-snippet__total pr-category-snippet__item'}).text
        if review_count_string != "No Reviews":
            review_count = [int(s) for s in review_count_string.split() if s.isdigit()][0]
        else:
            review_count = 0
    except AttributeError:
        review_count = 0
    string_price = item.find('span', {'class': 'saleprice-432gh'}).text
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s

    return the_date, description, inches, float(price), float(rating), int(review_count), "visions.ca"


def canadacomputers(the_date, driver):
    url_template = "https://www.canadacomputers.com/search/results_details.php?language=en&keywords={}"
    url = get_url('lg oled c1', url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find('div', {'id': 'product-list'})
    results_list = results.find_all('div', {'class': 'col-xl-3'})

    records = []
    for item in results_list:
        record = extract_cc_record(the_date, item)
        if record:
            records.append(record)

    write_csv(records)


def extract_cc_record(the_date, item):
    description = item.find('span', {'class': 'productTemplate_title'}).a.text
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = ''
    else:
        inches = regex.group().strip().replace('"', "").replace("”", "")
    string_price = item.find('span', {'class': 'pq-hdr-product_price'}).strong.text
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s

    return the_date, description, inches, float(price), "n/a", 0, "canadacomputers"


def amazon(the_date, driver):
    url_template = "https://www.amazon.ca/s?k={}&ref=nb_sb_noss"
    url = get_url('lg oled c1 series', url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find_all('div', {'data-component-type': 's-search-result'})

    records = []
    for item in results:
        record = extract_amazon_record(the_date, item)
        if record:
            records.append(record)

    write_csv(records)


def extract_amazon_record(the_date, item):
    description = item.h2.a.text.strip()
    if "C1" not in description:
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = ''
    else:
        inches = regex.group().strip().replace('"', "").replace("”", "")
    try:
        string_price = item.find('span', 'a-price').find('span', 'a-offscreen').text
        price = ""
        for s in string_price:
            if s.isdigit() or s == ".":
                price += s
    except AttributeError:
        return None
    try:
        rating_text = item.i.text
        regex_rating = re.search(r"(.{1,3}) out of .{1,3} stars", rating_text)
        if regex_rating is None:
            rating = 0
        else:
            rating = regex_rating.group(1).strip()
    except AttributeError:
        rating = 0
    try:
        review_count = item.find('span', {'class': 'a-size-base'}).text
        if review_count.isdigit() is False:
            review_count = 0
    except AttributeError:
        review_count = 0

    return the_date, description, inches, float(price), float(rating), int(review_count), "amazon.ca"


def clean_csv(the_date):
    if os.path.exists('results.csv'):
        with open('results.csv', 'r', encoding="utf-8") as fin, open('results_temp.csv', 'w', newline='', encoding='utf-8') as fout:
            # define reader and writer objects
            reader = csv.reader(fin, skipinitialspace=True)
            writer = csv.writer(fout)

            # write headers
            writer.writerow(["Date", "Description", "Size", "Price", "Rating", "Rting Cnt", "Source"])

            # iterate and write rows based on condition
            for index, row in enumerate(reader):
                if index == 0:
                    continue
                if row[0] != the_date:
                    writer.writerow(row)

        os.remove('results.csv')
        os.rename('results_temp.csv', 'results.csv')


def write_csv(results):
    write_header = True
    if os.path.exists('results.csv'):
        write_header = False
    with open('results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Date", "Description", "Size", "Price", "Rating", "Rting Cnt", "Source"])
        writer.writerows(results)


if __name__ == '__main__':
    main()
