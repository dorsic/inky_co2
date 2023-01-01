import inky_co2
import oswald32bs
import amatic32bs
import amatic96bs
import scd41
import time
import network
import urequests
import wifi_p26 as wifi
from micropython import const

#inky_co2.draw_text("2467", -30, 120, amatic96bs, 2)  # text_len 118
#inky_co2.draw_text("ppm", -155, 120, amatic32bs, 1)  # text_len 37
#inky_co2.draw_text("23.4°C", 95, 56, oswald32bs, 1)  # text_len 98

WARN_LIMIT = 2000
NOTIF_LIMIT = 800
DISPLAY_REFRESH_RATE = 6*60000   # 6 minutes - times 250px is 1500min~1day on chart
WIFI_REFRESH_RATE = 30      # 30 sec - how often data will be send through WiFi
HTTP_HEADERS = {'Content-Type': 'application/json'} 

url = const("http://192.168.1.65:3301/inky_co2")
N = 250
co2s = N*[0]
last_display_refresh = 0

try:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.connect(wifi.secrets['ssid'],wifi.secrets['pw'])
except:
    print("Unable to connect to wifi.")

def append(co2):
    global co2s
    co2s = [co2s[i] for i in range(1, len(co2s))] + [co2]

def draw_chart():
    global co2s
    mi = co2s[-1]
    mx = co2s[-1]
    for v in co2s:
        mi = v if (v < mi and v>0) else mi
        mx = v if v > mx else mx
    if (mx is None) or ((mx-mi) is None) or ((mx-mi) == 0):
        return

    k = 30/(mx-mi)
    last = co2s[-1]
    for i in range(len(co2s)):
        if co2s[i]:
            v = co2s[i]
            c = inky_co2.BLACK
            c = inky_co2.ACCENT if (v > NOTIF_LIMIT and last < WARN_LIMIT) else c
            c = inky_co2.WHITE if (v > NOTIF_LIMIT and last > WARN_LIMIT) else c
            inky_co2.draw_line(250-i, 0, 250-i, round(k*(v-mi)), c)

def display(co2, temp, rhum):
    global co2s
    global last_display_refresh
    if not (co2 or temp):
        return None
    
    if ((time.ticks_ms() - last_display_refresh) < DISPLAY_REFRESH_RATE) \
        and (co2s[-1] and co2 and (abs(co2s[-1]-co2) < 0.1*co2s[-1])):
        return None

    if co2:
        append(co2)
        bkg_colour = inky_co2.ACCENT if co2 >= WARN_LIMIT else inky_co2.WHITE
        co2_text_colour = inky_co2.ACCENT if co2 >= NOTIF_LIMIT else inky_co2.BLACK
        co2_text_colour = inky_co2.WHITE if co2 >= WARN_LIMIT else co2_text_colour
        text_colour = inky_co2.WHITE if co2 >= WARN_LIMIT else inky_co2.BLACK
    else:
        bkg_colour = inky_co2.WHITE
        co2_text_colour = inky_co2.BLACK
        text_colour = inky_co2.BLACK
    if co2 or temp:
        print("Refreshing display")
        inky_co2.clear()
        inky_co2.draw_rectangle(0, 0, 250, 122, bkg_colour, 1)
        inky_co2.draw_text(str(co2), -20, 120, amatic96bs, co2_text_colour)
        inky_co2.draw_text("ppm", -145, 120, amatic32bs, text_colour)
        inky_co2.draw_text(str(round(temp, 1))+"°C", 110, 56, oswald32bs, text_colour)
        inky_co2.draw_text(str(round(rhum)) + "%" , 47, 95, amatic32bs, text_colour)
        draw_chart()
        inky_co2.show()
        last_display_refresh = time.ticks_ms()

def wifi_send(co2, temp, rhum):
    global wlan

    if (co2 is None and temp is None):
        return

    try:
        if not wlan.isconnected():
            print('connecting to network...')
            wlan.connect(wifi.secrets['ssid'], wifi.secrets['pw'])

        if wlan.isconnected():
            r = urequests.post(url, json={"co2": co2, "temp": temp, "rhum": rhum}, headers=HTTP_HEADERS )
            r.close()
    except:
        print("Unable to send data via WiFi")

def main():
    i2c = machine.I2C(1, scl=machine.Pin(19), sda=machine.Pin(18), freq=400000)
    scd = scd41.SCD41(i2c)
    scd.start_periodic_measurement()
    while (True):
        co2, temp, rhum = scd.CO2, scd.temperature, scd.relative_humidity
        print(co2, temp, rhum)
        display(co2, temp, rhum)
        try:
            wifi_send(co2, temp, rhum)
            pass
        except:
            print("No wifi connection")

        time.sleep(WIFI_REFRESH_RATE)

main()


