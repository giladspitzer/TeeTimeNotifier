import pytz
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup as bs
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import json
import os
import boto3

SF = pytz.timezone('US/Pacific')


class Reservation:
    """Standard Model to hold data of reservations found for each course."""
    def __init__(self, id, course, date, time, players, price, cart_fee=None, subcourse=None, new=False):
        self.course = course
        self.id = id
        self.date = date
        self.time = time
        self.players = players
        self.price = price
        self.sub_course = subcourse.split('-')[1] if '-' in subcourse else subcourse
        self.cart_fee = cart_fee
        self.new = new

    def render_html(self):
        if self.cart_fee is not None:
            return f'<div class="reservation"><ul><li><b>@{self.time}</b></li><li>Players: {self.players}</li><li>${self.price}</li><li>Cart: ${self.cart_fee}</li><li>{self.sub_course}</li></ul></div>'
        else:
            return f'<div class="reservation"><ul><li><b>@{self.time}</b></li><li>Players: {self.players}</li><li>${self.price}</li><li>{self.sub_course}</li></ul></div>'

class EzGolf:
    """Standard Model to accept data for any tee-time website that makes use of the ez-golf software."""
    def __init__(self, row, name, url, days, players, course_ids, days_out, price_class, previous_search, img, tod_s, tod_e):
        self.row = row
        self.name = name
        self.url = url.split('/index')[0] + '/api/search/search'
        self.days = days # ["Sunday", "Saturday", "Monday", "Wednesday", "Thursday", "Friday"]
        self.players = int(players) if int(players) > 0 and int(players) < 5 else 4
        self.course_ids = [int(x) for x in course_ids.split(',')] # 321, 341
        self.days_out = int(days_out)  # 10 or "10"
        self.num_holes = 1
        self.start_time = tod_s
        self.end_time = tod_e
        self.price = int(price_class) if int(price_class) != 0 else None
        self.previous_search = [int(x) for x in json.loads(previous_search)] if len(previous_search) > 0 else []
        self.reservations = []
        self.html = ''
        self.img = img if img != '0' else 'https://teetimenotifier.s3-us-west-1.amazonaws.com/teetimenotifier.png'
        self.booking_url = url

        self.retrieve_data()
        self.create_html()

    def extract_ids(self):
        """Used to create a list of ids for all reservations found for course"""
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        """Returns list of strings (dates) that should be searched (based on how many days out and which days of week"""
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m/%d/%Y'))
        return dates

    def make_payload(self, date):
        """Returns payload for this website type packaged with accompanying data"""
        return {"date": date,
                "numHoles": self.num_holes,
                "numPlayers": self.players,
                "startTime": self.start_time,
                "endTime": self.end_time,
                "courseIDs": self.course_ids}

    def make_id(self, date):
        """Creates unique id for reservation based on timestamp -- used to keep track of whats new"""
        return int(date.replace('-', '').replace('T', '').split(':00')[0].replace(':', ''))

    def format_date(self, date):
        return datetime.strptime(date,'%m/%d/%Y').strftime('%A') + ' ' + date

    def parse_data(self, data, date):
        """Accepts html found from website and pareses it into list of reservations"""
        reservations = []
        for r in data:
            if (self.price is not None and int(r['SponsorID']) == self.price) or (self.price is None):
                reservations.append(Reservation(
                                                id=self.make_id(r['TeeTime']),
                                                course=self.name,
                                                date=self.format_date(date),
                                                time=r['TeeTimeDisplay'],
                                                players=r['PlayersAvailable'],
                                                price=r['Price'],
                                                subcourse=r['CourseName'],
                                                new=True if self.make_id(r['TeeTime']) not in self.previous_search else False
                                                )
                                    )
        return reservations

    def create_html(self):
        new_findings = list(filter(lambda x: x.new == True, self.reservations))
        if len(new_findings) > 0:
            reservations_html = ''
            for r in range(len(new_findings)):
                if r > 0:
                    if new_findings[r].date != new_findings[r - 1].date:
                        reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                else:
                    reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                reservations_html += new_findings[r].render_html()
            self.html = f'<div class="course"><h4>{self.name}</h4><br><div style="width:100%"><img src="{self.img}" height=120/></div><br>{reservations_html}<div style="width:100%"><a href="{self.booking_url}"><div class="reserve_btn">RESERVE!</div></a></div></div>'
        else:
            self.html = ''

    def retrieve_data(self):
        """Parent function to retrieve all reservations for all days and set variable within object"""
        reservations = []
        for d in self.get_list_dates():
            r = requests.post(self.url, self.make_payload(d))
            if r.status_code != 200:
                SNSError('Error fetching data for ' + str(self.name) + '. Contact Gilad Sptizer to debug.')
            else:
                reservations_day = self.parse_data(json.loads(r.content.decode('utf-8'))['Reservations'], d)
                for x in reservations_day:
                    reservations.append(x)
        self.reservations = reservations


