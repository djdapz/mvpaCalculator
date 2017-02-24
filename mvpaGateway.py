#!/usr/bin/python
# created by Devon D'Apuzzo

import MySQLdb as mdb
import sys
import cgi
import cgitb
import os
from datetime import datetime
from datetime import timedelta
import bucketLib
import json

#
# Good grief, we have to generate our own headers?  Crazy.
#


form = cgi.FieldStorage()

con = None

if os.environ['REQUEST_METHOD'] == 'POST':
        print 'Content-type: text/html\n\n'
        print "Post request received."

        # Create SQL entry
        try:
                print "Connecting to db..."
                con = mdb.connect('localhost', 'mhealth', 'mhealth', 'mhealthplay')
                print "Connected."
                print "Time: " + str(form.getvalue("time"))
                # NOTE: the query string puts the mac address and time
                # parameter in single quotes. Do NOT put the mac parameter
                # in single quotes or the syntax will fail.
                # TODO: sanitize data inputs to avoid injection
                queryString = "INSERT INTO djd_user_goals (" +\
                    "user_id, goal, achieved, day" +\
                    ") VALUES (" +\
                    "'" + str(form.getvalue("user_id")) + "', " +\
                    str(form.getvalue("goal")) +", " +\
                    str(form.getvalue("achieved")) +\
                    str(form.getvalue("goal")) +", " +\
                ");"

                cur = con.cursor()
                print "Executing: " + queryString
                cur.execute(queryString)
                print "Executed."

        except mdb.Error, e:
                print "Error connecting or executing query string."
                print e
        finally:
                if con:
                        con.close()

