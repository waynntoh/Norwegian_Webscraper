# Import required modules
import requests
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from time import sleep
from LoadingProgressTools import TimeTools
import random
import sys
import csv


def get_destination_codes():
    '''
    Scrapes for flight destinations' country and code available from the UK (Note: Incomplete)

    :return: A list of destinations' data
    '''

    url = 'https://www.norwegian.com/uk/destinations/'
    response = requests.get(url).text
    html = BeautifulSoup(response.text, 'html.parser')

    # Create a list to store data
    data = [['Destination', 'Country', 'Code']]

    # Extract data
    destination_list_items = html.find_all('li', attrs={'class': 'destination-list__item--col-3'})

    for item in destination_list_items:
        destination = item.find('span', attrs={'class': 'destination-list__title__link--click'}).getText()
        country = item.find('span', attrs={'class': 'preamble'}).getText()
        code = item.find('span', attrs={'class': 'airport-avatar__text'}).getText()

        # Clean data
        destination = destination.replace(country, '')
        destination = destination.replace(' ', '')
        destination = destination.replace('\n', '')
        destination = destination.replace('\r', '')

        new_row = [destination, country, code]
        data.append(new_row)

    return data


def build_url(origin, destination, date, transit, currency, mode):
    '''
    Builds a url for the Norwegian booking site

    :param origin: A code for the origin country (exp. LGW = London Gatwick) [String]
    :param destination: A code for the destination country (exp. ALC = Alicante, Spain) [String]
    :param date: A date sequence represented as (exp. 20190101) [String]
    :param transit: Whether or not to search for transit or direct only flights [String]
    :param currency: A code for the currency [String]
    :param mode: Unknown [String]
    :return: A url for the Norwegian booking site with specified parameters
    '''

    # Convert date into url format
    year = '{0:0=4d}'.format(date.year)
    month = '{0:0=2d}'.format(date.month)
    day = '{0:0=2d}'.format(date.day)

    BASE = 'https://www.norwegian.com/uk/ipc/availability/avaday?'
    queries = {
        'AdultCount': '1',
        'A_City': destination,
        'D_City': origin,
        'D_Month': str(year + '' + month),
        'D_Day': day,
        'IncludeTransit': transit,
        'TripType': '1',
        'CurrencyCode': currency,
        'mode': mode
    }

    queries = urlencode(queries)
    url = BASE + queries
    return url


def get_random_sleep(list_of_ints):
    '''
    Generates and returns a random int from the list parameter

    :param list_of_ints: A list of integers [list]
    :return: An integer
    '''

    random_int = random.choice(list_of_ints)
    return random_int


def day_scrape(origin, destination, date, list, transit, currency, mode):
    '''
    Scrapes flight details for the specified date

    :param origin: A code for the origin country (exp. LGW = London Gatwick) [String]
    :param destination: A code for the destination country (exp. ALC = Alicante, Spain) [String]
    :param date: A date sequence represented as (exp. 20190101)
    :param list: A list to write scraped data onto [List]
    :param transit: Whether or not to search for transit or direct only flights [String]
    :param currency: A code for the currency [String]
    :param mode: Unknown [String]
    :return: A list of newly scraped data
    '''

    # Build a url for a specific day
    url = build_url(origin=origin, destination=destination, date=date, transit=transit, currency=currency,
                    mode=mode)
    response = requests.get(url).text

    # Convert page into html
    soup = BeautifulSoup(response, 'html.parser')

    # Create presentable date format
    date = date.strftime('%a %x')

    try:

        # Get data rows
        table = soup.find('div', attrs={'class': 'bodybox'})
        info1_row = table.find_all('tr', attrs={'class': 'rowinfo1'})
        info2_row = table.find_all('tr', attrs={'class': 'rowinfo2'})
        last_row = table.find_all('tr', attrs={'class': 'lastrow'})

        # Loop through flights to extract data
        for i in range(0, len(info1_row)):

            # Extract tickets info to check if there are flights
            departure = info1_row[i].find('td', attrs={'class': 'depdest'}).find('div', attrs={
                'class': 'content emphasize'}).getText()
            arrival = info1_row[i].find('td', attrs={'class': 'arrdest'}).find('div', attrs={
                'class': 'content emphasize'}).getText()
            duration = info2_row[i].find('td', attrs={'class': 'duration'}).find('div', attrs={
                'class': 'content'}).getText()
            stops = info1_row[i].find('td', attrs={'class': 'duration'}).find('div', attrs={
                'class': 'content'}).getText()

            # Check if detail exists, set as empty string otherwise
            try:
                detail = last_row[i].find('li', attrs={'class': 'tooltipclick TooltipBoxTransit'}).getText()
            except AttributeError:
                try:
                    detail = last_row[i].find('li', attrs={'class': 'tooltipclick TooltipBoxNightstop'}).getText()
                except AttributeError:
                    detail = '-'

            # Check if flight number is presented, set as empty string otherwise
            try:
                flight = info1_row[i].find('input', attrs={'type': 'hidden'}).get('value')
            except AttributeError:
                flight = '-'

            # Lowfare Tickets
            try:
                lowfare = info1_row[i].find('td', attrs={'class': 'fareselect standardlowfare'}).find(
                    'label', attrs={'class': 'label seatsokfare'}).getText()
            except AttributeError:
                try:
                    lowfare = info1_row[i].find('td', attrs={'class': 'fareselect standardlowfare'}).find(
                        'label', attrs={'class': 'label fewseatsleftfare'}).getText()
                except AttributeError:
                    try:
                        lowfare = info1_row[i].find('td', attrs={'class': 'nofare standardlowfare'}).find(
                            'div', attrs={'class': 'content'}).getText()
                    except AttributeError:
                        lowfare = '-'

            # Lowfareplus Tickets
            try:
                lowfareplus = info1_row[i].find('td', attrs={'class': 'fareselect standardlowfareplus'}).find(
                    'label', attrs={'class': 'label seatsokfare'}).getText()
            except AttributeError:
                try:
                    lowfareplus = info1_row[i].find('td', attrs={'class': 'fareselect standardlowfareplus'}).find(
                        'label', attrs={'class': 'label fewseatsleftfare'}).getText()
                except AttributeError:
                    try:
                        lowfareplus = info1_row[i].find('td', attrs={'class': 'nofare standardlowfareplus'}).find(
                            'div', attrs={'class': 'content'}).getText()
                    except AttributeError:
                        lowfareplus = '-'

            # Flex Tickets
            try:
                flex = info1_row[i].find('td', attrs={'class': 'fareselect standardflex endcell'}).find(
                    'label', attrs={'class': 'label seatsokfare'}).getText()
            except AttributeError:
                try:
                    flex = info1_row[i].find('td', attrs={'class': 'fareselect standardflex endcell'}).find(
                        'label', attrs={'class': 'label fewseatsleftfare'}).getText()
                except AttributeError:
                    try:
                        flex = info1_row[i].find('td', attrs={'class': 'nofare standardflex endcell'}).find(
                            'div', attrs={'class': 'content'}).getText()
                    except AttributeError:
                        flex = '-'

            # Clean scraped data
            duration = duration[10:18]
            if flight is not '-':
                flight = flight[2:8]

            # Create a new row of data
            new_row = [date, departure, arrival, duration, stops, lowfare, lowfareplus, flex, flight, detail]
            # Append new row to existing rows
            list.append(new_row)
    except AttributeError:
        # Create a new row of data for scrape failure
        new_row = [date, '-', '-', '-', '-', '-', '-', '-', '-', '-']
        # Append new row to existing rows
        list.append(new_row)

    return list


