import machine
import dht
import time
import ssd1306
from incubator import IncubatorController

# Mapeo estricto de GPIOs de acuerdo con las restricciones de silicio (RNF-05)
PIN_DHT22     = 4
PIN_REED      = 5
PIN_HEATER    = 18
PIN_HUMID     = 19
PIN_BUZZER    = 23
PIN_LED_ERR   = 25
PIN_LED_HEAT  = 26
PIN_I2C_SDA   = 21
PIN_I2C_SCL   = 22

# Inicialización de hardware de comunicación (Bus I2C a 400kHz rápido)
try:
    i2c_bus = machine.I2C(0, scl=machine.Pin(PIN_I2C_SCL), sda=machine.Pin(PIN_I2C_SDA), freq=400000)
    display = ssd1306.SSD1306_I2C(128, 64, i2c_bus)
except Exception:
    display = None # Previene fallas críticas si el bus físico I2C no responde

# Inicialización de instancias de control
sensor_dht = dht.DHT22(machine.Pin(PIN_DHT22))
system = IncubatorController(PIN_REED, PIN_HEATER, PIN_HUMID, PIN_BUZZER, PIN_LED_ERR, PIN_LED_HEAT)

# Temporizadores cíclicos para multitarea apropiativa por software
last_sampling_time = 0
last_display_time = 0

# Variables globales para retener datos seguros frente a caídas de checksum
current_valid_temp = 36.0
current_valid_hum = 50.0

def update_hmi(temp, hum, alarm, door):
    """ RF-08: Renderizado gráfico en pantalla OLED SSD1306 """
    if display is None:
        return
        
    display.fill(0)
    display.text("INCUBADORA UNAL", 0, 0)
    display.text("----------------", 0, 10)
    
    # Explotación de la FPU matemática nativa del ESP32 para strings (RNF-08)
    display.text("Temp: {:.1f} C".format(temp), 0, 24)
    display.text("Hum : {:.1f} %".format(hum), 0, 38)
    
    # Despliegue dinámico de cadenas de alerta de bioseguridad
    if alarm:
        display.text("!BRECHA CRITICA!", 0, 54)
    elif door == 1:
        display.text("PUERTA ABIERTA", 0, 54)
    else:
        display.text("ESTADO: NORMAL", 0, 54)
        
    display.show()

def main_loop():
    global last_sampling_time, last_display_time, current_valid_temp, current_valid_hum
    
    # Mensaje inicializador de hardware
    if display:
        display.fill(0)
        display.text("INICIANDO FIRMWARE", 0, 20)
        display.text("Sistemas Biom.", 0, 35)
        display.show()
    time.sleep(2) # Tiempo técnico requerido para la estabilización del ASIC del DHT22
    
    while True:
        # Monitoreo de alta frecuencia para el sensor magnético (Garantiza los 50ms exactos)
        system.process_door_sensors()
        
        current_millis = time.ticks_ms()
        
        # RF-03: Período de Adquisición Nativa de Datos cada 2.0 segundos
        if time.ticks_diff(current_millis, last_sampling_time) >= 2000:
            try:
                # Dispara la solicitud del pulso de inicio en el bus monohilo 1-Wire
                sensor_dht.measure()
                
                # Si los 40 bits son íntegros, extrae los floats decodificados por hardware
                current_valid_temp = sensor_dht.temperature()
                current_valid_hum = sensor_dht.humidity()
                
                # Ejecuta la matriz de control homeostático
                system.execute_homeostasis(current_valid_temp, current_valid_hum)
                
            except OSError:
                """ RF-04: Gestión Crítica ante Fallas de Estructura de Datos (Checksum)
                El driver de MicroPython verifica internamente los bits y lanza un 
                OSError si la suma no coincide. Congelamos las salidas térmicas de forma segura
                para evitar oscilaciones descontroladas por ruido electromagnético. """
                system.heater.value(0)
                system.led_heat.value(0)
                system.led_err.value(1) # Forzar indicador físico de fallo
                
                if display:
                    display.fill(0)
                    display.text("ERR: BUS 1-WIRE", 0, 15)
                    display.text("Falla Checksum", 0, 30)
                    display.text("Lazo Congelado", 0, 45)
                    display.show()
                # Salta el ciclo de control actual reteniendo las variables anteriores
                last_sampling_time = time.ticks_ms()
                continue 
                
            last_sampling_time = time.ticks_ms()
            
        # Refresco asíncrono de la pantalla OLED (cada 200 ms) para no sobrecargar el bus I2C
        if time.ticks_diff(current_millis, last_display_time) >= 200:
            update_hmi(current_valid_temp, current_valid_hum, system.alarm_active, system.stable_door_state)
            last_display_time = time.ticks_ms()
            
        # RNF-08: Retardo mínimo de descanso del procesador (1ms) para evitar disparos del WDT 
        time.sleep_ms(1)

if __name__ == "__main__":
    main_loop()