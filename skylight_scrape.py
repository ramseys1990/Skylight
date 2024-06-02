###############################################################################################
# @Author: 	Shawn Ramsey
# 		    @ramseys1990
#           http://www.github.com/ramseys1990
# Date:		2024-04-23
#
# Description:	This will connect to Skylight's servers using the provided
# 		token and scrape calendar information.
#
# TODO:		Build this into a library
# TODO:		Accept login information and scrape the authentication token to be used - DONE
# TODO:		Scrape and provide an API to to create, modify, and delete all items.
#
###############################################################################################
import json
import requests
import base64
import dateutil.parser
from datetime import datetime, timedelta
from icalendar import Calendar, Event, vDatetime

#----------------------------------------------------------------
# SET TO TRUE FOR DEBUGGING
#----------------------------------------------------------------
debug = False

total_event_count = 0
# Base URL
url = 'https://app.ourskylight.com/api'

#----------------------------------------------------------------
# Logger Function
#----------------------------------------------------------------
def logger(text):
    if debug:
        print(text)



#----------------------------------------------------------------
# Class to hold information about our observed categories
#----------------------------------------------------------------
class Category:
    def __init__(self, category_id, label, color=None, selected_for_chore_chart=None, profile_pic_url=None):
        self.id = category_id
        self.label = label
        self.color = color
        self.selected_for_chore_chart = selected_for_chore_chart
        self.profile_pic_url = profile_pic_url

    def __str__(self):
        info = f'\nCategory ID: {self.id}\nLabel: {self.label}'
        if self.color:
            info += f'\nColor: {self.color}'
        if self.selected_for_chore_chart is not None:
            info += f'\nSelected for Chore Chart: {self.selected_for_chore_chart}'
        if self.profile_pic_url:
            info += f'\nProfile Picture URL: {self.profile_pic_url}'
        return info

#----------------------------------------------------------------
# Class to hold information about our observed calendar accounts
#----------------------------------------------------------------
class CalendarAccount:
    def __init__(self, calendar_id, email, active_calendars=None, provider=None):
        self.id = calendar_id
        self.email = email
        self.active_calendars = active_calendars  # List of dictionaries
        self.provider = provider

    def __str__(self):
        info = f"\nCalendar ID: {self.id}\nEmail: {self.email}\nProvider: {self.provider}"
        if self.active_calendars:
            info += "\nActive Calendars:"
            for calendar in self.active_calendars:
                info += f"\n  - ID: {calendar['id']}"
                info += f"\n    Name: {calendar['name']}"
                info += f"\n    Role: {calendar['role']}"
                info += f"\n    Editable: {calendar['editable']}"
        return info

    def get_active_calendars(self):
        return len(self.active_calendars)

#----------------------------------------------------------------
# Class to hold information about our observed events
#----------------------------------------------------------------
class EventInfo:
    def __init__(self, 
        event_id, 
        event_type,
        uid, 
        summary, 
        description=None, 
        location=None, 
        starts_at=None, 
        ends_at=None, 
        all_day=None, 
        status=None, 
        invited_emails=None, 
        rrule=None, 
        owner_email=None, 
        calendar_id=None, 
        master_event_id=None, 
        time_zone=None, 
        recurring=None, 
        recurring_config=None, 
        lat=None, 
        lng=None, 
        source=None, 
        kind=None, 
        editable=None,
        category_id=None):

        self.id = event_id
        self.type = event_type
        self.uid = uid
        self.summary = summary
        self.description = description
        self.location = location
        self.starts_at = starts_at
        self.ends_at = ends_at
        self.all_day = all_day
        self.status = status
        self.invited_emails = invited_emails
        self.rrule = rrule
        self.owner_email = owner_email
        self.calendar_id = calendar_id
        self.master_event_id = master_event_id
        self.time_zone = time_zone
        self.recurring = recurring
        self.recurring_config = recurring_config
        self.lat = lat
        self.lng = lng
        self.source = source
        self.kind = kind
        self.editable = editable
        self.category_id = category_id  # Store only category ID

    # Prints the contained information if called
    def __str__(self):
        info = f"\nEvent ID: {self.id}\nType: {self.type}\nUID: {self.uid}\nSummary: {self.summary}"
        if self.description:
            info += f"\nDescription: {self.description}"
        if self.location:
            info += f"\nLocation: {self.location}"
        if self.starts_at:
            info += f"\nStarts at: {self.starts_at}"
        if self.ends_at:
            info += f"\nEnds at: {self.ends_at}"
        if self.all_day:
            info += f"\nAll day event: {self.all_day}"
        if self.status:
            info += f"\nStatus: {self.status}"
        if self.invited_emails:
            info += f"\nInvited Emails: {', '.join(self.invited_emails)}"
        if self.rrule:
            info += f"\nRRULE: {self.rrule[0]}"
        if self.owner_email:
            info += f"\nOwner Email: {self.owner_email}"
        if self.calendar_id:
            info += f"\nCalendar ID: {self.calendar_id}"
        if self.master_event_id:
            info += f"\nMaster Event ID: {self.master_event_id}"
        if self.time_zone:
            info += f"\nTime Zone: {self.time_zone}"
        if self.recurring is not None:
            info += f"\nRecurring: {self.recurring}"
        if self.recurring_config:
            info += f"\nRecurring Config: {self.recurring_config}"
        if self.lat:
            info += f"\nLatitude: {self.lat}"
        if self.lng:
            info += f"\nLongitude: {self.lng}"
        if self.source:
            info += f"\nSource: {self.source}"
        if self.kind:
            info += f"\nKind: {self.kind}"
        if self.editable is not None:
            info += f"\nEditable: {self.editable}"
        return info

