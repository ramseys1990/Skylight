This will scrape calendar information from Skylight utilizing the Authorization header obtained after logging in.

This will currently take user input for:

User Email
User Password

It will then login to the Skylight API and generate the proper Auth Token after retrieving the User ID and User Token.

It then retrieves the list of available frames and requests user input as to which frame to extract the calendar information from.
**I currently only have one Skylight Calendar so I do not know what the responses for multiple frames looks like, they may all produce the same data?

It then generates an iCalendar .ics file with the retireved calendar information and displays some statistics about what we extracted.
