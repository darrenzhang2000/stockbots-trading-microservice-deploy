import datetime
# BDay is business day, not birthday...
from pandas.tseries.offsets import BDay

today = datetime.datetime.today()
day1Before = today - BDay(1)
day2Before = today - BDay(2)
day3Before = today - BDay(3)
day4Before = today - BDay(4)
day5Before = today - BDay(5)



print(today)