def period_scrape(origin, destination, end_date, start_date='', transit='true', currency='GBP', mode='ab'):
    '''
    Scrapes for flight date for a a specific period. (Note: Norwegian mostly prepares flights 6-8 months ahead of time)

    :param origin: A code for the origin country (exp. LGW = London Gatwick) [String]
    :param destination: A code for the destination country (exp. ALC = Alicante, Spain) [String]
    :param start_date: The starting date of the period for scraping (Exp. 20190101) [String]
    :param end_date: The end date of the period for scraping (Exp. 20190131) [String]
    :param transit: Whether or not to search for transit or direct only flights [String]
    :param currency: A code for the currency [String]
    :param mode: Unknown [String]
    :return: A url for the Norwegian booking site with specified parameters
    '''

    # Creates a list to store scraped data
    list = [['Date', 'Departure', 'Arrival', 'Duration', 'Stops', 'LowFare(£)', 'LowFare+(£)', 'Flex(£)', 'Flight', 'Details']]

    if start_date == '':
        today = datetime.today() + timedelta(days=1)
        start_date = str(today.year) + '{0:0=2d}'.format(today.month) + '{0:0=2d}'.format(today.day)

    # Convert start and end dates into date objects
    start_day = datetime(year=int(start_date[0:4]), month=int(start_date[4:6]), day=int(start_date[6:8]))
    end_date = datetime(year=int(end_date[0:4]), month=int(end_date[4:6]), day=int(end_date[6:8]))

    # Prep iterations
    delta = timedelta(days=1)
    progress_index = 0
    diff = ((end_date - start_day).days + 1)
    sleep_time = 1
    timetool = TimeTools.TimeTool()
    timetool.start_count()

    # Loop through scrape period for web scraping
    while start_day <= end_date:
        sys.stdout.write('\rProgress: [%d/%d] (days)  ||  ETA: [%s]' %
                         (progress_index, diff, timetool.time_remaining(progress_index, diff, sleep_time)))

        # Call day_scrape method to scrap daily data
        day_scrape(origin=origin, destination=destination, date=start_day, list=list, transit=transit,
                   currency=currency, mode=mode)

        # Proceed iterations
        start_day += delta
        progress_index += 1

        # A delay before the next request is made to avoid banning from website
        sleep(sleep_time)

    # End progress bar
    timetool.end_count()
    return list


data = period_scrape(origin='LGW', destination='ALC', start_date='20191001', end_date='20200831')

# Create and write data to a csv file
TITLE_BASE = 'London Gatwick - Alicante '
date = datetime.today()
date = date.strftime('%d-%m-%Y')
date = '[' + str(date) + ']'
EXTENSION = '.csv'
title = TITLE_BASE + date + EXTENSION

new_file = open(title, 'w', newline='')
csv_output = csv.writer(new_file)
csv_output.writerows(data)
