import pytz
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
import json
SF = pytz.timezone('US/Pacific')

# TODO- change print failures to email, documentation, clearing of code, scan for new ones, send HTML email, text message, API endpoint


class Reservation:
    def __init__(self, id, course, date, time, players, price, cart_fee=None, subcourse=None, new=False):
        self.course = course
        self.id = id
        self.date = date
        self.time = time
        self.players = players
        self.price = price
        self.sub_course = subcourse
        self.cart_fee = cart_fee
        self.new = new


class EzGolf:
    def __init__(self, row, name, url, days, players, course_ids, days_out, price_class, previous_search):
        self.row = row
        self.name = name
        self.url = url.split('/index')[0] + '/api/search/search'
        self.days = days # ["Sunday", "Saturday", "Monday", "Wednesday", "Thursday", "Friday"]
        self.players = int(players) if int(players) > 0 and int(players) < 5 else 4
        self.course_ids = [int(x) for x in course_ids.split(',')] # 321, 341
        self.days_out = int(days_out)  # 10 or "10"
        self.num_holes = 1
        self.start_time = "5:00 AM"
        self.end_time = "7:00 PM"
        self.price = int(price_class) if int(price_class) != 0 else None
        self.previous_search = [int(x) for x in json.loads(previous_search)] if len(previous_search) > 0 else []
        self.reservations = []

        self.retrieve_data()

    def extract_ids(self):
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m/%d/%Y'))
        return dates

    def make_payload(self, date):
        return {"date": date,
                "numHoles": self.num_holes,
                "numPlayers": self.players,
                "startTime": self.start_time,
                "endTime": self.end_time,
                "courseIDs": self.course_ids}

    def make_id(self, date):
        return int(date.replace('-', '').replace('T', '').split(':00')[0].replace(':', ''))

    def parse_data(self, data, date):
        reservations = []
        for r in data:
            if (self.price is not None and int(r['SponsorID']) == self.price) or (self.price is None):
                reservations.append(Reservation(
                                                id=self.make_id(r['TeeTime']),
                                                course=self.name,
                                                date=date,
                                                time=r['TeeTimeDisplay'],
                                                players=r['PlayersAvailable'],
                                                price=r['Price'],
                                                subcourse=r['CourseName'],
                                                new=True if self.make_id(r['TeeTime']) not in self.previous_search else False
                                                )
                                    )
        return reservations

    def retrieve_data(self):
        reservations = []
        for d in self.get_list_dates():
            r = requests.post(self.url, self.make_payload(d))
            if r.status_code != 200:
                print("Failure")
            else:
                reservations_day = self.parse_data(json.loads(r.content.decode('utf-8'))['Reservations'], d)
                for x in reservations_day:
                    reservations.append(x)
        self.reservations = reservations


class Quick18:
    def __init__(self, row, name, url, days, players, course_id, days_out, price_class, previous_search):
        self.row = row
        self.name = name
        self.url = url.split('/teetimes')[0] + '/teetimes/searchmatrix'
        self.days = days  # ["Sunday", "Saturday", "Monday", "Wednesday", "Thursday", "Friday"]
        self.players = int(players) if int(players) > 0 and int(players) < 5 else 4
        self.course_ids = int(course_id) if len(course_id.split(',')) < 2 else 0 # 321, 341
        self.days_out = int(days_out)  # 10 or "10"
        self.time_day = "Any"
        self.price = int(price_class) - 1 if int(price_class) > 0 else None
        self.previous_search = [int(x) for x in json.loads(previous_search)] if len(previous_search) > 0 else []
        self.reservations = []

        self.retrieve_data()

    def extract_ids(self):
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m/%d/%Y'))
        return dates

    def make_payload(self, date):
        return {"SearchForm.Date": date,
                "SearchForm.TimeOfDay": str(self.time_day),
                "SearchForm.Players": str(self.players),
                "SearchForm.CourseId": str(self.course_ids)}

    def make_id(self, date):
        return int(date.split('/teetime/')[1].split('?')[0])

    def parse_data(self, html, date):
        soup = bs(html, "html.parser")
        reservations_raw = soup.find(attrs={'class': 'matrixTable'}).find('tbody').find_all('tr')
        reservations = []
        for r in reservations_raw:
            reservations.append(Reservation(course=self.name,
                                            id=self.make_id(r.find(attrs={'class': 'teebutton'})['href']),
                                            date=date,
                                            time=r.find(attrs={'class': 'mtrxTeeTimes'}).get_text().split()[0],
                                            players=r.find(attrs={'class': 'matrixPlayers'}).get_text(),
                                            price=[x.get_text() for x in r.findAll(attrs={'class': 'mtrxPrice'})][self.price] if self.price is not None else [x.get_text() for x in r.findAll(attrs={'class': 'mtrxPrice'})],
                                            subcourse=r.find(attrs={'class': 'mtrxCourse'}).get_text() if r.find(attrs={'class': 'mtrxCourse'}) is not None else None,
                                            new=True if self.make_id(r.find(attrs={'class': 'teebutton'})['href']) not in self.previous_search else False
                                            )
                                )
        return reservations

    def retrieve_data(self):
        reservations = []
        for d in self.get_list_dates():
            r = requests.post(self.url, self.make_payload(d))
            if r.status_code != 200:
                print("Failure")
            else:
                reservations_day = self.parse_data(r.content, d)
                for x in reservations_day:
                    reservations.append(x)

        self.reservations = reservations


class ForeUp:
    def __init__(self, row, name, days, players, days_out, schedule_id, booking_class, previous_search):
        self.row = row
        self.name = name
        self.url = 'https://foreupsoftware.com/index.php/api/booking/times?'
        self.days = days  # ["Sunday", "Saturday", "Monday", "Wednesday", "Thursday", "Friday"]
        self.players = int(players) if int(players) > 0 and int(players) < 5 else 4
        self.days_out = int(days_out)  # 10 or "10"
        self.b_class = int(booking_class)
        self.s_id = int(schedule_id)
        self.previous_search = [int(x) for x in json.loads(previous_search)] if len(previous_search) > 0 else []
        self.reservations = []

        self.retrieve_data()

    def extract_ids(self):
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m-%d-%Y'))
        return dates

    def make_payload(self, date):
        return self.url + f"time=all&date%={date}&holes=18&players={self.players}&booking_class={self.b_class}&schedule_id={self.s_id}&specials_only=0&api_key=no_limits"

    def make_id(self, date):
        return int(date.replace('-', '').replace(' ', '').replace(':', ''))

    def parse_data(self, data, date):
        reservations = []
        for r in data:
            reservations.append(Reservation(
                                            id=self.make_id(r['time']),
                                            course=self.name,
                                            date=date,
                                            time=r['time'].split(' ')[1],
                                            players=r['available_spots'],
                                            price=r['guest_green_fee'],
                                            subcourse=r['schedule_name'],
                                            cart_fee=r['guest_cart_fee'],
                                            new=True if self.make_id(r['time']) in self.previous_search else False
                                            )
                                )
        return reservations

    def retrieve_data(self):
        reservations = []
        for d in self.get_list_dates():
            r = requests.get(self.make_payload(d))
            if r.status_code != 200:
                print("Failure")
            else:
                reservations_day = self.parse_data(json.loads(r.content.decode('utf-8')), d)
                for x in reservations_day:
                    reservations.append(x)

        self.reservations = reservations
