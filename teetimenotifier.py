from models import *
from oauth2client.service_account import ServiceAccountCredentials
import gspread
from datetime import datetime


def open_sheet():
    scope = ['https://spreadsheets.google.com/feeds']
    credentials = ServiceAccountCredentials.from_json_keyfile_name('credentials.json', scope)
    gc = gspread.authorize(credentials)
    link = 'https://docs.google.com/spreadsheets/d/1R3BmywhR5hkjQIam-IIcsdY9j_wMaKKgS61qZ05qJAw/edit?usp=sharing'
    sh = gc.open_by_url(link).sheet1
    return sh


def get_days_desired(bools):
    day_options = ["Saturday", "Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]
    days = []
    for i in range(len(bools)):
        if bools[i] == 'Yes':
            days.append(day_options[i])

    return days


def create_courses(sheet):
    courses = []
    active_row = sheet.col_values(2)
    active = [x + 1 for x in range(len(active_row)) if active_row[x] == 'Yes']
    for i in active:
        data = sheet.batch_get(['A' + str(i) + ':S' + str(i)])[0][0]
        if data[3] == 'EzLinks':
            courses.append(EzGolf(i, data[0], data[2], get_days_desired(data[10:17]), data[4], data[5], data[6], data[7], data[17]))
        elif data[3] == 'Quick18':
            courses.append(Quick18(i, data[0], data[2], get_days_desired(data[10:17]), data[4], data[5], data[6], data[7], data[17]))
        elif data[3] == 'ForeUp':
            courses.append(ForeUp(i, data[0], get_days_desired(data[10:17]), data[4], data[6], data[8], data[9], data[17]))

    return courses


def update_previous_found(sheet, courses):
    updates = []
    for course in courses:
        updates.append({'range': 'R' + str(course.row) + ':S' + str(course.row),
                        'values': [[course.extract_ids(), datetime.now(SF).strftime("%m/%d/%Y, %H:%M:%S")]]})
    sheet.batch_update(updates)


# from teetimenotifier import *
sheet = open_sheet()  # returns object with access to Google Sheet
courses = create_courses(sheet)  # returns list of objects (courses) with all data
update_previous_found(sheet, courses)
# for course in courses:
#     print(course.name)
#     print(filter(lambda x: x.new == True, course.reservations))
#     print(filter(lambda x: x.new == True, course.reservations))
#     print('_________________________________________')
# for c in courses:
#     c.retrieve_data()
