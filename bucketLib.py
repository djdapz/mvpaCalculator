# created by Devon D'Apuzzo

import MySQLdb as mdb
import sys
import cgi
import cgitb
import os
from datetime import datetime
from datetime import timedelta



class Bucket:

    def __init__(self, start_time, interval):
        #NOTE INTERVAL MUST BE IN MINUTESfi
        self.start_time = start_time
        self.end_time = start_time + timedelta(0, interval*60)
        self.heart_rate = None
        self.hr_max = None
        self.hr_min = None
        self.steps = None
        self.calories = None
        self.mvpa_guess = False

    def getInterval(self):
        return  (self.end_time - self.start_time).seconds / 60 #in minutes

    def printRow(self, mode):
        if mode == "table":
            print "<tr>"

            print "<td>"
            print str(self.start_time.month) + '/' + str(self.start_time.day)+ '     ' + str(self.start_time.hour) + ":" + str(self.start_time.minute)
            print "</td>"

            print "<td>"
            print str(self.end_time.month) + '/' + str(self.end_time.day)+ '     ' + str(self.end_time.hour) + ":" + str(self.end_time.minute)
            print "</td>"

            print "<td>"
            print str(self.heart_rate)
            print "</td>"

            print "<td>"
            print str(self.hr_max)
            print "</td>"

            print "<td>"
            print str(self.hr_min)
            print "</td>"

            print "<td>"
            print str(self.steps)
            print "</td>"

            print "<td>"
            print str(self.calories)
            print "</td>"

            print "<td>"
            print str(self.mvpa_guess)
            print "</td>"

            print "</tr>"
        elif mode == "csv":
            print "<p>"

            print (str(self.start_time.month) + '/' + str(self.start_time.day) + '     ' + str(
                self.start_time.hour) + ":" + str(self.start_time.minute)).strip()
            print ","

            print (
            str(self.end_time.month) + '/' + str(self.end_time.day) + '     ' + str(self.end_time.hour) + ":" + str(
                self.end_time.minute)).strip()
            print ","

            print str(self.heart_rate).strip()
            print ","

            print str(self.hr_max).strip()
            print ","

            print str(self.hr_min).strip()
            print ","

            print str(self.steps).strip()
            print ","

            print str(self.calories).strip()
            print ","

            print str(self.mvpa_guess).strip()

            print "</p>"
        elif mode =="quiet":
            return
        else:
            print "MODE UNKNOWN - ROW"


    def printHeader(self, mode):
        if mode =="table":
            print "<tr><th>start_time</th><th>end_time</th><th>hr</th><th>hr_max</th>"
            print "<th>hr_min</th><th>steps</th><th>calories</th><th>guessed_mvpa</th></tr>"
        elif mode =="csv":
            print "<p>start_time, end_time, hr, hr_max, hr_min, steps, calories, guessed_mvpa</p>"
        elif mode == "quiet":
            return
        else:
            print "MODE UNKNOWN - HEADER"


def scaleBuckets(buckets, scale):
    for bucket in buckets:
        if bucket.calories:
            x = bucket.calories
            bucket.calories = x / scale
        if bucket.steps:
            x = bucket.steps
            bucket.steps = x / scale

def labelBuckets(buckets):
    interval = buckets[0].getInterval()
    steps_per_minute_threshold = 90
    steps_threshold = interval * steps_per_minute_threshold
    base_calories_per_minute = 6.08333/5
    calories_threshold = interval * base_calories_per_minute * 5
    hr_threshold = 100
    for bucket in buckets:
        if bucket.steps > steps_threshold:
            bucket.mvpa_guess = True
        elif bucket.calories > calories_threshold:
            bucket.mvpa_guess = True
        elif (bucket.hr_max > hr_threshold) or (bucket.hr_min > hr_threshold) or (bucket.heart_rate > hr_threshold):
            if (bucket.calories > calories_threshold / 1.5) or (bucket.steps > steps_threshold / 2):
                bucket.mvpa_guess = True


def buildOutMissingValues(buckets):
    base_calories_per_minute = 6.08333 / 5
    interval = buckets[0].getInterval()
    resting_heart_rate = 65

    last_max = 0
    last_min = 0
    last_hr = 0

    for bucket in buckets:
        if bucket.steps == None:
            bucket.steps = 0

        if bucket.calories == None:
            bucket.calories = base_calories_per_minute * interval

        if bucket.heart_rate:
            last_hr = bucket.heart_rate
        else:
            if last_hr > resting_heart_rate:
                last_hr -= int(round((last_hr - resting_heart_rate)/2))
            else:
                last_hr += int(round((resting_heart_rate - last_hr) / 2))
            bucket.heart_rate = last_hr

        if bucket.hr_max:
            last_max = bucket.hr_max
        else:
            if last_max > resting_heart_rate:
                last_max -= int(round((last_max - resting_heart_rate) / 2))
            else:
                last_max += int(round((resting_heart_rate - last_max) / 2))
            bucket.hr_max = last_max

        if bucket.hr_min:
            last_min = bucket.hr_min
        else:
            if last_min > resting_heart_rate:
                last_min -= int(round((last_min - resting_heart_rate) / 2))
            else:
                last_min += int(round((resting_heart_rate - last_min) / 2))
            bucket.hr_min = last_min


        #
        # if bucket.hr_max:
        #     last_max = bucket.hr_max
        # else:
        #     bucket.hr_max = last_max
        #
        # if bucket.hr_min:
        #     last_min = bucket.hr_min
        # else:
        #     bucket.hr_min = last_min





