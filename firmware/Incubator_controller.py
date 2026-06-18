import machine
import time

class IncubatorController:
    def __init__(self, pin_reed, pin_heater, pin_humid, pin_buzzer, pin_led_err, pin_led_heat):
        # Inicialización de Pines usando constantes de hardware del ESP32
        self.reed = machine.Pin(pin_reed, machine.Pin.IN, machine.Pin.PULL_UP)
        self.heater = machine.Pin(pin_heater, machine.Pin.OUT)
        self.humidifier = machine.Pin(pin_humid, machine.Pin.OUT)
        self.led_err = machine.Pin(pin_led_err, machine.Pin.OUT)
        self.led_heat = machine.Pin(pin_led_heat, machine.Pin.OUT)
        
        # Configuración del subsistema LEDC del ESP32 para el Cristal Piezoeléctrico (RNF-06)
        # Frecuencia deliberada de 2000Hz (resonancia de cavidad)
        self.buzzer = machine.PWM(machine.Pin(pin_buzzer), freq=2000, duty=0)
        
        # Parámetros Clínicos de Homeostasis (Ambiente Térmico Neutral - ATN)
        self.TEMP_MIN = 35.5
        self.TEMP_MAX = 36.5
        self.HUM_MIN = 40.0
        self.HUM_MAX = 60.0
        
        # Variables de estado internas para algoritmos no bloqueantes
        self.last_reed_raw = 1
        self.stable_door_state = 1  # 0 = Cerrada, 1 = Abierta
        self.last_debounce_time = 0
        self.door_open_timer = 0
        self.alarm_active = False

    def process_door_sensors(self):
        """ RF-05: Algoritmo de Antirrebote por Software (Debounce >= 50ms) """
        current_read = self.reed.value() # Lógica negativa debido a INPUT_PULLUP
        
        if current_read != self.last_reed_raw:
            self.last_debounce_time = time.ticks_ms()
            
        if time.ticks_diff(time.ticks_ms(), self.last_debounce_time) >= 50:
            if current_read != self.stable_door_state:
                self.stable_door_state = current_read
                
                if self.stable_door_state == 1:
                    # Registra el instante exacto en que se vulneró el microclima
                    self.door_open_timer = time.ticks_ms()
                else:
                    # Restablece de forma segura si la puerta fue cerrada
                    self.door_open_timer = 0
                    self.alarm_active = False
                    self.buzzer.duty(0)
                    self.led_err.value(0)
                    
        self.last_reed_raw = current_read
        
        # RF-07: Temporización Crítica de Bioseguridad (\tau = 5s)
        if self.stable_door_state == 1 and self.door_open_timer != 0:
            if time.ticks_diff(time.ticks_ms(), self.door_open_timer) >= 5000:
                self.alarm_active = True
                self.buzzer.duty(512)  # Ciclo de trabajo del 50% exacto para SPL máximo
                self.led_err.value(not self.led_err.value()) # Parpadeo síncrono

    def execute_homeostasis(self, temp, hum):
        """ RF-01, RF-02 y RF-06: Control de lazo cerrado y mitigación por evaporación """
        
        # RF-06: Interrupción inmediata de potencia térmica ante apertura física de cabina
        if self.stable_door_state == 1:
            self.heater.value(0)
            self.led_heat.value(0)
        else:
            # RF-01: Regulación Termodinámica con Histéresis Matemática
            if temp < self.TEMP_MIN:
                self.heater.value(1)     # Cierra el relé (pasa potencia de 12VDC)
                self.led_heat.value(1)   # Indicador visual de transferencia térmica
            elif temp > self.TEMP_MAX:
                self.heater.value(0)     # Abre el relé
                self.led_heat.value(0)
                
        # RF-02: Control Homeostático de Humedad Relativa (Mitigación de pérdida evaporativa)
        if hum < self.HUM_MIN:
            self.humidifier.value(1) # Activa humidificador ultrasónico por acoplamiento fotónico
        elif hum >= self.HUM_MAX:
            self.humidifier.value(0) # Apaga humidificación