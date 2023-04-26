import sys
import pandas as pd
import xmltodict
import requests
import os
import time

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

def get_last_index(url):
    #coding utf8 for korean
    response = requests.get(url).content.decode('utf8')
    #convert xml to dict
    xml = xmltodict.parse(response)
    
    last_url = next(filter(lambda l: l['@rel'] == 'last', xml['feed']['link']))['@href']
    last_index = next(filter(lambda s: 'page=' in s, last_url.split('/'))).replace('page=', '')
    last_index = int(last_index)

    return last_index

def appstore_crawler (appid, outfile='./appstore_reviews.csv'):
    url = f'https://itunes.apple.com/kr/rss/customerreviews/page=1/id={appid}/sortby=mostrecent/xml'

    #exception handling for no review
    try:
        last_index = get_last_index(url)
    except Exception as e:
        print (url)
        print (f'\tNo Reviews: appid {appid}')
        print (f'\tExeption: {e}')
        return
    
    result = list()
    for idx in range(1, last_index+1):
        url = f"https://itunes.apple.com/kr/rss/customerreviews/page={idx}/id={appid}/sortby=mostrecent/xml?urlDesc=/customerreviews/id={appid}/sortBy=mostRecent/xml"
        print(url)

        response = requests.get(url).content.decode('utf8')

        # sleep for 1 second after request
        time.sleep(1)

        #exception handling for broken xml
        try:
            xml = xmltodict.parse(response)
        except Exception as e:
            print (f'\tXml Parse Error {e}\n\tSkip {url} :')
            continue
        
        #check if there's a review
        try:
            num_reviews = len(xml['feed']['entry'])
        except Exception as e:
            print (f'\tNo Entry {e}')
            continue

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
    res_df.to_csv(outfile, encoding='utf-8-sig', index=False)
    print ('Save reviews to file: %s \n' %(outfile))

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
    
    outfile = os.path.join('appstore_' + str(app_id)+'.csv')
    appstore_crawler(app_id, outfile=outfile)
    print(f'App\'s url-> {app_url}')