#----------------------------------------------------------------
# Class to hold all of our identified Frames and respective info
#----------------------------------------------------------------
class Frame:

    # Create a Frame object with the data from a JSON structure
    # Accepts a dictionary with the frame information
    def __init__(self, data):
        self.id = data['id']
        self.type = data['type']
        self.attributes = data['attributes']
        self.relationships = data['relationships']
        
        # Extract user information (if available)
        user_data = data['relationships'].get('user', {}).get('data')
        self.user_id = user_data.get('id') if user_data else None
        
        # Extract event notification setting information (if available)
        event_notification_data = data['relationships'].get('event_notification_setting', {}).get('data')
        self.event_notification_info = event_notification_data

        # Extract meta information
        self.meta = data['meta']

        # Extract all frames from a provided JSON string
        # Returns a list of Frame objects, each representing a frame from the provided JSON data
        @staticmethod
        def extract_all_frames(data_string):
            data = json.loads(data_string)
            frames = []
            for frame_data in data['data']:
                frames.append(Frame(frame_data))
            return frames

# ----------------------------------------------------------------
# Handles the Login process
# ----------------------------------------------------------------
class login():
    loggedIn = False
    userId = 0
    userToken = ''
    userEmail = ''
    userPassword = ''
    authToken = ''
    frame_id = []

    def __init__(self):
        userEmail = input('Enter email:')
        userPassword = input('Enter password:')
        r = requests.post(f'{url}/sessions', json={
            'email': userEmail,
            'name':'',
            'phone':'',
            'password': userPassword,
            'resettingPassword':'false',
            'textMeTheApp':'true',
            'agreedToMarketing':'true'
        }).json()

        self.userId = r['data']['id']
        self.userToken = r['data']['attributes']['token']

        self.loggedIn = True
        #logger(r)

    def __str__(self):
        info = 'Login Info: '
        if self.userEmail:
            info+= f'\nUser Email: {self.userEmail}\n'
        if self.userPassword:
            info+= f'\nUser Password: {self.userPassword}\n'
        if self.userId:
            info += f'\nUserId: {self.userId}\n'
        if self.userToken:
            info += f'\nUser Token: {self.userToken}\n'
        if self.authToken:
            info += f'\nAuth Token: {self.authToken}\n'
        if self.frame_id:
            info += f'\nFrames:'
            for frame in self.frame_id:
                info += f'\n{frame}'
        return info

    # Verifies that we have a User ID and returns it    
    def getId(self):
        if self.loggedIn:
            
            logger(f'UserID: {self.userId}')
            return(self.userId)
        else:
            return 'NOT_LOGGED_IN'
    
    # Verifies that we have a token and returns it
    def getToken(self):
        if self.userToken:
            logger(f'UserToken: {self.userToken}')
            return(self.userToken)
        else:
            return 'NOT_LOGGED_IN'
        #if self.loggedIn:

    # Verifies that we have a User ID and User Token then produces an Auth Token
    def getAuthToken(self):
        if self.userId != 0 and self.userToken != '':
            preAuthString = self.userId + ':' + self.userToken
            self.authToken = base64.b64encode(preAuthString.encode())

            logger(f'Auth token: {self.authToken}')
            return self.authToken
        else:
            return 'MISSING_ITEM'

    # Obtains our available frames
    def getFrameInfo(self):
        all_info = []

        # Obtain the JSON data
        data = requests.get(
            f'{url}/frames?show_deleted=true&', 
            headers={'Authorization': f'Basic {self.getAuthToken().decode()}'}    
        ).json()

        for calendar_data in data['data']:
            # Extract frame information
            frame_info = calendar_data['attributes'].copy()
            frame_info['id'] = calendar_data['id']
            frame_info['type'] = calendar_data['type']

            # Extract user information (if available)
            if calendar_data['relationships']['user']['data'] is not None:
                user_info = calendar_data['relationships']['user']['data']
                frame_info['user_id'] = user_info['id']
            else:
                frame_info['user_id'] = None

            # Extract event notification setting information (if available)
            if calendar_data['relationships']['event_notification_setting']['data'] is not None:
                frame_info['event_notification_info'] = calendar_data['relationships']['event_notification_setting']['data']
            # Assuming there's data in event_notification_info, you can extract it here
            else:
                frame_info['event_notification_info'] = None

            # Extract meta information
            frame_info['meta'] = data['meta']

            all_info.append(frame_info)
        return all_info

    # Obtains our available frame ID's
    # TODO: Extract and store this while initially getting Frame info to prevent multiple calls
    def getFrameId(self):
        

        # Obtain the JSON data
        data = requests.get(
            f'{url}/frames?show_deleted=true&', 
            headers={'Authorization': f'Basic {self.getAuthToken().decode()}'}    
        ).json()

        for frame_data in data['data']:
            # Build a list of ID's for available frames
            self.frame_id.append(frame_data['id'])

        return self.frame_id

