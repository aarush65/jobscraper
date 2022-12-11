
from __future__ import print_function

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import google_auth_oauthlib
import requests
import json
from bs4 import BeautifulSoup

def extractLinkedln(page):
  # Grabs raw HTML from the linkedln url
  headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'}
  url = f'https://www.linkedin.com/jobs/search/?currentJobId=3367365685&distance=25&f_E=1&geoId=103644278&keywords=software%20engineer%20intern&start={page}'
  r = requests.get(url, headers)
  soup = BeautifulSoup(r.content, 'html.parser') 
  return soup

def transformLinkedln(soup):
    # Transforms HTML to an array of arrays with details about the job posting(Each job has a title, company name, and link to the application)
    jobs = []
    for job in soup.find_all("li"):
        company, title,lin = None,None,None

        t = job.find('h3')
        if t != None:
            title = t.text.strip()
        box = job.find('a',attrs={'class':'hidden-nested-link'})
        if box != None:
            lk = box.get('href')[33:]
            company = lk.split("?")[0]
        link = job.find('a',attrs={'class':'base-card__full-link absolute top-0 right-0 bottom-0 left-0 p-0 z-[2]'})
        if link != None:
            lin = link.get('href')
        if title != None and box != None and lin != None:
            job =  [
                title,
                company,
                lin,
            ]
            jobs.append(job)
    return jobs


def getCreds(scope, client, secret):
    # Gets credentials of users 
    # Returns token which then can be used to call the Sheets API
    return google_auth_oauthlib.get_user_credentials(scope, client,secret)
def create(title,creds):
    # Creates a spreadsheet
    try:
        service = build('sheets', 'v4', credentials=creds)
        spreadsheet = {
            'properties': {
                'title': title
            }
        }
        spreadsheet = service.spreadsheets().create(body=spreadsheet,
                                                    fields='spreadsheetId') \
            .execute()
        print(f"Spreadsheet ID: {(spreadsheet.get('spreadsheetId'))}")
        return spreadsheet.get('spreadsheetId')
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error

def update_values(spreadsheet_id, range_name, value_input_option,
                  _values, creds):
    # Update values in the spreadsheet
    try:
        service = build('sheets', 'v4', credentials=creds)
        body = {
            'values': _values
        }
        result = service.spreadsheets().values().update(
            spreadsheetId=spreadsheet_id, range=range_name,
            valueInputOption=value_input_option, body=body).execute()
        print(f"{result.get('updatedCells')} cells updated.")
        return result
    except HttpError as error:
        print(f"An error occurred: {error}")
        return error


if __name__ == '__main__':
    with open('credentials.json') as user_file:
        file_contents = user_file.read()
    info = json.loads(file_contents)['installed']
    c_id = info['client_id']
    c_secret =  info['client_secret']
    scope = ["https://www.googleapis.com/auth/spreadsheets"]

    creds = getCreds(scope,c_id,c_secret)
    c = extractLinkedln(0)
    tmp = transformLinkedln(c)
    spreadsheet_id = create("Final", creds)
    print(update_values(spreadsheet_id,'A1:C25',"USER_ENTERED", tmp, creds))
    
    