#! /usr/bin/env python3

import csv
import logging
import os
import re
from datetime import datetime
from time import sleep
from typing import Optional

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.edge.service import Service
from webdriver_manager.microsoft import EdgeChromiumDriverManager


def main():
    the_date = datetime.today().strftime('%Y-%m-%d')
    s = Service(EdgeChromiumDriverManager().install())
    driver = webdriver.Edge(service=s)
    pricescrape("lg oled c1", driver, the_date, "c1")
    # sleep(3)
    # pricescrape("samsung odyssey neo g9", driver, the_date, "neo g9")


def pricescrape(search_term: str, driver: webdriver, the_date: str, required_term: str) -> None:
    clean_csv(search_term, the_date)
    amazon(search_term.lower(), the_date, driver, required_term.lower())
    canadacomputers(search_term.lower(), the_date, driver, required_term.lower())
    visions(search_term.lower(), the_date, driver, required_term.lower())
    bestbuy(search_term.lower(), the_date, driver, required_term.lower())
    memory_express(search_term.lower(), the_date, driver, required_term.lower())
    newegg(search_term.lower(), the_date, driver, required_term.lower())


def get_url(search_term: str, url_template: str, delimiter: str) -> str:
    search_term = search_term.replace(" ", delimiter)
    return url_template.format(search_term)


def newegg(search_term: str, the_date: str, driver: webdriver, required_term: str) -> None:
    url_template = "https://www.newegg.ca/p/pl?d={}"
    url = get_url(search_term, url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    delay = 5  # seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'price-current')))
        logging.debug("page is ready")
    except TimeoutException:
        logging.error("newegg loading page took too long")
        logging.error("skipping..")
        return

    results = soup.find('div', {'class': 'item-cells-wrap border-cells items-grid-view four-cells expulsion-one-cell'})
    results_list = results.find_all('div', {'class': 'item-cell'})

    records = []
    for item in results_list:
        record = extract_newegg_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_newegg_record(the_date: str, item: str, required_term: str) -> Optional[
    tuple[str, str, int, float, float, int, str]]:
    description = item.find('a', {'class': 'item-title'}).text.strip()
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\"\s", description)
    if regex is None:
        regex = re.search(r"\s(\d\d)\sinch\s", description)
        if regex is None:
            inches = 0
        else:
            inches = regex.group(1)
    try:
        rating_tag = str(item.find('a', {'class': 'item-rating'}).i).strip()
        regex_rating = re.search(r"\saria-label=\"rated\s(.*)\sout\sof\s5\"\s", rating_tag)
        rating = regex_rating.group(1).strip()
    except AttributeError:
        rating = 0
    try:
        review_count_tag = item.find('span', {'class': 'item-rating-num'}).text.strip()
        regex_review_count = re.search(r"\((.*)\)", review_count_tag)
        review_count = regex_review_count.group(1).strip()
    except AttributeError:
        review_count = 0
    string_price = ""
    try:
        string_price = item.find('li', {'class': 'price-current'}).strong.text.strip()
    except AttributeError:
        print(f"newegg price error: {description}")
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s
    if price != "":
        price = float(price)

    return the_date, description, int(inches), price, float(rating), int(review_count), "newegg.ca"


def memory_express(search_term: str, the_date: str, driver: webdriver, required_term: str) -> None:
    url_template = "https://www.memoryexpress.com/Search/Products?Search={}"
    url = get_url(search_term, url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    delay = 5  # seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'c-cact-product-list')))
        logging.debug("page is ready")
    except TimeoutException:
        logging.error("memory express loading page took too long")
        logging.error("skipping..")
        return

    results = soup.find('div', {'data-role': 'product-list-container'})
    results_list = results.find_all('div', {'class': 'c-shca-icon-item'})


    records = []
    for item in results_list:
        record = extract_me_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_me_record(the_date: str, item: str, required_term: str) -> Optional[
    tuple[str, str, int, float, float, int, str]]:
    description = item.find('div', {'class': 'c-shca-icon-item__body-name'}).a.text.strip()
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)in\s", description)
    if regex is None:
        inches = 0
    else:
        inches = regex.group(1)
    rating = 0
    review_count = 0
    string_price = item.find('div', {'class': 'c-shca-icon-item__summary-prices'}).find('div', {
        'class': 'c-shca-icon-item__summary-list'}).span.text.strip()
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s

    return the_date, description, int(inches), float(price), float(rating), int(review_count), "memoryexpress"


