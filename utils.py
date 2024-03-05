from datetime import date, datetime
# Extract today date
today = date.today()

def get_day_of_today():
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
    
def convert_timedelta_to_minutes(duration):
    days, seconds = duration.days, duration.seconds
    hours = days * 24 + seconds // 3600
    minutes = (seconds % 3600) // 60
    seconds = (seconds % 60)
    return hours * 60 + minutes

def calculate_late_between_in_and_standard(time_in, standard_time):
    FMT = '%H:%M:%S'
    tdelta = datetime.strptime(time_in, FMT) - datetime.strptime(standard_time, FMT)
    min = convert_timedelta_to_minutes(tdelta)
    if (min <= 0):
        min = 0
    return min