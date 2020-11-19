from requests import Request, Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
import json
import logging


def main():
    api = CoingeckoApi()
    portfolio = {'bitcoin': 1.0,
                 'ethereum': 42.0}
    print(api.get_portfolio_value(portfolio))


class CoingeckoApi:
    def __init__(self):
        self.ids = self.get_ids()

    def get_portfolio_value(self, portfolio):
        total_value = 0.0
        parameters = {
            'ids': ','.join(portfolio.keys()),
            'vs_currencies': 'eur'
        }
        data = self.request('simple/price', parameters)
        for currency in data:
            price = float(data[currency]['eur'])
            balance = portfolio[currency]
            value = balance * price
            total_value += value

        return total_value

    def get_ids(self):
        ids = []
        data = self.request('coins/list')
        for currency in data:
            ids.append(currency['id'])
        return ids

    def is_valid_id(self, id):
        if id in self.ids:
            return True
        else:
            return False

    def request(self, resource, parameters=None):
        url = 'https://api.coingecko.com/api/v3/' + resource
        session = Session()
        try:
            response = session.get(url, params=parameters)
            data = json.loads(response.text)
        except (ConnectionError, Timeout, TooManyRedirects) as e:
            data = None
            logging.critical(e)

        return data


if __name__ == '__main__':
    main()