elif os.environ['REQUEST_METHOD'] == 'GET':





        mode = "csv"
        uid = "Fahad"
        now = datetime.now()
        #end_time = datetime(now.year, now.month, now.day, 22, 0, 0)
        end_time = now
        start_time = datetime(now.year, now.month, now.day, 7, 0, 0)
        special_dates = None


        if form.has_key("mode"):
            mode = form.getvalue("mode")




        if mode == 'api' or mode =='test':
            print 'Content-type: #application/json\n\n'
        else:
            print 'Content-type: text/html\n\n'

        if mode == 'test':
            x = {}
            x['mvpa'] = 100
            print(json.JSONEncoder().encode(x))
            quit()

        if mode == 'api':
            if form.has_key("request"):
                request = form.getvalue("request")
            else:
                x = {}
                x['error'] = "in API mode you need a request field to get data. visit this url for help: http://murphy.wot.eecs.northwestern.edu/~djd809/mvpaGateway.py?help=true "
                print(json.JSONEncoder().encode(x))
                quit()
        else:
            print "<style>"
            print "table{border - collapse: collapse;width: 100 %;}"
            print "th, td{text - align: left;padding: 8px;}"
            print "tr:nth-child(even){background - color:  # f2f2f2}"
            print "th {background - color:  #4CAF50;color: white;}"
            print "</style>"



        if form.has_key("help") and not mode=='api':
            if form.getvalue("help") == "true" or form.getvalue("help") == "True" or form.getvalue("help") == "1":
                print "<h3>MvpaGateway API Help</h3>"
                print "<table>"

                print "<tr><th>QUERY KEY</th><th>REQUIRED</th><th>DEFAULT VALUE</th><th>DETAILS</th></tr>"
                print "<tr><td>uid</td><td>YES</td><td>'Fahad'</td><td>unique username for query</td></tr>"
                print "<tr><td>mode</td><td>YES</td><td>csv</td><td><ul><li>mode = 'csv'--> returns csv like data</li><li>model='table'--> Returns HTML Table</li><li>model='api' --> enteres api mode and returns JSON. use request field to specify what you want</li></td></tr>"
                print "<tr><td>request</td><td>IF MODE = API</td><td>None</td><td><ul><li>request = 'mvpa'--> json with 'mvpa' field</li><li>reuqest='buckets'--> json of all buckets</li></td></tr>"
                print "<tr><td>special_dates</td><td>no</td><td>None</td><td>non-default date settings - use 'original_testing' to pull table from first testing period</td></tr>"
                print "<tr><td>start_time</td><td>no</td><td>Current Day at 7AM</td><td>override default start time. format 'hour:minute:second AM/PM Month(Feb) day, year(4digit)'</td></tr>"
                print "<tr><td>end_time</td><td>no</td><td>Current Day at 10PM</td><td>override default end time. Special values: '10'-10PM today, 'now'-current time or manual: format 'hour:minute:second AM/PM Month(Feb) day, year(4digit)'</td></tr>"
                print "<tr><td>days_ago</td><td>no</td><td>0</td><td>Single number requesting data from x day's ago</td></tr>"
                print "<tr><td>help</td><td>no</td><td>false</td><td>if help='true' or 'True' this table is included in query</td></tr>"
                print "</table>"

        if form.has_key("uid"):
            uid = form.getvalue("uid")

        if form.has_key('special_dates'):
            special_dates = form.getvalue("special_dates")
            if special_dates == "original_testing":
                start_time = datetime(2017, 2, 19, 20, 0, 0)
                end_time = datetime(2017, 2, 20, 22, 0, 0)

        if form.has_key("start_time"):
            start_time = datetime.strptime(form.getvalue("start_time"), '%I:%M:%S %p %b %d, %Y')

        if form.has_key("end_time"):
            end_time_key = form.getvalue("end_time")
            if end_time_key == "10":
                end_time = datetime(now.year, now.month, now.day, 22, 0, 0)
            elif end_time_key == "now":
                end_time = now
            else:
                end_time = datetime.strptime(end_time_key, '%I:%M:%S %p %b %d, %Y')

        if form.has_key("days_ago"):
            start_time -= timedelta(form.getvalue("days_ago"), 0)

        try:

            # FOR TESTING AND DEMO DATA ONLY REMOVE WHEN LIV
            buckets = bucketLib.getBuckets(start_time, end_time, uid=uid)

            bucketLib.buildOutMissingValues(buckets)
            bucketLib.labelBuckets(buckets)
            interval = buckets[0].getInterval()




            if mode == "table":
                print "<h3>MVPA TABLE</h3>"
                print "<table>"
            if not(mode == 'api'):
                buckets[0].printHeader(mode)
            step_sum = 0
            calories_sum = 0
            mvpa_sum = 0

            for bucket in buckets:
                if bucket.steps:
                    step_sum += bucket.steps
                if bucket.calories:
                    calories_sum = bucket.calories + calories_sum
                if bucket.mvpa_guess == True:
                    mvpa_sum += interval

                if not (mode == 'api'):
                    bucket.printRow(mode)
            if mode == "table":
                print "</table>"

            if mode == 'api':

                if request == 'mvpa':
                    x = {}
                    x['mvpa'] = mvpa_sum
                    print (json.JSONEncoder().encode(x))
                elif request == 'buckets':
                    objects = []
                    for bucket in buckets:
                        x = {}
                        x['mvpa_guess'] = str(bucket.mvpa_guess)
                        x['heart_rate'] = str(bucket.heart_rate)
                        x['hr_max'] = str(bucket.hr_max)
                        x['hr_min'] = str(bucket.hr_min)
                        x['calories'] = str(bucket.calories)
                        x['steps'] = str(bucket.steps)
                        x['start_time'] = str(bucket.start_time)
                        x['end_time'] = str(bucket.end_time)
                        objects.append(x)
                    print (json.JSONEncoder().encode(objects))

            else:
                print "<h2>calories sum: " + str(calories_sum) + "</h2>"
                print "<h2>step_sum : " + str(step_sum) + "</h2>"
                print "mvpa_sum : " + str(mvpa_sum)


        except mdb.Error, e:
                print "Error %d = %s<p>" % (e.args[0],e.args[1])
                sys.exit(1)
        #
        # finally:
        if con:
                con.close()

else:
        print "You sent a " + str(os.environ['REQUEST_METHOD']) + \
            " request. This script only works with POST and GET requests."
