from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import re
import csv
from datetime import datetime

def main():
    the_date = datetime.today().strftime('%Y-%m-%d')
    s = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=s)
    amazon(the_date, driver)


def amazon(the_date, driver):
    url = get_amazon_url('lg oled c1 series')
    driver.get(url)

    soup = BeautifulSoup(driver.page_source, "html.parser")
    results = soup.find_all('div', {'data-component-type': 's-search-result'})

    records = []
    for item in results:
        record = extract_amazon_record(the_date, item)
        if record:
            records.append(record)

    write_csv(records)


def get_amazon_url(search_term):
    # https://www.amazon.ca/s?k=lg+oled+c1+series+55"&ref=nb_sb_noss
    template = "https://www.amazon.ca/s?k={}&ref=nb_sb_noss"
    search_term = search_term.replace(" ", "+")
    return template.format(search_term)


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
        rating = item.i.text
    except AttributeError:
        rating = ''
    try:
        review_count = item.find('span', {'class': 'a-size-base'}).text
    except AttributeError:
        review_count = 0

    return the_date, description, inches, float(price), rating, review_count, "amazon.ca"


def write_csv(results):
    with open('results.csv', 'a', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["Date", "Description", "Size", "Price", "Rating", "Rting Cnt", "Source"])
        writer.writerows(results)


if __name__ == '__main__':
    main()