#------------------------------------------------------------------
# Handles parsing a calendar event form the provided JSON data
# Returns an iCalendar Event object.
#------------------------------------------------------------------
def parse_event(event_data):

    event = Event()
    event.add('summary', event_data['attributes']['summary'])
    event.add('uid', event_data['attributes']['uid'])

    # Extract date/time parts for parsing
    dtstart_str = event_data['attributes']['starts_at'].split('.')[0]
    dtend_str = event_data['attributes']['ends_at'].split('.')[0]

    # Parse date/time strings using datetime
    dtstart = datetime.strptime(dtstart_str, '%Y-%m-%dT%H:%M:%S')
    event.add('dtstart', vDatetime(dtstart))
    
    if event_data['attributes']['all_day']:
        event.add('dtend', vDatetime(dtstart + timedelta(days=1)))
    else:
        dtend = datetime.strptime(dtend_str, '%Y-%m-%dT%H:%M:%S')
        event.add('dtend', vDatetime(dtend))

    # Add location (if available)
    if event_data['attributes'].get('location'):
        event.add('location', event_data['attributes']['location'])

    # Add time zone (already assumed UTC for 'starts_at' and 'ends_at')
    if event_data['attributes'].get('timezone'):
        event.add('tzid', event_data['attributes']['timezone'])
    
    # Add recurrence rule (if available)
    # TODO: Maybe clean this up? 
    if event_data['attributes'].get('recurring'):
        rrule_str = event_data['attributes']['rrule'][0]
        logger(f"Original RRULE: {rrule_str}")

        # Try parsing UNTIL date (assuming YYYYMMDD format)
        try:
            until_date = dateutil.parser.parse(rrule_str.split("UNTIL=")[1][:8])
            # Convert parsed date to datetime object
            until_datetime = until_date.astimezone()  # Assuming local timezone
        except (IndexError, ValueError):
            # No UNTIL= found or invalid date format, keep original format
            until_datetime = None
            pass

        # Update RRULE UNTIL date with the correct ISO8601 format (if valid)
        if until_datetime:
            rrule_str = rrule_str.replace(f"UNTIL={rrule_str.split('UNTIL=')[1]}", f"UNTIL={until_datetime.isoformat()}")

        # Split and convert remaining date strings (if any)
        rrule_formatted = rrule_str.split(';')
        rrule_dict = dict(item.split('=', 1) for item in rrule_formatted)
        logger(f"Modified RRULE: {rrule_str}")
        logger(f"RRULE dictionary: {rrule_dict}")

        # Add UNTIL as datetime to the dictionary (if valid)
        if until_datetime:
            rrule_dict['UNTIL'] = until_datetime

        event.add('rrule', rrule_dict)

    # Add other relevant properties (you can add more based on your needs)
    event.add('description', event_data['attributes'].get('description', ''))
    event.add('created', vDatetime(datetime.now()))
    event.add('last-modified', vDatetime(datetime.now()))
    
    return event

