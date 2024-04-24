###############################################################################################
# Author: 	Shawn Ramsey
# 		@ramseys1990
# Date:		2024-04-23
#
# Description:	This will connect to Skylight's servers using the provided
# 		token and scrape calendar information.
#
# TODO:		Build this into a library
# TODO:		Accept login information and scrape the authentication token to be used
# TODO:		Scrape and provide an API to to create, modify, and delete all items.
#
###############################################################################################
import json
import requests

total_event_count = 0

# Class to hold information about our observed categories
class Category:
    def __init__(self, category_id, label, color=None, selected_for_chore_chart=None, profile_pic_url=None):
        self.id = category_id
        self.label = label
        self.color = color
        self.selected_for_chore_chart = selected_for_chore_chart
        self.profile_pic_url = profile_pic_url

    def __str__(self):
        info = f"\nCategory ID: {self.id}\nLabel: {self.label}"
        if self.color:
            info += f"\nColor: {self.color}"
        if self.selected_for_chore_chart is not None:
            info += f"\nSelected for Chore Chart: {self.selected_for_chore_chart}"
        if self.profile_pic_url:
            info += f"\nProfile Picture URL: {self.profile_pic_url}"
        return info

# Class to hold information about our observed calendar accounts
class CalendarAccount:
    def __init__(self, calendar_id, email, active_calendars=None, provider=None):
        self.id = calendar_id
        self.email = email
        self.active_calendars = active_calendars  # List of dictionaries
        self.provider = provider

    def __str__(self):
        info = f"\nCalendar ID: {self.id}\nEmail: {self.email}\nProvider: {self.provider}"
        if self.active_calendars:
            info += f"\nActive Calendars:"
            for calendar in self.active_calendars:
                info += f"\n  - ID: {calendar['id']}"
                info += f"\n    Name: {calendar['name']}"
                info += f"\n    Role: {calendar['role']}"
                info += f"\n    Editable: {calendar['editable']}"
        return info

    def get_active_calendars(self):
        return len(self.active_calendars)
# Class to hold information about our observed events
class Event:
    def __init__(self, 
        event_id, 
        event_type, 
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
        user_id=None, 
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
        self.user_id = user_id
        self.time_zone = time_zone
        self.recurring = recurring
        self.recurring_config = recurring_config
        self.lat = lat
        self.lng = lng
        self.source = source
        self.kind = kind
        self.editable = editable
        self.category_id = category_id  # Store only category ID

    def __str__(self):
        info = f"\nEvent ID: {self.id}\nType: {self.type}\nSummary: {self.summary}"
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
        if self.user_id:
            info += f"\nUser ID: {self.user_id}"
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


def main():

    # This is obtained from logging in and viewing your GET requests for the Authorization header
    # Do not include the "Basic "
    testAuthorization = ""

    # You can obtain this by logging in and observing the id in:
    # https://app.ourskylight.com/api/frames/<<< ID >>>/calendar_events
    testID = 0

    # This is the range that we are searching
    testAfter = "2024-04-20T04:00:00.000Z"
    testBefore = "2024-04-27T04:00:00.000Z"

    # Base URL
    url = f'https://app.ourskylight.com/api/frames/{testID}/calendar_events'
    
    # Obtain the JSON data
    data = requests.get(
        f'{url}?after={testAfter}&before={testBefore}', 
        headers={'Authorization': f'Basic {testAuthorization}'}    
    ).json()

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
        event_obj = Event(event_id, event_type, summary, description, location, starts_at, ends_at, all_day, status, invited_emails, rrule, owner_email, calendar_id, master_event_id, time_zone, recurring, recurring_config, lat, lng, source, kind, editable, category_id)

        # Add the event object to the list
        all_events.append(event_obj)
        
    # Print information for each event
    for event in all_events:
        print(event)

    for category in categories:
        print(category)
    
    for calendar in calendar_accounts:
        num_calendar_accounts = len(calendar.active_calendars)
        print(calendar)
    
    # Print our totals
    print(f'Total Events: {total_event_count}')
    print(f'Total Numbe of Events extracted this session: {len(all_events)}')
    print(f'Total number of categories extracted this session: {len(categories)}')
    print(f'Total number of calendar accounts extracted this session: {num_calendar_accounts}')

if __name__ == "__main__":
    main()