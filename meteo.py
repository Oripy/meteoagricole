import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

import locale
locale.setlocale(locale.LC_ALL, 'fr_FR.UTF-8')

from datetime import date, datetime

from urllib.request import urlopen
from bs4 import BeautifulSoup

source = 'https://www.meteo60.fr/previsions-meteo-agricole-cazaux-saves.html'
html = urlopen(source)
soup = BeautifulSoup(html, 'lxml')
pub = soup.find("p", {"class" : "publication"}).find_all("strong", recursive=False)
date_pub = datetime.strptime(pub[1].text, "%A %d %B %Y %Hh TU")

try:
    saved_data = pd.read_pickle("saved.pkl")
except FileNotFoundError:
    print("no previous file")
    saved_data = pd.DataFrame(columns=["Day", "Hour", "RAW_Temp", "RAW_ground_Temp", "RAW_Rain", "RAW_Evaporation", "Date", "Temp", "Temp_surface", "Temp_ground", "Rain", "Evaporation", "published"])

if date_pub in saved_data.published:
    print("no new data")
else:
    data = pd.read_html(source)
    data[0] = data[0].drop(data[0].tail(1).index)
    data[1] = data[1].drop(data[1].tail(1).index)

    print(data[0].columns)
    print(data[1].columns)

    headernames = ['Day', 'Hour', 'RAW_Temp', 'RAW_ground_Temp', 'RAW_Rain', 'RAW_Evaporation']
    # table1 = data[0][['Jour', 'Heure', 'TÂ°C', 'TÂ°C sol surface (0/10cm)***', 'Pluie sur 3h**', 'Evapo. cumul (mm)']]
    table1 = data[0].iloc[:, [0, 1, 2, 8, 5, 6]]
    table1.columns = headernames

    # table2 = data[1][['Jour', 'Heure', 'TÂ°C', 'TÂ°C sol surface (0/10cm)***', 'Pluie sur 3h**']]
    table2 = data[1].iloc[:, [0, 1, 2, 7, 5]]
    table2.columns = headernames[:5]
    table2 = table2.reindex(columns=headernames)

    meteo = pd.concat([table1, table2])

    meteo = meteo.assign(Hour=lambda x:x.Hour.str.extract(r'(^[0-9]*)h'))
    meteo.Hour = meteo.Hour.apply(lambda x: '0'+x if len(x) == 1 else x)

    meteo.Day = date.today().strftime('%Y') + meteo.Day.astype(str)
    meteo['Date'] = pd.to_datetime(meteo[['Day', 'Hour']].astype(str).apply(' '.join, 1), format='%Y%a%d%b %H')

    meteo = meteo.assign(Temp=lambda x:x.RAW_Temp.str.extract(r'(^-?[0-9]*)'))
    meteo.Temp = pd.to_numeric(meteo.Temp)

    meteo = meteo.assign(Temp_surface=lambda x:x.RAW_ground_Temp.str.extract(r'(^-?[0-9]*)'))
    meteo.Temp_surface = pd.to_numeric(meteo.Temp_surface)
    meteo = meteo.assign(Temp_ground=lambda x:x.RAW_ground_Temp.str.extract(r'\((-?[0-9]*)\)'))
    meteo.Temp_ground = pd.to_numeric(meteo.Temp_ground)

    meteo = meteo.assign(Rain=lambda x:x.RAW_Rain.str.extract(r'(^[0-9]*,[0-9]*)'))
    meteo = meteo.assign(Rain=lambda x:x.Rain.str.replace(',', '.').astype(float))
    meteo.Rain = meteo.Rain.cumsum()

    meteo = meteo.assign(Evaporation=lambda x:x.RAW_Evaporation.replace(',', '.').astype(float))

    meteo["published"] = date_pub

meteo = pd.concat([meteo, saved_data])
meteo.to_pickle("saved.pkl")

print(meteo.head())
# meteo.plot(x='Date', y=['Temp', 'Temp_surface', 'Temp_ground']).get_figure().savefig('output.png')

meteo.Evaporation = -meteo.Evaporation

ax1 = plt.subplot(311)
plt.bar(meteo.Date, meteo.Rain)
plt.bar(meteo.Date, meteo.Evaporation)
plt.setp(ax1.get_xticklabels(), visible=False)
ax1.grid(True)

ax2 = plt.subplot(312, sharex=ax1)
plt.plot(meteo.Date, meteo.Temp, ".")
plt.setp(ax2.get_xticklabels(), visible=False)
ax2.grid(True)

ax3 = plt.subplot(313, sharex=ax1)
plt.plot(meteo.Date, meteo.Temp_surface, ".g")
plt.plot(meteo.Date, meteo.Temp_ground, ".r")
plt.setp(ax3.get_xticklabels())
plt.xticks(rotation=45)
ax3.grid(True)
ax3.margins(0)
ax3.xaxis.set_major_locator(mdates.DayLocator(interval=1))
ax3.xaxis.set_major_formatter(mdates.DateFormatter('%a %d %b'))

plt.tight_layout()
plt.show()