def bestbuy(search_term: str, the_date: str, driver: webdriver, required_term: str) -> None:
    url_template = "https://www.bestbuy.ca/en-ca/search?search={}"
    url = get_url(search_term, url_template, "+")
    driver.get(url)
    soup = BeautifulSoup(driver.page_source, "html.parser")
    delay = 5  # seconds
    try:
        WebDriverWait(driver, delay).until(EC.presence_of_element_located((By.CLASS_NAME, 'productsContainer_2xEUC')))
        logging.debug("page is ready")
    except TimeoutException:
        logging.error("bestbuy loading page took too long")
        logging.error("skipping..")
        return
    results = soup.find('div', {'class': 'productsContainer_2xEUC'})
    results_list = results.find_all('div', {'class': 'x-productListItem'})
    records = []
    for item in results_list:
        record = extract_bestbuy_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_bestbuy_record(the_date: str, item: str, required_term: str) -> Optional[tuple[str, str, int, float, float, int, str]]:
    description = item.find('div', {'class': 'productItemName_3IZ3c'}).text
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = 0
    else:
        inches = regex.group().strip().replace('"', "").replace("”", "")
    try:
        rating_tag = str(item.find('meta', {'itemprop': 'ratingValue'}))
        regex_rating = re.search(r"\scontent=\"(.*)\"\s", rating_tag)
        rating = regex_rating.group(1).strip()
    except AttributeError:
        rating = 0
    try:
        review_count_tag = str(item.find('meta', {'itemprop': 'reviewCount'}))
        regex_review_count = re.search(r"\scontent=\"(.*)\"\s", review_count_tag)
        review_count = regex_review_count.group(1).strip()
    except AttributeError:
        review_count = 0
    # string_price = item.find('div', {'class': 'price_FHDfG medium_za6t1 salePrice_kTFZ3'}).text
    string_price = ""
    try:
        string_price = item.find('span', {'data-automation': 'product-price'}).find('span', {'class': 'screenReaderOnly_3anTj'}).text
    except AttributeError:
        print(f"bestbuy price error: {description}")
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s
    if price != "":
        price = float(price)

    return the_date, description, int(inches), price, float(rating), int(review_count), "bestbuy.ca"


def visions(search_term: str, the_date: str, driver: webdriver, required_term: str) -> None:
    url_template = "https://www.visions.ca/catalogue/category/ProductResults.aspx?categoryId=0&searchText={}"
    url = get_url(search_term, url_template, "%20")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find('div', {'id': 'result-container-kg874'})
    results_list = results.find_all('div', {'class': 'prodlist-itembox'})

    records = []
    for item in results_list:
        record = extract_visions_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_visions_record(the_date: str, item: str, required_term: str) -> Optional[
    tuple[str, str, int, float, float, int, str]]:
    description = item.find('div', {'class': 'prodlist-title'}).a.text
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = 0
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
    string_price = item.find('div', {'class': 'ht389-saleprice'}).text
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s

    return the_date, description, int(inches), float(price), float(rating), int(review_count), "visions.ca"


def canadacomputers(search_term: str, the_date: str, driver: webdriver, required_term: str) -> None:
    url_template = "https://www.canadacomputers.com/search/results_details.php?language=en&keywords={}"
    url = get_url(search_term, url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find('div', {'id': 'product-list'})
    results_list = results.find_all('div', {'class': 'col-xl-3'})

    records = []
    for item in results_list:
        record = extract_cc_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_cc_record(the_date: str, item: str, required_term: str) -> Optional[
    tuple[str, str, int, float, float, int, str]]:
    description = item.find('span', {'class': 'productTemplate_title'}).a.text
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        inches = 0
    else:
        inches = regex.group().strip().replace('"', "").replace("”", "")
    string_price = item.find('span', {'class': 'pq-hdr-product_price'}).strong.text
    price = ""
    for s in string_price:
        if s.isdigit() or s == ".":
            price += s

    return the_date, description, int(inches), float(price), 0, 0, "canadacomputers"


def amazon(search_term: str, the_date: str, driver: webdriver, required_term: str):
    url_template = "https://www.amazon.ca/s?k={}&ref=nb_sb_noss"
    url = get_url(search_term, url_template, "+")
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find_all('div', {'data-component-type': 's-search-result'})

    records = []
    for item in results:
        record = extract_amazon_record(the_date, item, required_term)
        if record:
            records.append(record)

    write_csv(search_term, records)


def extract_amazon_record(the_date: str, item: str, required_term: str) -> Optional[
    tuple[str, str, int, float, float, int, str]]:
    description = item.h2.a.text.strip()
    if required_term not in description.lower():
        return None
    regex = re.search(r"\s(\d\d)\D\s", description)
    if regex is None:
        regex = re.search(r"\s(\d\d)-Inch.*", description)
        if regex is None:
            inches = 0
        else:
            inches = regex.group(1)
    else:
        inches = regex.group(1).strip().replace('"', "").replace("”", "")
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

    return the_date, description, int(inches), float(price), float(rating), int(review_count), "amazon.ca"


def clean_csv(search_term: str, the_date: str) -> None:
    filename = search_term.replace(" ", "_") + "_results"
    if os.path.exists(filename + ".csv"):
        with open(filename + ".csv", 'r', encoding="utf-8") as fin, open(filename + "_temp.csv", 'w', newline='',
                                                                         encoding='utf-8') as fout:
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

        os.remove(filename + ".csv")
        os.rename(filename + "_temp.csv", filename + ".csv")


def write_csv(search_term: str, results: list[tuple]) -> None:
    filename = search_term.replace(" ", "_") + "_results.csv"
    write_header = True
    if os.path.exists(filename):
        write_header = False
    with open(filename, 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        if write_header:
            writer.writerow(["Date", "Description", "Size", "Price", "Rating", "Rting Cnt", "Source"])
        writer.writerows(results)


if __name__ == '__main__':
    main()
