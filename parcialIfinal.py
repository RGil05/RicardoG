# -*- coding: utf-8 -*-
"""
Created on Mon Apr  7 18:36:35 2025

@author: rgil0
"""

import tkinter as tk
import requests
from pyfirmata import Arduino, util

# === Configuración de Arduino ===
arduino_port = "COM3"  # Cambia esto según tu configuración
board = Arduino(arduino_port)
it = util.Iterator(board)
it.start()

# Pines del joystick
x_pin = board.get_pin('a:3:i')  # Eje Y
y_pin = board.get_pin('a:2:i')  # Eje X
x_pin.enable_reporting()
y_pin.enable_reporting()

# Dirección IP de la Raspberry Pi Pico W
pico_ip = "192.168.94.40"  # Cambia esta IP por la tuya
ultimo_comando = None

# === Lógica de envío de comandos ===
def enviar_comando(comando):
    global ultimo_comando
    if comando != ultimo_comando:
        try:
            url = f"http://{pico_ip}/{comando}"
            response = requests.get(url, timeout=1)
            if response.status_code == 200:
                print(f"Comando {comando} enviado")
            else:
                print(f"Error al enviar {comando}: {response.status_code}")
        except Exception as e:
            print(f"Error de conexión: {e}")
        ultimo_comando = comando

# === Zona muerta y movimiento ===
zona_muerta = 0.3
umbral_mov = 0.7
bloqueo_movimiento = False
limite_seguridad = 20  # cm

# === Actualización por joystick ===
def actualizar_joystick():
    x_val = x_pin.read()
    y_val = y_pin.read()

    if x_val is not None and y_val is not None:
        x = x_val * 2 - 1
        y = y_val * 2 - 1

        if abs(x) < zona_muerta and abs(y) < zona_muerta:
            enviar_comando("detener")
        else:
            if abs(y) > abs(x):
                if y > umbral_mov:
                    if not bloqueo_movimiento:
                        enviar_comando("adelante")
                    else:
                        enviar_comando("detener")
                elif y < -umbral_mov:
                    enviar_comando("atras")
                else:
                    enviar_comando("detener")
            else:
                if not bloqueo_movimiento:
                    if x > umbral_mov:
                        enviar_comando("girar_derecha")
                    elif x < -umbral_mov:
                        enviar_comando("girar_izquierda")
                    else:
                        enviar_comando("detener")
                else:
                    enviar_comando("detener")

    root.after(100, actualizar_joystick)

# === Verificación de distancia ===
def verificar_distancia():
    global bloqueo_movimiento
    try:
        url = f"http://{pico_ip}/distancia"
        response = requests.get(url, timeout=1)
        if response.status_code == 200:
            data = response.text
            if "Distancia" in data:
                distancia = int(data.split(":")[1].replace("cm", "").strip())
                print(f"Distancia detectada: {distancia} cm")

                if distancia < limite_seguridad:
                    bloqueo_movimiento = True
                    mostrar_alerta_canvas()
                else:
                    bloqueo_movimiento = False
                    ocultar_alerta_canvas()
    except Exception as e:
        print(f"Error leyendo distancia: {e}")

    root.after(500, verificar_distancia)

# === Ventana de alerta canvas ===
alerta_canvas = tk.Canvas(width=500, height=100, bg="#fa0202", highlightthickness=4, highlightbackground="#000000")
alerta_texto = alerta_canvas.create_text(250, 50, text="¡PELIGRO! Objeto muy cerca", fill="#ffffff", font=("Arial", 20, "bold"))

def mostrar_alerta_canvas():
    if not alerta_canvas.winfo_ismapped():
        alerta_canvas.place(x=50, y=50)

def ocultar_alerta_canvas():
    if alerta_canvas.winfo_ismapped():
        alerta_canvas.place_forget()

# === Control por teclado ===
def manejar_tecla(event):
    tecla = event.keysym.lower()
    if tecla == "w":
        if not bloqueo_movimiento:
            enviar_comando("adelante")
        else:
            enviar_comando("detener")
    elif tecla == "s":
        enviar_comando("atras")
    elif tecla == "a":
        if not bloqueo_movimiento:
            enviar_comando("girar_izquierda")
        else:
            enviar_comando("detener")
    elif tecla == "d":
        if not bloqueo_movimiento:
            enviar_comando("girar_derecha")
        else:
            enviar_comando("detener")
    elif tecla == "space":
        enviar_comando("detener")

# === Salida segura ===
def cerrar():
    board.exit()
    root.destroy()

# === Interfaz principal ===
root = tk.Tk()
root.title("Control del Carrito (Joystick + WASD)")
root.geometry("600x300")
root.configure(bg="#f0f0f0")

titulo = tk.Label(
    root,
    text="Control del Carrito",
    font=("Comic Sans MS", 20, "italic bold underline"),
    fg="#800080", bg="#D3D3D3",
    relief="groove", bd=3, width=30
)
titulo.pack(pady=20)

btn_cerrar = tk.Button(root, text="Cerrar", font=("Arial", 14), command=cerrar, bg="#aa2929", fg="white")
btn_cerrar.pack(pady=10)

# Vincular eventos de teclado
root.bind("<KeyPress>", manejar_tecla)

# Iniciar bucles
actualizar_joystick()
verificar_distancia()
root.mainloop()