class Quick18:
    """Standard Model to accept data for any tee-time website that makes use of the quick18 software."""
    def __init__(self, row, name, url, days, players, course_id, days_out, price_class, previous_search, img, tod):
        self.row = row
        self.name = name
        self.url = url.split('/teetimes')[0] + '/teetimes/searchmatrix'
        self.days = days  # ["Sunday", "Saturday", "Monday", "Wednesday", "Thursday", "Friday"]
        self.players = int(players) if int(players) > 0 and int(players) < 5 else 4
        self.course_ids = int(course_id) if len(course_id.split(',')) < 2 else 0 # 321, 341
        self.days_out = int(days_out)  # 10 or "10"
        self.time_day = tod
        self.price = int(price_class) - 1 if int(price_class) > 0 else None
        self.previous_search = [int(x) for x in json.loads(previous_search)] if len(previous_search) > 0 else []
        self.reservations = []
        self.html = ''
        self.img = img if img != '0' else 'https://teetimenotifier.s3-us-west-1.amazonaws.com/teetimenotifier.png'
        self.booking_url = url

        self.retrieve_data()
        self.create_html()

    def extract_ids(self):
        """Used to create a list of ids for all reservations found for course"""
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        """Returns list of strings (dates) that should be searched (based on how many days out and which days of week"""
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m/%d/%Y'))
        return dates

    def make_payload(self, date):
        """Returns payload for this website type packaged with accompanying data"""
        return {"SearchForm.Date": date,
                "SearchForm.TimeOfDay": str(self.time_day),
                "SearchForm.Players": str(self.players),
                "SearchForm.CourseId": str(self.course_ids)}

    def make_id(self, date):
        """Creates unique id for reservation based on timestamp -- used to keep track of whats new"""
        return int(date.split('/teetime/')[1].split('?')[0])

    def format_date(self, date):
        return datetime.strptime(date,'%m/%d/%Y').strftime('%A') + ' ' + date

    def parse_data(self, html, date):
        """Accepts html found from website and pareses it into list of reservations"""
        soup = bs(html, "html.parser")
        reservations_raw = soup.find(attrs={'class': 'matrixTable'}).find('tbody').find_all('tr')
        reservations = []
        for r in reservations_raw:
            reservations.append(Reservation(course=self.name,
                                            id=self.make_id(r.find(attrs={'class': 'teebutton'})['href']),
                                            date=self.format_date(date),
                                            time=r.find(attrs={'class': 'mtrxTeeTimes'}).get_text().split()[0],
                                            players=r.find(attrs={'class': 'matrixPlayers'}).get_text(),
                                            price=[x.get_text() for x in r.findAll(attrs={'class': 'mtrxPrice'})][self.price] if self.price is not None else [x.get_text() for x in r.findAll(attrs={'class': 'mtrxPrice'})],
                                            subcourse=r.find(attrs={'class': 'mtrxCourse'}).get_text() if r.find(attrs={'class': 'mtrxCourse'}) is not None else self.name,
                                            new=True if self.make_id(r.find(attrs={'class': 'teebutton'})['href']) not in self.previous_search else False
                                            )
                                )
        return reservations

    def create_html(self):
        new_findings = list(filter(lambda x: x.new == True, self.reservations))
        if len(new_findings) > 0:
            reservations_html = ''
            for r in range(len(new_findings)):
                if r > 0:
                    if new_findings[r].date != new_findings[r - 1].date:
                        reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                else:
                    reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                reservations_html += new_findings[r].render_html()
            self.html = f'<div class="course"><h4>{self.name}</h4><br><div style="width:100%"><img src="{self.img}" height=120/></div><br>{reservations_html}<div style="width:100%"><a href="{self.booking_url}"><div class="reserve_btn">RESERVE!</div></a></div></div>'
        else:
            self.html = ''

    def retrieve_data(self):
        """Parent function to retrieve all reservations for all days and set variable within object"""
        reservations = []
        for d in self.get_list_dates():
            r = requests.post(self.url, self.make_payload(d))
            if r.status_code != 200:
                SNSError('Error fetching data for ' + str(self.name) + '. Contact Gilad Sptizer to debug.')
            else:
                reservations_day = self.parse_data(r.content, d)
                for x in reservations_day:
                    reservations.append(x)

        self.reservations = reservations


