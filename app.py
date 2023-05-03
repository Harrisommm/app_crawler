import sys
import pandas as pd
import xmltodict
import requests
import os
import time
import argparse

def get_url(app_id, page=1):
    """Generate the URL to request app reviews."""
    return f'https://itunes.apple.com/kr/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/xml'

def request_api(url):
    """Request the given URL and return the decoded content."""
    response = requests.get(url)
    return response.content.decode('utf8')

def get_last_index(url):
    """Retrieve the last index for the app reviews."""
    response = request_api(url)
    xml = xmltodict.parse(response)
    last_url = next(filter(lambda l: l['@rel'] == 'last', xml['feed']['link']))['@href']
    last_index = next(filter(lambda s: 'page=' in s, last_url.split('/'))).replace('page=', '')
    last_index = int(last_index)
    return last_index

def process_reviews(xml):
    """Process the XML content and return the list of review dictionaries."""
    try:
        entries = xml['feed']['entry']
    except KeyError:
        print(f'\tNo Entry')
        return []

    if not isinstance(entries, list):
        entries = [entries]

    result = []
    for entry in entries:
        result.append({
            'USER': entry['author']['name'],
            'DATE': entry['updated'],
            'STAR': int(entry['im:rating']),
            'LIKE': int(entry['im:voteSum']),
            'TITLE': entry['title'],
            'REVIEW': entry['content'][0]['#text'],
        })

    return result

def appstore_crawler(app_id, outfile='./appstore_reviews.csv'):
    """Crawl app reviews and save them to a file."""
    url = get_url(app_id)
    try:
        last_index = get_last_index(url)
    except Exception as e:
        print(url)
        print(f'\tNo Reviews: appid {app_id}')
        print(f'\tException: {e}')
        return

    result = []
    for idx in range(1, last_index + 1):
        url = get_url(app_id, idx)
        print(url)

        response = request_api(url)
        time.sleep(1)

        try:
            xml = xmltodict.parse(response)
        except Exception as e:
            print(f'\tXml Parse Error {e}\n\tSkip {url} :')
            continue

        reviews = process_reviews(xml)
        result.extend(reviews)

    res_df = pd.DataFrame(result)
    res_df['DATE'] = pd.to_datetime(res_df['DATE'], format="%Y-%m-%dT%H:%M:%S-07:00")
    with open(outfile, 'w', encoding='utf-8-sig') as f:
        res_df.to_csv(f, index=False)
    print(f'Save reviews to file: {outfile}\n')

def main(app_id, app_url):
    outfile = os.path.join('appstore_' + str(app_id) + '.csv')
    appstore_crawler(app_id, outfile=outfile)
    print(f"App's url-> {app_url}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Crawl app store reviews for the given app ID and URL.')
    parser.add_argument('--app-id', type=int, required=True, help='App ID to crawl reviews for')
    parser.add_argument('--app-url', type=str, required=True, help='App URL to display after crawling')

    args = parser.parse_args()

    main(args.app_id, args.app_url)
    