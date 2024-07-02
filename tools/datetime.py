from datetime import datetime

months = ["January","Feburary","March","April","May","June","July","August","September","October","November","December"]

def dateparse(d: datetime):
    d = d.replace(tzinfo=None)
    diff = datetime.now() - d 
    if diff.days == 0:
        return "Today"
    if diff.days == 1:
        return "Yesterday"
    return "{m} {d}, {y}".format(m=months[d.month-1][:3],d=d.day,y=d.year)

def timeparse(d: datetime):
    #we dont care about 24h users

    h = d.hour%12
    suffix = "AM" if d.hour<12 else "PM"

    return f"{h}:{d.minute} {suffix}"

def datetimeparse(d: datetime):
    "get it?"

    dp = dateparse(d)
    h = "{d} {t}"
    if dp in ("Today", "Yesterday"): h = "{d} at {t}"

    return h.format(d=dp, t=timeparse(d))

    
