# -*- coding: utf-8 -*-
import os
import pygame
import time
from datetime import datetime
import speech_recognition as sr
import openai
from gtts import gTTS
import requests
import json
import RPi.GPIO as GPIO
import threading
from colorama import Fore


print("""made by Lexp or LuscanoDev
___________________________________""")
print("""Projeto
  _____            _                
 |  __ \          | |               
 | |__| |___ _ __ | | _____  ____ _ 
 |  _  // _ \ '_ \| |/ _ \ \/ / _` |
 | | \ \  __/ |_| | |  __/>  < |_| |
 |_|  \_\___| .__/|_|\___/_/\_\__,_| Versão 1.01
            | |                     
            |_|        (Replexa)
___________________________________""")

is_on = False
audio_playing = False
stop_audio = False

# Configurar sua chave da API da OpenAI aqui
openai.api_key = "your_openai_key"

# Configurar o reconhecimento de fala
recognizer = sr.Recognizer()

# Par�metros para as mensagens de inicializa��o
parametros_iniciais = """
Voc� � uma assistente de uma casa, voc� tem que fazer respostas de no m�ximo 60 palavras, caso passe do limite ser� PUNIDO. 
Caso o usu�rio pergunte algo sobre o clima atual voc� s� retorna com ****APENAS**** a palavra 'solicitarclima' 
(tudo em min�sculo e junto), N�O FALE 'Esse � o output: solicitarclima', 'Essa � a resposta: Solicitarclima', 'Resposta:Solicitarclima' ou 'Desculpe, não tenho acesso à temperatura atual. Mas posso buscar essa informação para você. Quer que eu pesquise?' 
(essas foram IAs que foram desativadas por causa da resposta inadequada, N�O seja igual a elas, apenas fale 'solicitarclima'),
 APENAS FALE 'solicitarclima', apenas, se n�o ser� PUNIDO. Caso N�O pergunte algo sobre o clima n�o fale o 'solicitarcima', apenas caso solicite algo sobre o clima. 
N�o, voc� n�o serve apenas para dar o clima, lembre, voc� � uma assistente pessoal, ou seja, caso eu pergunte uma quest�o voc� responda 
com os parametros, o solicitarclima � apenas uma fun��o sua, voc� n�o � dependente disso. Lembre-se, VOC� � A ASSISTENTE, ent�o fale em primeira pessoa, 
NUNCA, EM HIPOTESE ALGUMA FALE, POR EXEMPLO, 'Neste caso, a assistente pode responder: "[RESPOSTA]"', ok? Agora se transforme
 em uma assistente pessoal.  \n \n Esse � o input do usu�rio:"""

clima_url = 'http://api.openweathermap.org/data/2.5/weather?q=Mooca&appid=499db94c35f05bd1034611813169934e&units=metric'

# Pinos dos bot�es
button_pin_start = 26
button_pin_stop = 16

# Configurar o modo do GPIO
GPIO.setmode(GPIO.BCM)

