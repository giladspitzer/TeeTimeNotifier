import requests, datetime, json, boto3
from bs4 import BeautifulSoup


def get_news_data(link, identifyer=None):
    """This function receives the link of the website to call, stores the content as a Beautiful Soup object, obtains
    the article data via the div class articleCopy, and returns that data."""
    webpage_response = requests.get(link)  # calls the website
    webpage = webpage_response.content  # stores the content of the website
    soup = BeautifulSoup(webpage, "html.parser")  # stores content as Beautiful Soup object
    if identifyer is not None:
        article = soup.find(attrs={'class': identifyer})  # stores the article content of the site
        print('\nDownloaded article data from', link)
        return article
    else:
        print('\nDownloaded article data from', link)
        return soup


def get_latest_news_date():
    site_data = get_news_data('https://www.car.org/aboutus/mediacenter/newsreleases', 'articleCopy')
    latest = site_data.find_all('p')[1].get_text().split(':')
    latest_date = latest[0]
    latest_text = latest[1]
    return latest_date, latest_text


def get_last_updated_date():
    site_data = get_news_data('https://connect-ad89addf944e.s3.amazonaws.com/latestnews.json')
    text = site_data.text
    date = text.split('is dated ')[1].split(' and')[0]
    return date


def compile_news_data(soup):

    def get_headers():
        headers_raw = soup.find_all('h6')
        headers = ['']
        for header in headers_raw:
            headers.append(header.get_text())
        headers.append('')
        return headers

    def get_blurbs():
        blurbs_raw = soup.find_all('p')
        blurbs = ['']
        for blurb in blurbs_raw:
            blurbs.append(blurb.get_text())
        if blurbs[1] == blurbs[2]:
            blurbs.pop(0)
        return blurbs

    def get_links():
        buttons = soup.find_all(attrs={'class': 'underline blue accessible'})
        links = ['']
        for i in range(len(buttons)):
            links.append('www.car.org' + str(buttons[i]['href']))
        links.append('')
        return links

    return get_headers(), get_blurbs(), get_links()


def create_dictionary(date, headers, blurbs, links):
    keys = ['uid', 'updateDate', 'titleText', 'mainText', 'redirectionUrl']  # list of keys for each dictionary
    dicts = ['', headers[0], headers[1], headers[2], 'More Info']  # labels
    master_dictionary = []  # master dictionary that will hold all 5 of the subs

    for i in range(len(dicts)):
        dictionary = {}
        if i == 0:  # if first item (intro dict) then text is just the date
            text = 'This update is dated ' + date + ' and will inform you on the latest news at California ' \
                                                    'Association of REALTORS.'

        elif i == 4:  # if last item (more info dict) then give info about more info
            text = 'For links to more information or to read more CAR news reports,' \
                   ' head to www.car.org/about us/media center/news releases.'

        else:  # otherwise concatenate text's info with their heading
            text = blurbs[i] + ' For more information on this specific news release, head to: ' + links[i]

        uid = 'EXAMPLE_CHANNEL_MULTI_ITEM_JSON_TTS_' + str(i)  # unique id required for each dict in Alexa
        date = str(datetime.datetime.now().isoformat()).split('T') # required date format for Alexa
        date = date[0] + 'T0' + str(i) + ':00:00.0Z'  # had to debug this --> datetime.isoformat was not working
        title = 'C.A.R Latest News: ' + dicts[i]  # Title displayed during each dict
        # Parallel list of values for keys list above
        values = [uid, date, title, text, 'https://www.car.org/aboutus/mediacenter/newsreleases']
        for i in range(len(keys)):  # formulates dict for each text in list passed into function and adds to master
            dictionary[keys[i]] = values[i]

        master_dictionary.append(dictionary)

    print('Created model for JSON')

    return master_dictionary


def upload_file(dictionary, file_name, bucket):
    """This function accepts a file and AWS bucket, and uploads the file to the S3 bucket and makes it public while also
    specifying its application/json format for the parameter content type (under Metadata in browser). There is a setup
     that must take place in order for the boto3 SDK to work. I used terminal to pip install boto3 and awscli. Then I
     gave terminal aws configure and I was prompted to enter the aws_access_key_id, aws_secret_access_key, and region.
     """

    try:
        s3 = boto3.resource(
            's3',
            region_name='us-east-1',
            aws_access_key_id=***REMOVED***,
            aws_secret_access_key=***REMOVED***
        )
        content = json.dumps(dictionary).encode("utf-8")
        s3.Object(bucket, file_name).put(Body=content, ContentType= 'application/json', Bucket= bucket, Key=file_name,
                                         ACL="public-read")

    except:
        return False

    print('Uploaded latestnews.json file to AWS S3 bucket')

    return True


def setup(event=None, context=None):
    date, text = get_latest_news_date()
    last_updated_date = get_last_updated_date()

    if date != last_updated_date:
        article_data = get_news_data('https://www.car.org/', 'newsItems')
        headers, blurbs, links = compile_news_data(article_data)
        master_dictionary = create_dictionary(date, headers, blurbs, links)
        state = upload_file(master_dictionary, 'latestnews.json', 'connect-ad89addf944e')
        # print final status of program
        if state:
            print('\n------> Success!')
        else:
            print('\n------> Sorry something went wrong. Please try again later.')
    else:
        print('nothing to update!')


setup()