def getBuckets(start_time, end_time, uid, db):
    con = mdb.connect('localhost', 'mhealth', 'mhealth', 'mhealthplay')
    cur = con.cursor()

    #todo get uid
    sql_query = "select distinct * from "+db+" where uid = '"+ uid+"';"
    cur.execute(sql_query)
    rows = cur.fetchall()



    interval = 5  # IN MINUTES
    num_buckets = ((end_time - start_time).seconds / (60 * interval) + ((end_time - start_time).days * 24 * 60 * 60 ) / (60 * interval)) + 1 #+1 for safety
    buckets = []

    iterating_time = start_time
    for num in range(num_buckets):
        buckets.append(Bucket(iterating_time, interval))
        iterating_time += timedelta(0, interval * 60)

    for row in rows:
        #map to row
        start_interval = datetime.strptime(row[1], '%I:%M:%S %p %b %d, %Y')
        end_interval  = datetime.strptime(row[2], '%I:%M:%S %p %b %d, %Y')
        start_bucket = datetimeToBucketNumber(start_time, end_time, interval, start_interval)
        end_bucket = datetimeToBucketNumber(start_time, end_time, interval, end_interval)

        if start_bucket == -1 or end_bucket == -1:
            continue

        #handle calories
        if row[3] == 'calories' or row[3] =='steps':
            # print "<ul>"
            # print "<li>"
            # print "num_buckets: " + str(len(buckets))
            # print "</li>"
            # print "<li>"
            # print "start_interval: " + str(start_interval)
            # print "</li>"
            # print "<li>"
            # print "end_interval: " + str(end_interval)
            # print "</li>"
            # print "<li>"
            # print "start_bucket: " + str(start_bucket)
            # print "</li>"
            # print "<li>"
            # print "start_bucket-start_time: " + str(buckets[start_bucket].start_time)
            # print "</li>"
            # print "<li>"
            # print "start_bucket-end_time: " +str(buckets[start_bucket].end_time)
            # print "</li>"
            # print "<li>"
            # print "end_bucket: " + str(end_bucket)
            # print "</li>"
            # print "<li>"
            # print "end_bucket-start_time: " + str(buckets[end_bucket].start_time)
            # print "</li>"
            # print "<li>"
            # print "end_bucket-end_time: " +str(buckets[end_bucket].end_time)
            # print "</li>"
            # print "<li>"
            # print "key: " + str(row[3])
            # print "</li>"
            # print "<li>"
            # print "value: " + str(row[4])
            # print "</li>"
            # for steps and calories it makes sense to map percentages of the attribute to each bucket
            key = row[3]
            value = row[4]

            # print "<ul>"
            if(start_bucket == end_bucket):

                #if they're in the same bucket we can just increment
                incrementBucket(buckets, value, start_bucket, key)

            elif end_bucket - start_bucket == 1:

                totalSeconds = float((end_interval - start_interval).seconds)

                percentageStart = float((buckets[start_bucket].end_time - start_interval).seconds)/ totalSeconds


                percentageEnd = float((end_interval - buckets[end_bucket].start_time).seconds)/ totalSeconds


                incrementBucket(buckets, value*percentageStart, start_bucket, key)


                incrementBucket(buckets, value*percentageEnd, end_bucket, key)

            else:


                totalSeconds = (end_interval - start_interval).seconds
                startSeconds = (buckets[start_bucket].end_time - start_interval).seconds
                endSeconds= (end_interval - buckets[start_bucket].start_time).seconds

                middleBuckets = (buckets[0].end_time - buckets[0].start_time).seconds

                incrementBucket(buckets, value * startSeconds / totalSeconds, start_bucket, key)
                incrementBucket(buckets, value * endSeconds / totalSeconds, end_bucket, key)





                for i in range(start_bucket+1, end_bucket): #Exclude start and end indeces
                    incrementBucket(buckets, value * middleBuckets / totalSeconds, i, key)

        elif row[3] == 'max':
            #Max from an interval will become the maximum for any bucket that it is at least HALF in
            #TODO - consider case that nothing is there
            key = row[3]
            value = row[4]

            if (start_bucket == end_bucket):
                # if they're in the same bucket we can just make it the max
                buckets[start_bucket].hr_max = max(buckets[start_bucket].hr_max, value)


            else:
                percentageOfStart = float((buckets[start_bucket].end_time - start_interval).seconds) / float((end_interval - start_interval).seconds)
                percentageOfEnd = float((end_interval - buckets[end_bucket].start_time).seconds) / float((end_interval - start_interval).seconds)

                if percentageOfStart > .5:
                    buckets[start_bucket].hr_max = max(buckets[start_bucket].hr_max, value)

                if percentageOfEnd > .5:
                    buckets[end_bucket].hr_max = max(buckets[end_bucket].hr_max, value)

                if end_bucket - start_bucket > 1:
                    #if it covers more than just the start and end, populate in-between buckets
                    for i in range(start_bucket + 1, end_bucket):  # Exclude start and end indeces

                        buckets[i].hr_max = max(buckets[i].hr_max, value)

        elif row[3] == 'min':
            # Max from an interval will become the maximum for any bucket that it is at least HALF in
            #TODO - consider case that nothing is there
            key = row[3]
            value = row[4]

            if (start_bucket == end_bucket):

                insertMin(buckets, value, end_bucket)


            else:
                percentageOfStart = float((buckets[start_bucket].end_time - start_interval).seconds) /  float((end_interval - start_interval).seconds)
                percentageOfEnd = float((end_interval - buckets[end_bucket].start_time).seconds) /   float((end_interval - start_interval).seconds)

                if percentageOfStart > .5:
                    insertMin(buckets, value, start_bucket)

                if percentageOfEnd > .5:

                    insertMin(buckets, value, end_bucket)

                if end_bucket - start_bucket > 1:
                    # if it covers more than just the start and end, populate in-between buckets
                    for i in range(start_bucket + 1, end_bucket):  # Exclude start and end indeces
                        insertMin(buckets, value, i)

        elif row[3] == 'average':

            # Average from an interval will become the average for any bucket that it is fully part, average of a bucket that it is touching, or the full average of a bucket that has no average
            # TODO - consider case that nothing is there
            key = row[3]
            value = row[4]

            if (start_bucket == end_bucket):


                # if they're in the same bucket we have to average
                setAverageBucketValue(buckets, interval, start_bucket, key, value, start_interval, end_interval)

            else:


                setAverageBucketValue(buckets, interval, start_bucket, key, value, start_interval, buckets[start_bucket].end_time)
                setAverageBucketValue(buckets, interval, end_bucket, key, value, buckets[end_bucket].start_time, end_interval)

                if end_bucket - start_bucket > 1:
                    # if it covers more than just the start and end, populate in-between buckets
                    for i in range(start_bucket + 1, end_bucket):  # Exclude start and end indeces
                        setAverageBucketValue(buckets, interval, i, key, value,  buckets[i].start_time, buckets[i].end_time)

        else:
            print "ERROR ERROR ERROR, we encountered an unhandled category:     " + row[3]


    return buckets


