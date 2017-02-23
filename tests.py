
import pandas
import bucketLib


print "<p>entering getBuckets()...<p>"
rows = pandas.read_csv('dataset.csv')
rows = rows.values.tolist();
del rows[-1]
buckets = bucketLib.getBuckets(rows=rows)
print "<p>got buckets...<p>"
buckets[0].printTableHeader()
for bucket in buckets:
    bucket.printTableRow()

