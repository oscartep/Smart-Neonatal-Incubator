# Smart Neonatal Incubator

Low-cost neonatal incubator based on ESP32 for real-time temperature and humidity monitoring, automated environmental control and safety alerts.

## Overview

This project presents the design and implementation of a smart neonatal incubator prototype developed using an ESP32 microcontroller.

The system monitors temperature, humidity and door status in real time, providing automatic environmental control and safety alerts through visual and audible indicators.

The objective is to provide a low-cost technological solution capable of maintaining a controlled microclimate suitable for neonatal care.

## Main Features

- Real-time temperature monitoring
- Real-time humidity monitoring
- Automated heater control
- Automated humidifier control
- OLED display interface
- Door monitoring system
- Visual alarm indicators
- Audible alarm system
- Electrical isolation for power stages
- ESP32-based architecture

## Hardware Components

- ESP32-WROOM-32
- DHT22 Temperature and Humidity Sensor
- SSD1306 OLED Display
- Reed Switch Door Sensor
- Relay Module
- 4N25 Optocoupler
- Piezoelectric Buzzer
- Status LEDs
- LM2596 Buck Converter
- AMS1117 3.3V Regulator

## Project Structure

```text
docs/
firmware/
hardware/
simulation/
images/