def datetimeToBucketNumber(start, end, interval, dt):
    if(dt < start):
        return -1
    if(dt > end):
        return -1

    time_elapsed = dt - start

    bucket = time_elapsed.seconds / (interval * 60) + (time_elapsed.days * 24 * 60 * 60 ) / (60 * interval)


    return bucket


def insertMin(buckets, value, bucket):
    if (buckets[bucket].hr_min == None):
        buckets[bucket].hr_min = value
    else:
        buckets[bucket].hr_min =  min(buckets[bucket].hr_min, value)

def incrementBucket(buckets, value, bucket, attribute):
    if (getattr(buckets[bucket], attribute) == None):
        setattr(buckets[bucket], attribute, value)
    else:
        setattr(buckets[bucket], attribute, getattr(buckets[bucket], attribute) + value)

def setAverageBucketValue(buckets, interval, bucketNumber, attribute, value, start_time, end_time):
    #note start and end time are for the times IN THE BUCKET

    bucket_start = buckets[bucketNumber].start_time
    bucket_end = buckets[bucketNumber].end_time

    if(start_time < bucket_start or end_time > bucket_end):
        print "ERR in setAverageBucketValue      start_time:" + str(start_time) + "    end_time: " +str(end_time) + "     bucketNumber"
        return

    if(start_time == bucket_start and end_time == bucket_end):
        percentage = 1
    if(start_time > bucket_start and end_time < bucket_end):
        percentage = float((end_time - start_time).seconds) / float(interval * 60)

    elif(start_time == bucket_start ):
        percentage = float((end_time - bucket_start).seconds) / float(interval * 60)
    elif (end_time == bucket_end):
        percentage = float((bucket_end - start_time).seconds) / float(interval * 60)

    percentage = float((end_time - start_time).seconds) / float(interval * 60)

    current_avg = buckets[bucketNumber].heart_rate

    if (current_avg):
        new_avg = float(current_avg) * (1 - percentage) + float(value) * percentage
    else:
        new_avg = value

    buckets[bucketNumber].heart_rate = new_avg
