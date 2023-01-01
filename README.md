# inky_co2
CO2 sensor (SCD41) with Inky ePaper display attached to Raspberry Pi Pico W

![./images/IMG_9161.jpeg]()
Measures level of CO2 in the air in PPM, temperature and humidity and displays them on a 3-colour ePaper display.
Display is refreshed every 6 minutes or when the CO2 concentration change is greater than 10%.
Internally the CO2 level is measured every 30 sec a communitated over wifi to a log server.
On each display refresh a new bar is added to the bar chart showing the development of CO2 concentration over time.
In steady environment the chart shows 6min * 250px = 1500min ~ 1day of measurements.
New value is added always to the right.

CO2 values are colour-coded showing as
- black when under 800 ppm
- red when between 800 and 2000 ppm
- white on red background then over 2000 ppm.

Everything is set on a custom PCB which is designed for both RPi Pico or RPi Zero.
For RPi Pico a micropython code is attached together with required font files.

### Installation
Install micropython on your RPi Pico W. For brand new Picos, this is already preinstalled.
Copy all files in micropython folder to your Pico. Thonny application or REPL tools can be used.
The main.py file is automaticaly executed upon power-up which contains a neverending ```while True:``` loop.

![./images/IMG_9165.jpeg]()
![./images/IMG_9169.jpeg]()
![./images/IMG_9163.jpeg]()



