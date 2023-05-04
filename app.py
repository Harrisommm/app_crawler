import pandas as pd
import xmltodict
import requests
import os
import time
import sys

app_info = {
    'burnfit': 
    {
        'id': 1503464984,
        'url': 'https://apps.apple.com/kr/app/%EB%B2%88%ED%95%8F-%EC%9A%B4%EB%8F%99-%EC%9D%BC%EC%A7%80-%EB%81%9D%ED%8C%90%EC%99%95/id1503464984'
    },
    'fleek': 
    {
        'id': 1576993198,
        'url': 'https://apps.apple.com/kr/app/%ED%94%8C%EB%A6%AD-%EC%9A%B4%EB%8F%99%EC%9D%BC%EC%A7%80-%EC%9A%B4%EB%8F%99%EA%B8%B0%EB%A1%9D-%EC%9A%B4%EB%8F%99%EC%9D%BC%EA%B8%B0-%EC%9A%B4%EB%8F%99%EB%A3%A8%ED%8B%B4/id1576993198'
    },
    'planfit': 
    {
        'id': 1511876936,
        'url': 'https://apps.apple.com/kr/app/%ED%94%8C%EB%9E%9C%ED%95%8F-%ED%97%AC%EC%8A%A4-%ED%99%88%ED%8A%B8-%EC%9A%B4%EB%8F%99-%EB%A3%A8%ED%8B%B4-%EC%B6%94%EC%B2%9C%EA%B3%BC-%ED%94%BC%ED%8A%B8%EB%8B%88%EC%8A%A4-%EA%B8%B0%EB%A1%9D/id1511876936'
    },
    'fiet': 
    {
        'id': 1643675480,
        'url': 'https://apps.apple.com/app/id1643675480?mt=8'
    }
}

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
    #convert xml to dict
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

def appstore_crawler (appid, outfile='./appstore_reviews.csv'):
    url = get_url(app_id)

    #exception handling for no review
    try:
        last_index = get_last_index(url)
    except Exception as e:
        print (url)
        print (f'\tNo Reviews: appid {appid}')
        print (f'\tExeption: {e}')
        return
    
    result = []
    for idx in range(1, last_index + 1):
        url = get_url(app_id, idx)
        print(url)

        response = request_api(url)

        # sleep for 1 second after request
        time.sleep(1)

        #exception handling for broken xml
        try:
            xml = xmltodict.parse(response)
        except Exception as e:
            print (f'\tXml Parse Error {e}\n\tSkip {url} :')
            continue
        
        reviews = process_reviews(xml)
        result.extend(reviews)

        #prevent error when there is only 1 review
        try:
            xml['feed']['entry'][0]['author']['name']
            single_reviews = False
        except:
            #print ('\tOnly 1 review!!!')
            single_reviews = True
            pass

        #save user review on a list
        if single_reviews:
                result.append({
                    'USER': xml['feed']['entry']['author']['name'],
                    'DATE': xml['feed']['entry']['updated'],
                    'STAR': int(xml['feed']['entry']['im:rating']),
                    'LIKE': int(xml['feed']['entry']['im:voteSum']),
                    'TITLE': xml['feed']['entry']['title'],
                    'REVIEW': xml['feed']['entry']['content'][0]['#text'],
                })
        else:
            for i in range(len(xml['feed']['entry'])):
                result.append({
                    'USER': xml['feed']['entry'][i]['author']['name'],
                    'DATE': xml['feed']['entry'][i]['updated'],
                    'STAR': int(xml['feed']['entry'][i]['im:rating']),
                    'LIKE': int(xml['feed']['entry'][i]['im:voteSum']),
                    'TITLE': xml['feed']['entry'][i]['title'],
                    'REVIEW': xml['feed']['entry'][i]['content'][0]['#text'],
                })



    #create dataframe
    res_df = pd.DataFrame(result)
    #implement to dataframe
    res_df['DATE'] = pd.to_datetime(res_df['DATE'], format="%Y-%m-%dT%H:%M:%S-07:00")
    with open(outfile, 'w', encoding='utf-8-sig') as f:
        res_df.to_csv(f, index=False)
    print(f'Save reviews to file: {outfile}\n')

def main(app_id, app_url):
    outfile = os.path.join('appstore_' + str(app_id) + '.csv')
    appstore_crawler(app_id, outfile=outfile)
    print(f"App's url-> {app_url}")

# if __name__ == '__main__':
#     parser = argparse.ArgumentParser(description='Crawl app store reviews for the given app ID and URL.')
#     parser.add_argument('--app-id', type=int, required=True, help='App ID to crawl reviews for')
#     parser.add_argument('--app-url', type=str, required=True, help='App URL to display after crawling')

#     args = parser.parse_args()

#     main(args.app_id, args.app_url)
    
if __name__ == '__main__':
    switch = input("Please specify the number for app crawling. 1.Burnfit  2.Fleek  3.Planfit  4.Fiet:  ")
    
    if switch == "1":
        print("Crawling Burnfit reviews.")
        app_id = app_info['burnfit']['id']
        app_url = app_info['burnfit']['url']
    elif switch == "2":
        print("Crawling Fleek reviews.")
        app_id = app_info['fleek']['id']
        app_url = app_info['fleek']['url']
    elif switch == "3":
        print("Crawling Planfit reviews.")
        app_id = app_info['planfit']['id']
        app_url = app_info['planfit']['url']
    elif switch == "4":
        print("Crawling Fiet reviews.")
        app_id = app_info['fiet']['id']
        app_url = app_info['fiet']['url']
    else:
        print("Invalid input. Please enter a number between 1 and 4.")
        sys.exit(1)
    
    main(app_id, app_url)
    