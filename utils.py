from datetime import date
# Extract today date
today = date.today()

def getDayOfToday():
    if today.weekday() == 0:
        return 'Monday'
    elif today.weekday() == 1:
        return 'Tuesday'
    elif today.weekday() == 2:
        return 'Wednesday'
    elif today.weekday() == 3:
        return 'Thursday'
    elif today.weekday() == 4:
        return 'Friday'
    elif today.weekday() == 5:
        return 'Saturday'
    else:
        return 'Sunday'