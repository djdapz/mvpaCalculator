import MySQLdb as mdb
import sys
import cgi
import cgitb
import os
from datetime import datetime
from datetime import timedelta



class Bucket:

    def __init__(self, start_time, interval):
        #NOTE INTERVAL MUST BE IN MINUTES
        self.start_time = start_time
        self.end_time = start_time + timedelta(0, interval*60)
        self.heart_rate = None
        self.hr_max = None
        self.hr_min = None
        self.steps = None
        self.calories = None

    def printTableRow(self):
        print "<tr>"

        print "<td>"
        print self.start_time
        print "</td>"

        print "<td>"
        print self.end_time
        print "</td>"

        print "<td>"
        print self.heart_rate
        print "</td>"

        print "<td>"
        print self.hr_max
        print "</td>"

        print "<td>"
        print self.hr_min
        print "</td>"

        print "<td>"
        print self.steps
        print "</td>"

        print "<td>"
        print self.calories
        print "</td>"

        print "</tr>"

    def printTableHeader(self):
        print "<tr><th>start_time</th><th>end_time</th><th>hr</th><th>hr_max</th><th>hr_min</th><th>steps</th><th>calories</th></tr>"




def getBuckets(uid = "Fahad"):
    print "<p>in getBuckets()...<p>"
    con = mdb.connect('localhost', 'mhealth', 'mhealth', 'mhealthplay')
    cur = con.cursor()

    #todo get uid
    cur.execute("select distinct * from raw_fit where uid = '"+ uid+"'")
    rows = cur.fetchall()

    print "<p>got rows...<p>"


    now = datetime.now()
    start_time = datetime(now.year, now.month, now.day, 7, 0, 0)
    end_time = datetime(now.year, now.month, now.day, 22, 0, 0)


    # FOR TESTING AND DEMO DATA ONLY REMOVE WHEN LIVE
    start_time = datetime(2017, 2, 19, 20, 0, 0)
    end_time = datetime(2017, 2, 20, 22, 0, 0)


    interval = 5  # IN MINUTES
    num_buckets = (end_time - start_time).seconds / (60 * interval) + ((end_time - start_time).days * 24 * 60 * 60 ) / (60 * interval)
    buckets = []

    iterating_time = start_time

    for num in range(num_buckets):
        buckets.append(Bucket(iterating_time, interval))
        iterating_time += timedelta(0, interval * 60)

    for row in rows:
            #map to row
            #make sure data is in format
            row[0] = row[0].strip()
            row[1] = row[1].strip()
            row[2] = row[2].strip()
            row[3] = row[3].strip()
            start_interval = datetime.strptime(row[1], '%I:%M:%S %p %b %d, %Y')

            end_interval  = datetime.strptime(row[2], '%I:%M:%S %p %b %d, %Y')

            start_bucket = datetimeToBucketNumber(start_time, end_time, interval, start_interval)
            end_bucket = datetimeToBucketNumber(start_time, end_time, interval, end_interval)

            if start_bucket == -1 or end_bucket == -1:
                continue

            #handle calories
            if row[3] == 'calories' or row[3] =='steps':
                # for steps and calories it makes sense to map percentages of the attribute to each bucket
                key = row[3]
                value = row[4]

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

                    middleBuckets = (end_bucket - start_bucket) * interval * 60

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
                    setattr(buckets[start_bucket], key, max(buckets[start_bucket].hr_max,  value))

                else:
                    percentageOfStart = float((buckets[start_bucket].end_time - start_interval).seconds) / float((end_interval - start_interval).seconds)
                    percentageOfEnd = float((end_interval - buckets[end_bucket].start_time).seconds) / float((end_interval - start_interval).seconds)

                    if percentageOfStart > .5:
                        setattr(buckets[start_bucket], key, max(buckets[start_bucket].hr_max, value))

                    if percentageOfEnd > .5:
                        setattr(buckets[end_bucket], key, max(buckets[end_bucket].hr_max, value))

                    if end_bucket - start_bucket > 1:
                        #if it covers more than just the start and end, populate in-between buckets
                        for i in range(start_bucket + 1, end_bucket):  # Exclude start and end indeces
                            setattr(buckets[i], key, max(buckets[i].hr_max, value))

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



    percentage = float((start_time - end_time).seconds) / float(interval * 60)
    current_avg = buckets[bucketNumber].average

    if (current_avg):
        new_avg = float(current_avg) * (1 - percentage) + float(value) * percentage
    else:
        new_avg = value

    buckets[bucketNumber].average = value