class ForeUp:
    """Standard Model to accept data for any tee-time website that makes use of the foreup software."""
    def __init__(self, row, name, days, players, days_out, schedule_id, booking_class, previous_search, img, booking_url, tod):
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
        self.html = ''
        self.tod = tod
        self.img = img if img != '0' else 'https://teetimenotifier.s3-us-west-1.amazonaws.com/teetimenotifier.png'
        self.booking_url = booking_url

        self.retrieve_data()
        self.create_html()

    def extract_ids(self):
        """Used to create a list of ids for all reservations found for course"""
        ids = []
        for r in self.reservations:
            ids.append(r.id)

        return json.dumps(ids)

    def get_list_dates(self):
        """Returns list of strings (dates) that should be searched (based on how many days out and which days of week"""
        dates = []
        current_day = datetime.now(SF).date()
        for i in range(self.days_out + 1):
            if (current_day + timedelta(days=i)).strftime('%A') in self.days:
                dates.append((current_day + timedelta(days=i)).strftime('%m-%d-%Y'))
        return dates

    def make_payload(self, date):
        """Returns payload for this website type packaged with accompanying data"""
        return self.url + f"time={self.tod}&date%={date}&holes=18&players={self.players}&booking_class={self.b_class}&schedule_id={self.s_id}&specials_only=0&api_key=no_limits"

    def make_id(self, date):
        """Creates unique id for reservation based on timestamp -- used to keep track of whats new"""
        return int(date.replace('-', '').replace(' ', '').replace(':', ''))

    def format_date(self, date):
        return datetime.strptime(date,'%m-%d-%Y').strftime('%A') + ' ' + date

    def parse_data(self, data, date):
        """Accepts html found from website and pareses it into list of reservations"""
        reservations = []
        for r in data:
            reservations.append(Reservation(
                                            id=self.make_id(r['time']),
                                            course=self.name,
                                            date=self.format_date(date),
                                            time=r['time'].split(' ')[1],
                                            players=r['available_spots'],
                                            price=r['guest_green_fee'],
                                            subcourse=r['schedule_name'],
                                            cart_fee=r['guest_cart_fee'] if 'guest_cart_fee' in r.keys() else 0,
                                            new=True if self.make_id(r['time']) not in self.previous_search else False
                                            )
                                )
        return reservations

    def create_html(self):
        new_findings = list(filter(lambda x: x.new == True, self.reservations))
        if len(new_findings) > 0:
            reservations_html = ''
            for r in range(len(new_findings)):
                if r > 0:
                    if new_findings[r].date != new_findings[r - 1].date:
                        reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                else:
                    reservations_html += f'<div style="width:100%"><h4 class="day">{new_findings[r].date}</div>'
                reservations_html += new_findings[r].render_html()
            self.html = f'<div class="course"><h4>{self.name}</h4><br><div style="width:100%"><img src="{self.img}" height=120/></div><br>{reservations_html}<div style="width:100%"><a href="{self.booking_url}"><div class="reserve_btn">RESERVE!</div></a></div></div>'
        else:
            self.html = ''

    def retrieve_data(self):
        """Parent function to retrieve all reservations for all days and set variable within object"""
        reservations = []
        for d in self.get_list_dates():
            r = requests.get(self.make_payload(d))
            if r.status_code != 200:
                SNSError('Error fetching data for ' + str(self.name) + '. Contact Gilad Sptizer to debug.')
            else:
                reservations_day = self.parse_data(json.loads(r.content.decode('utf-8')), d)
                for x in reservations_day:
                    reservations.append(x)

        self.reservations = reservations


class Email:
    def __init__(self, to_addr, subject, html):
        self.to = to_addr
        self.subject = subject
        self.html = html
        self.text = ''
        self.sender = 'bayareateetimes@gmail.com'

        self.send_email()

    def send_email(self):
        message = MIMEMultipart("alternative")
        message["Subject"] = self.subject
        message["From"] = self.sender
        message["To"] = self.to
        part1 = MIMEText(self.text, "plain")
        part2 = MIMEText(self.html, "html")
        message.attach(part1)
        message.attach(part2)

        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.ehlo()
            server.starttls()
            server.login(self.sender, os.environ['MAIL_PASSWORD'])
            server.sendmail(
                self.sender, self.to, message.as_string()
            )


class SNSTextMessage:
    def __init__(self):
        client = boto3.client('sns', region_name='us-west-1', aws_access_key_id=os.environ['AWS_ACCESS'],
                              aws_secret_access_key=os.environ['AWS_SECRET'])
        response = client.publish(
            TopicArn='arn:aws:sns:us-west-1:527232459706:New_TEE_TIMES',
            Message='New Tee Times Found -- Check your email!',
        )


class SNSError:
    def __init__(self, message):
        client = boto3.client('sns', region_name='us-west-1', aws_access_key_id=os.environ['AWS_ACCESS'],
                              aws_secret_access_key=os.environ['AWS_SECRET'])
        response = client.publish(
            TopicArn='arn:aws:sns:us-west-1:527232459706:TeeTimeNotifier_Error',
            Message=message,
        )


