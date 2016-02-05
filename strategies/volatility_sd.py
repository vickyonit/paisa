from datetime import datetime, date, timedelta
import calendar
from math import sqrt
import requests
import re
import csv
import numpy


def get_symbols():
    return ['NIFTY']

def is_equity(symbol):
    return True


def _run_strategy(symbol, date):
    stock_price = get_price(symbol, date)
    vix = get_vix(symbol)
    standard_deviation = calculate_one_standard_deviation(stock_price, vix)
    if standard_deviation/stock_price > 0.05:
        put_strike = round((stock_price - standard_deviation)/100) * 100
        call_strike = round((stock_price + standard_deviation)/100) * 100
        print "Yes, you should invest today:"
        print "Sell {} {} PE and {} CE".format(symbol, put_strike, call_strike)
        return True
    else:
        print "Sorry, better day is around the corner!"
        return False

def get_price(symbol, date):
    if is_equity(symbol):
        return get_equity_price(symbol, date)
    return get_index_price(symbol)

def run_strategy():
    for symbol in get_symbols():
        _run_strategy(symbol)


def get_index_price(symbol, date):
    previous_day = (date - timedelta(days=1)).strftime('%d-%m-%Y')
    url = 'http://www.nseindia.com/products/dynaContent/equities/indices/historicalindices.jsp?indexType={}%2050&fromDate={}&toDate={}'.\
        format(symbol, previous_day, previous_day)

    content = requests.get(url)._content
    regex = re.compile("<td class=\"number\">(?P<price>[0-9. ]+)<\/td>")
    price = float(regex.findall(content)[3])
    return price


def get_equity_price(symbol, date):
    previous_day = (date - timedelta(days=1)).strftime('%d-%m-%Y')
    days_ago_2 =  (date - timedelta(days=2)).strftime('%d-%m-%Y')
    url = 'http://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/getHistoricalData.jsp?symbol={}&series=EQ&fromDate={}&toDate={}'.\
        format(symbol, days_ago_2, previous_day)

    content = requests.get(url)._content
    regex = re.compile("<td>(?P<price>[0-9., ]+)<\/td>")
    price = float(regex.findall(content)[4])
    return price


def get_equity_vix(symbol, from_date):
    from_day = (from_date - timedelta(days=5)).strftime('%d-%b-%Y')
    to_day = (from_date - timedelta(days=1)).strftime('%d-%b-%Y')
    url = 'http://www.nseindia.com/live_market/dynaContent/live_watch/get_quote/getHistoricalData.jsp?symbol={}&series=EQ&fromDate={}&toDate={}'.\
        format(symbol, from_day, to_day)

    print url
    content = requests.get(url)._content

    regex = re.compile(r"<div\s+id=\'csvContentDiv\'\sstyle=\'display:none;\'>.*?<\/div>")
    con = regex.findall(content)[0]
    con = con.replace("<div id=\'csvContentDiv\' style=\'display:none;\'>\"Date\",\"Symbol\",\"Series\",\"Open Price\",\"High Price\",\"Low Price\",\"Last Traded Price \",\"Close Price\",\"Total Traded Quantity\",\"Turnover (in Lakhs)\":", '').replace(":</div>", "")
    reader = csv.reader(con.split(':'), delimiter=',')
    previous_day_value = 0
    percent_change = []
    for row in reader:
        today_value = float(row[7].replace(',',''))
        if not previous_day_value:
            previous_day_value = today_value
        else:
            percent_change.append(((today_value - previous_day_value) / previous_day_value) * 100)
            previous_day_value = today_value
    vix = numpy.std(percent_change) * sqrt(252)
    return vix


def get_vix(symbol, date):
    if is_equity(symbol):
        return get_equity_vix(symbol, date)
    return get_vix_for_nifty(date)


def get_vix_for_nifty(date):
    previous_day = (date - timedelta(days=1)).strftime('%d-%b-%Y')
    url = 'http://www.nseindia.com/products/dynaContent/equities/indices/hist_vix_data.jsp?&fromDate={}&toDate={}'. \
        format(previous_day, previous_day)
    content = requests.get(url)._content
    regex = re.compile("<td class=t1>(?P<vix>[0-9. ]+)<\/td>")
    vix = float(regex.findall(content)[3])
    return vix


def get_days_to_expiration(date):
    year = date.year
    month = date.month
    x = calendar.monthrange(year, month)
    last_thursday = x[1]
    while True:
        z = calendar.weekday(year, month, last_thursday)
        if z != 3:
            last_thursday -= 1
        else:
            return (date(year, month, last_thursday) - date.date()).days


def calculate_one_standard_deviation(stock_price, vix):
    days_to_expiration = get_days_to_expiration()
    deviation = (stock_price * (vix/100) * sqrt(days_to_expiration)) / sqrt(365)
    return deviation