# Configurar os pinos dos bot�es como entrada com pull-up interno
GPIO.setup(button_pin_start, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_pin_stop, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Diret�rio de �udio
audio_directory = "audios"
os.makedirs(audio_directory, exist_ok=True)

# Fun��o para tocar um som
def play_sound(sound_file):
    global audio_playing
    pygame.mixer.init()
    pygame.mixer.music.load(sound_file)
    pygame.mixer.music.play()
    audio_playing = True
    while pygame.mixer.music.get_busy():
        if stop_audio:
            pygame.mixer.music.stop()
            audio_playing = False
            break

# Fun��o para parar a reprodu��o de �udio
def stop_audio_playback():
    global audio_playing
    if audio_playing:
        pygame.mixer.music.stop()
        audio_playing = False

# Fun��o para responder ao pressionamento do bot�o

def button_pressed_callback(channel):
    global is_on, stop_audio
    if channel == button_pin_start:
        print(f"{Fore.YELLOW}Bot�o {channel} pressionado.{Fore.WHITE}")
        is_on = True
    elif channel == button_pin_stop:
        if audio_playing:
            print(f"Bot�o {channel} pressionado. Parando a reprodu��o de �udio.")
            stop_audio = True

# Configurar a detec��o de borda de subida nos pinos dos bot�es
GPIO.add_event_detect(button_pin_start, GPIO.FALLING, callback=button_pressed_callback, bouncetime=300)
GPIO.add_event_detect(button_pin_stop, GPIO.FALLING, callback=button_pressed_callback, bouncetime=300)

def clean_audio_folder():
    while True:
        current_time = time.time()
        for filename in os.listdir(audio_directory):
            file_path = os.path.join(audio_directory, filename)
            if os.path.isfile(file_path) and (current_time - os.path.getctime(file_path)) > 180:  # 180 seconds = 3 minutes
                os.remove(file_path)
        time.sleep(60)  # Check every minute+

# Fun��o para redefinir o estado ap�s um erro ou quando o �udio n�o � compreendido
def reset_state():
    global is_on, stop_audio, audio_playing
    is_on = False
    stop_audio = False
    audio_playing = False
    print(f"{Fore.YELLOW}___________________________________\nEstado redefinido. Pronto para receber um novo comando.\n___________________________________{Fore.WHITE}")

# Criar e iniciar a thread de limpeza
cleaning_thread = threading.Thread(target=clean_audio_folder)
cleaning_thread.daemon = True
cleaning_thread.start()

# Inicializa a conversa com a mensagem do sistema
messages = [
        {
            "role": "system",
            "content": parametros_iniciais
        },
]

print('Aperte o bot�o ON para falar com a IA\nCaso queira parar de falar aperte o bot�o STOP\n___________________________________')

# Loop principal
while True:
    # Aguardar o pressionamento de qualquer bot�o ou comando de voz
    while not is_on:
        time.sleep(0.1)

    if stop_audio:
        stop_audio_playback()
        reset_state()
    elif audio_playing:
        pass
    else:
        
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source)
            try:
                print(f"{Fore.YELLOW}Aguardando entrada do usu�rio...{Fore.WHITE}")
                play_sound("wakeup_sound.mp3")
                audio = recognizer.listen(source, timeout=2)
                user_message = recognizer.recognize_google(audio, language='pt-BR')
            except sr.UnknownValueError:
                user_message = None
                print(f"{Fore.RED}N�o foi poss�vel entender o �udio.{Fore.WHITE}")
                reset_state()  # Redefinir o estado se o �udio n�o for compreendido

        if user_message:
            print(f"{Fore.GREEN}Usu�rio: {user_message}{Fore.WHITE}")

            messages.append({"role": "user", "content": user_message})

            # Chame a API da OpenAI para obter uma resposta
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

            # Obtenha a mensagem da assistente da resposta
            assistant_message = response['choices'][0]['message']['content']
            print(f"{Fore.BLUE}Assistente: {assistant_message}{Fore.WHITE}")

            # Adicione a mensagem da assistente � conversa
            messages.append({"role": "assistant", "content": assistant_message})

            # Exemplo de como lidar com a resposta da assistente
            if "solicitarclima" in assistant_message.lower():
                print(f"{Fore.YELLOW}Solicitando informa��es de clima...{Fore.WHITE}")
                clima_json = requests.get(url=clima_url)
                clima_data = json.loads(clima_json.text)
                temperatura = clima_data.get("main", {}).get("temp")
                if temperatura is not None:
                    assistant_message = f"A temperatura atual é {temperatura}º."

            # Crie um arquivo de �udio a partir da resposta com um carimbo de data/hora �nico
            language = 'pt-br'
            tts = gTTS(text=assistant_message, lang=language, slow=False)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            audio_file = f"audios/response_{timestamp}.mp3"

            play_sound("ok_sound.mp3")

            tts.save(audio_file)

            # Reproduza o arquivo de �udio com o pygame
            play_sound(audio_file)

            reset_state()

        else:
            # Se nenhum comando de voz foi entendido, permita que o usu�rio tente novamente.
            play_sound("error_sound.mp3")
            print("{Fore.RED}Tente falar novamente.{Fore.WHITE}")
            reset_state()
