from machine import Pin, SPI, I2C, UART
import utime
import math
from ili9341 import Display, color565
from imu import MPU6050
from ds3231 import DS3231_I2C 
from xglcd_font import XglcdFont
from time import sleep
from gps import GPS
import machine

#definimos pines para la pantalla
spi = SPI(1, baudrate=10000000, sck=Pin(18), mosi=Pin(23))
display = Display(spi, dc=Pin(4), cs=Pin(5), rst=Pin(19))
display.clear()

font = XglcdFont('fonts/EspressoDolce18x24.c', 18, 24)

#definimos pines uart para el gps
TX_PIN = 17
RX_PIN = 16

#definimos pines i2c para el mpu
#giroscopio = I2C(0, scl=Pin(12), sda=Pin(14), freq=400000) 

#definimos pines i2c para el ds
reloj = I2C(1,sda=Pin(26), scl=Pin(27))
ds = DS3231_I2C(reloj)

# definimos los pines de los sensores de efecto Hall con resistencia pull-up
HALL_SENSOR_1_PIN = Pin(32, Pin.IN, Pin.PULL_UP)  # Sensor 1
HALL_SENSOR_2_PIN = Pin(25, Pin.IN, Pin.PULL_UP)  # Sensor 2

#definimos los pinnes para el boton resistencia pulldown
BUTTON_PIN = Pin(15, Pin.IN, Pin.PULL_DOWN)

#variables
ciclos = 0                     # Contador de revoluciones
rin = 2035                     # Circunferencia de la rueda en mm (28" rim)
velocidad = 0.0           
distancia = 0.0            
revTimer = 0                 
debounce = 80                  # Tiempo de debounce
cadencia = 0
ultima_cadencia = 0
pulsos_por_segundo = 0


# Variables para manejar el estado del botón
boton_presionado = False
tiempo_presion_boton = 0
   
#configuracion del giroscopio
     
#imu = MPU6050(giroscopio)

#while True:
#  ax = imu.accel.x
#  ay = imu.accel.y
#  az = imu.accel.z
#  gx = imu.gyro.x
#  gy = imu.gyro.y
#  gz = imu.gyro.z
#  t = imu.temperature
  
#configuracion del gps
gps = GPS(TX_PIN, RX_PIN)

#configuracion de los sensores de efecto hall
    #velocidad y distancia

def hallvel(pin):
    global ciclos, distancia, velocidad, revTimer
    if HALL_SENSOR_1_PIN.value() == 1:
        ciclos += 1

        distancia = (rin * ciclos) / 100000 

        # Calcular la velocidad
        tiempoact = utime.ticks_ms()  
        tiempot = tiempoact - revTimer
        if tiempot > 0:
            velocidad = (rin / tiempot) * 3.6  
    
        revTimer = tiempoact
    
HALL_SENSOR_1_PIN.irq(trigger=Pin.IRQ_RISING, handler=hallvel)

    #cadencia

def hall_cadencia(pin):
    global pulsos_por_segundo
    pulsos_por_segundo += 1

HALL_SENSOR_2_PIN.irq(trigger=machine.Pin.IRQ_RISING, handler=hall_cadencia)

#boton pull down

# Botón pull-down
def manejar_boton(pin):
    global boton_presionado, tiempo_presion_boton

    if pin.value() == 1:  # Si el botón está presionado
        if not boton_presionado:  # Si no se había detectado el inicio de la presión
            boton_presionado = True
            tiempo_presion_boton = utime.ticks_ms()  # Guardar el tiempo de inicio
    else:  # Si el botón se ha soltado
        if boton_presionado:  # Si estaba presionado
            # Verificar si se ha mantenido presionado durante más de 2 segundos (2000 ms)
            if utime.ticks_diff(utime.ticks_ms(), tiempo_presion_boton) > 2000:
                reiniciar_valores()  # Reiniciar los valores si se ha mantenido presionado el tiempo suficiente
        boton_presionado = False  # Reiniciar el estado del botón
        
BUTTON_PIN.irq(trigger=machine.Pin.IRQ_FALLING | machine.Pin.IRQ_RISING, handler=manejar_boton)

# Reiniciar valores

# reiniciar valores
def reiniciar_valores():
    global velocidad, distancia, ciclos, cadencia
    velocidad = 0.0
    distancia = 0.0
    ciclos = 0
    cadencia = 0
    pulsos_por_segundo = 0
    print("Valores reiniciados")

# Bucle principal

while True:
    tiempo_actual = utime.ticks_ms()
    
    # Verifica si ha pasado un segundo
    if tiempo_actual - ultima_cadencia >= 1000:
        cadencia = pulsos_por_segundo 
        rpm = cadencia * 60 
    
    # Mostrar los datos en la pantalla
    display.clear()
    t = ds.read_time()
    display.draw_text(0, 0, "Hora: %02x:%02x:%02x" %(t[2],t[1],t[0]), font, color565(255, 255, 255))
    display.draw_text(0, 25, "Velocidad: {:.2f} km/h".format(velocidad), font, color565(255, 255, 255))
    display.draw_text(0, 50, "Distancia: {:.2f} km".format(distancia), font, color565(255, 255, 255))
    display.draw_text(0, 75, "Cadencia: {} RPM".format(rpm), font, color565(255, 255, 255))
    
    pulsos_por_segundo = 0
    ultima_cadencia = tiempo_actual

        
        
    # Pausa breve para evitar sobrecarga
    utime.sleep(1)