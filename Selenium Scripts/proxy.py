import requests
from random import sample, shuffle

ALL_PROXIES = []

def set_proxies(country_code='ALL'):
    global ALL_PROXIES
    token = open('proxies_token.txt','r').read().strip() # Get your token from https://proxy.webshare.io/user/dashboard
    response = requests.get(
        "https://proxy.webshare.io/api/v2/proxy/list/?mode=direct&page=1&page_size=100",
        headers={"Authorization": f"Token {token}"}
    )
    data = response.json()
    proxies = []

    country_codes = set()
    for item in data['results']:
        country_codes.add(item['country_code'])

    for item in data['results']:
        if country_code == 'ALL':
            proxy = f"http://{item['username']}:{item['password']}@{item['proxy_address']}:{item['port']}"
            proxies.append(proxy)
        else:
            if item['country_code'] == country_code:
                proxy = f"http://{item['username']}:{item['password']}@{item['proxy_address']}:{item['port']}"
                proxies.append(proxy)
    
    ALL_PROXIES = proxies

    return proxies

def get_random_proxies(n=1,random=True):
    global ALL_PROXIES
    shuffle(ALL_PROXIES)
    n = min(len(ALL_PROXIES), n)
    if random:
        return sample(ALL_PROXIES, n)
    else:
        return ALL_PROXIES[:n]
    
if __name__ == '__main__':
    proxies = set_proxies('ALL')
    print(proxies)
    print(len(proxies))
