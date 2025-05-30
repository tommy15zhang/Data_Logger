# Data_Logger

# Application Perspective

Different plants have different perferred temperature and humidity. We can fetch a list of plants and let the farmer to choose which plants they want, and place the data logger near the plant. We also provide advice to what to do, like turn on the heater or remove the heater. 

Also another interesting mode is to run the arduino for a specific amount of time, and then generate a report in pdf

Data will be sent from the Arduino to the computer in this order

Temp = ,

Humidity = ,

Air_quality = ,

quality = , 

Avg_temp = ,

Avg_humidity = ,

Avg_air_qual = ,

Temp_too_low = ,

Temp_too _high = ,

Humidity_too_low = ,

Humidity_too_high = ,

Air_quality_poor =


for quality, it gives a 0,1,2,3 value where

FORCE_SIGNAL   = 0;
HIGH_POLLUTION = 1;
LOW_POLLUTION = 2;
FRESH_AIR = 3;

I'm not sure what force_signal is but I believe also high pollution. I could try converting this to be bad okay good that is sent but sending as a flag that is then processed after would be more efficient in terms of data.



It is also worth considering what we want the flags could be. It can be either the values being too high/low or the changes that need to be made. These are mostly the same though tbh

The first values are actual values and the last 5 will be a flag where it indicates any issue with the current environment

The actual data will look like this

25,67,40,22,50,38,0,0,1,0,1
