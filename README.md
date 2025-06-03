# Data_Logger

# Application Perspective
run a week long reading, and based on the data, give some suggestion to farmer what plants he/she can plant here.


Different plants have different perferred temperature and humidity. We can fetch a list of plants and let the farmer to choose which plants they want, and place the data logger near the plant. We also provide advice to what to do, like turn on the heater or remove the heater. 

Also another interesting mode is to run the arduino for a specific amount of time, and then generate a report in pdf

Data will be sent from the Arduino to the computer in this format

    
    Serial.print(temp);
    Serial.print(",");
    Serial.print(humidity);
    Serial.print(",");
    Serial.print(quality);
    Serial.print(",");
    Serial.print(tempAverage);
    Serial.print(",");
    Serial.print(humidityAverage);
    Serial.print(",");
    Serial.print(tempTooHigh);
    Serial.print(",");
    Serial.print(tempTooLow);
    Serial.print(",");
    Serial.print(humidityTooLow);
    Serial.print(",");
    Serial.print(humidityTooHigh);
    Serial.print(",");
    Serial.println(airQualityIssue);


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
