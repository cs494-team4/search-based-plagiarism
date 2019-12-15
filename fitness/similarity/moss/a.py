import mosspy

userid = 650367394

m = mosspy.Moss(userid, "python")


# Submission Files
m.addFile("submission/sample_original.py")
m.addFile("submission/sample_refactored.py")

url = m.send() # Submission Report URL

#print ("Report Url: " + url)

# Save report file
m.saveWebPage(url, "submission/report.html")

# Download whole report locally including code diff links
mosspy.download_report(url, "submission/report/", connections=8)
