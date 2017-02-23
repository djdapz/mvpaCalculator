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

#
# Good grief, we have to generate our own headers?  Crazy.
#
print 'Content-type: text/html\n\n'

form = cgi.FieldStorage()

con = None

if os.environ['REQUEST_METHOD'] == 'POST':
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
            start_time = datetime.strptime(form.getvalue("end_time"), '%I:%M:%S %p %b %d, %Y')




        try:


            # FOR TESTING AND DEMO DATA ONLY REMOVE WHEN LIV
            start_time = datetime(2017, 2, 19, 20, 0, 0)
            end_time = datetime(2017, 2, 20, 22, 0, 0)
            buckets = bucketLib.getBuckets(start_time, end_time, uid=uid)
            bucketLib.buildOutMissingValues(buckets)
            bucketLib.labelBuckets(buckets)
            interval = buckets[0].getInterval()

            if mode == "table":
                print "<table>"
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
                bucket.printRow(mode)
            if mode == "table":
                print "</table>"

            print "<h2>calories sum: " + str(calories_sum) + "</h2>"
            print "<h2>step_sum : " + str(step_sum) + "</h2>"
            print "<h2>mvpa_sum : " + str(mvpa_sum) + "</h2>"

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