#----------------------------------------------------------------
# Generates an iCalendar string from the provided JSON data
# Returns a Calendar object containing the iCalendar data
#----------------------------------------------------------------
def generate_icalendar(data):

    cal = Calendar()
    cal.add('prodid', '-//skylight-extractor//www.icalendar.com//')
    cal.add('version', '1.0')

    # Process events
    for event_data in data['data']:
        event = parse_event(event_data)
        cal.add_component(event)

    return cal


def main():
    frame_ids = []
    num_calendar_accounts = []

    # Test new login
    AccountInfo = login()

    logger(AccountInfo.getId())
    logger(AccountInfo.getToken())
    logger(AccountInfo.getAuthToken())

    frame_ids = AccountInfo.getFrameId()

    for frame in frame_ids:
        print('Frame ID: ' + frame)

    # This is obtained from logging in and viewing your GET requests for the Authorization header
    # Do not include the "Basic "
    # TODO: Remove this option once the login in finished
    testAuthorization = ''

    # You can obtain this by logging in and observing the id in:
    # https://app.ourskylight.com/api/frames/<<< ID >>>/calendar_events

    # TODO: Extract all frames and iterate through
    frameID = input('Type a frame ID to extract from above: ')
    #frameID = 1600234

    # This is the range that we are searching
    # TODO: Accept input for this
    testAfter = '2020-01-01T00:00:00.000Z'
    testBefore = '2026-12-31T23:59:59.000Z'

    # Base URL
    url = f'https://app.ourskylight.com/api/frames/{frameID}/calendar_events'
    
    # Obtain the JSON data
    data = requests.get(
        f'{url}?after={testAfter}&before={testBefore}', 
        headers={'Authorization': f'Basic {AccountInfo.getAuthToken().decode()}'}    
    ).json()

    # If debug is enabled, dump our retrieved Calendar events JSON data
    if debug:
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    
    # Generate iCalendar data
    ical = generate_icalendar(data)

    # Assuming you have the `ical` object generated from your code
    # Only print if debug is enabled
    if debug:
        with open('output.txt', 'w') as f:
            for event in ical.walk('VEVENT'):
                # Check data type of dtstart, dtend, and other relevant properties)
                print(event['summary'], file=f)
                print(f"dtstart data type: {type(event['dtstart'].dt)}", file=f)
                print(f"dtend data type: {type(event['dtend'].dt)}", file=f)

                # Check other properties as needed
                # if 'rrule' in event:
                #   print(f'rrule data type: {type(event['rrule'].dt)}')

                print('-' * 20, file=f)  # Separator for each event

    # Write iCalendar data to file (replace with your desired filename)
    with open('calendar.ics', 'wb') as f:
        f.write(ical.to_ical())

    print('iCalendar file generated successfully!')

    # Set aside for the events
    events = data['data']

    # Set aside for the includes (Categories and Calendar Accounts)
    included_data = data['included']

    # Go ahead and grab the total number of events
    total_event_count = data['meta']['total_event_count']  # Extract total event count

    # Extract categories
    categories = []
    for item in included_data:
        if item['type'] == 'category':
            category_id = item['id']
            label = item['attributes']['label']
            try:
                color = item['attributes']['color']
            except KeyError:
                color = None
            try:
                selected_for_chore_chart = item['attributes']['selected_for_chore_chart']
            except KeyError:
                selected_for_chore_chart = None
            try:
                profile_pic_url = item['attributes']['profile_pic_url']
            except KeyError:
                profile_pic_url = None
            category_obj = Category(category_id, label, color, selected_for_chore_chart, profile_pic_url)

            # Append this to the list of categories
            categories.append(category_obj)

    # Extract calendar accounts
    # This may be accounts specific to the user logged in?
    # I have not observed other active calendars from family memebers
    calendar_accounts = []
    for item in included_data:
        if item['type'] == 'calendar_account':
            calendar_id = item['id']
            attributes = item['attributes']
            email = attributes['email']
            active_calendars = attributes['active_calendars']
            provider = attributes['provider']
            calendar_obj = CalendarAccount(calendar_id, email, active_calendars, provider)
            
            # Append this to the list of available calendars
            calendar_accounts.append(calendar_obj)

    # Create Event objects and store in a list
    all_events = []
    for event in events:

        # Store all attributes to be moved into a class
        event_id = event['id']
        event_type = event['type']                                      # Example: "calendar_event"
        uid = event['attributes'].get('uid')                            # Example: "from-app-d7a81571fe0e5983a4f8a76d9bbbb7e0-after-1707091200"
        summary = event['attributes'].get('summary')                    # Example: "Free Lunch at Work"
        description = event['attributes'].get('description')            # I have not observed a value here yet
        location = event['attributes'].get('location')                  # A full address
        starts_at = event['attributes'].get('starts_at')                # Example: "2024-04-23T18:00:00.000Z"
        ends_at = event['attributes'].get('ends_at')                    # Example: "2024-04-23T19:00:00.000Z"
        all_day = event['attributes'].get('all_day')                    # True or False
        invited_emails = event['attributes'].get('invited_emails')      # List, I have not observed any emails here yet
        status = event['attributes'].get('status')                      # Example: "approved"
        rrule = event['attributes'].get('rrule')                        # Example: "RRULE:FREQ=WEEKLY;WKST=SU;INTERVAL=1;BYDAY=TU" or "RRULE:FREQ=YEARLY"
        owner_email = event['attributes'].get('owner_email')            # Email of creator
        calendar_id = event['attributes'].get('calendar_id')            # I have not value here yet
        master_event_id = event['attributes'].get('master_event_id')    # I have not value here yet
        time_zone = event['attributes'].get('timezone')                 # Example: "America/New_York"
        recurring = event['attributes'].get('recurring')                # True or False
        recurring_config = event['attributes'].get('recurring_config')  # True or False
        lat = event['attributes'].get('lat')                            # I have not observed a value here yet
        lng = event['attributes'].get('lng')                            # I have not observed a value here yet
        source = event['attributes'].get('source')                      # Example: "skylight" or "ics_link" or "google"
        kind = event['attributes'].get('kind')                          # Example: "standard"
        editable = event['attributes'].get('editable')                  # True, I have not observed False yet

        # Extract category ID (if it exists)
        category_id = None
        if event['relationships'].get('category'):
            category_id = event['relationships']['category']['data']['id']

        # Create Event object
        event_obj = EventInfo(event_id, event_type, uid, summary, description, location, starts_at, ends_at, all_day, status, invited_emails, rrule, owner_email, calendar_id, master_event_id, time_zone, recurring, recurring_config, lat, lng, source, kind, editable, category_id)

        # Add the event object to the list
        all_events.append(event_obj)



    # The logger function checks for the debug flag
    # but for sake of time, we'll check before looping

    # Print information for each event
    if debug:
        for event in all_events:
            logger(event)

    # Print information for each category
    if debug:
        for category in categories:
            logger(category)
    
    # Print information for each calendar
    if debug:
        for i, calendar in enumerate(calendar_accounts):
            num_calendar_accounts[i] = len(calendar.active_calendars)
            logger(calendar)
    
    # Print our totals
    print(f'Total Events: {total_event_count}')
    print(f'Total number of events extracted this session: {len(all_events)}')
    print(f'Total number of categories extracted this session: {len(categories)}')
    for i, calendar in enumerate(calendar_accounts):
        print(f'Total number of calendars within Calender {i}: {len(calendar.active_calendars)}')

if __name__ == '__main__':
    main()