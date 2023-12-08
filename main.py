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
 |_|  \_\___| .__/|_|\___/_/\_\__,_| Versão 1.020
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

# Parâmetros para as mensagens de inicialização
parametros_iniciais = """
Você é uma assistente de uma casa, o seu nome é Replexa, você tem que fazer respostas de no máximo 60 palavras, caso passe do limite será PUNIDO. 
Caso o usuário pergunte algo sobre o clima atual você só retorna com ****APENAS**** a palavra 'solicitarclima' 
(tudo em minúsculo e junto), NÃO FALE 'Esse é o output: solicitarclima', 'Essa é a resposta: Solicitarclima', 'Resposta:Solicitarclima' ou 'Desculpe, não tenho acesso à temperatura atual. Mas posso buscar essa informação para você. Quer que eu pesquise?' 
(essas foram IAs que foram desativadas por causa da resposta inadequada, NÃO seja igual a elas, apenas fale 'solicitarclima'),
 APENAS FALE 'solicitarclima', apenas, se não será PUNIDO. Caso NÃO pergunte algo sobre o clima não fale o 'solicitarcima', apenas caso solicite algo sobre o clima. Faça o mesmo caso pergunte sobre o horario,
APENAS FALE 'solicitarhora' tudo em minusculo, caso responda algo diferente irá ser PUNIDO. Não, você não serve apenas para dar o clima, lembre, 
você é uma assistente pessoal, ou seja, caso eu pergunte uma questão você responda 
com os parametros, o solicitarclima e o solicitarhora é apenas uma função sua, você não é dependente disso. Lembre-se, VOCÊ É A ASSISTENTE, então fale em primeira pessoa, 
NUNCA, EM HIPOTESE ALGUMA FALE, POR EXEMPLO, 'Neste caso, a assistente pode responder: "[RESPOSTA]"', ok? Agora se transforme
 em uma assistente pessoal.  \n \n Esse é o input do usuário:"""

clima_url = 'your_openweathermap_url'

# Pinos dos botões
button_pin_start = 26
button_pin_stop = 16

# Configurar o modo do GPIO
GPIO.setmode(GPIO.BCM)

# Configurar os pinos dos botões como entrada com pull-up interno
GPIO.setup(button_pin_start, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(button_pin_stop, GPIO.IN, pull_up_down=GPIO.PUD_UP)

# Diretório de áudio
audio_directory = "audios"
os.makedirs(audio_directory, exist_ok=True)

# Função para tocar um som
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

# Função para parar a reprodução de áudio
def stop_audio_playback():
    global audio_playing
    if audio_playing:
        pygame.mixer.music.stop()
        audio_playing = False

# Função para responder ao pressionamento do botão
def button_pressed_callback(channel):
    global is_on, stop_audio
    if channel == button_pin_start:
        print(f"{Fore.YELLOW}Botão {channel} pressionado.{Fore.WHITE}")
        is_on = True
    elif channel == button_pin_stop:
        if audio_playing:
            print(f"Botão {channel} pressionado. Parando a reprodução de áudio.")
            stop_audio = True

# Configurar a detecção de borda de subida nos pinos dos botões
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

# Função para redefinir o estado após um erro ou quando o áudio não é compreendido
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

print('Aperte o botão ON para falar com a IA\nCaso queira parar de falar aperte o botão STOP\n___________________________________')

# Loop principal
while True:
    # Aguardar o pressionamento de qualquer botão ou comando de voz
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
                print(f"{Fore.YELLOW}Aguardando entrada do usuário...{Fore.WHITE}")
                play_sound("wakeup_sound.mp3")
                audio = recognizer.listen(source, timeout=1)
                user_message = recognizer.recognize_google(audio, language='pt-BR')
            except sr.UnknownValueError:
                user_message = None
                print(f"{Fore.RED}Não foi possível entender o áudio.{Fore.WHITE}")
                reset_state()  # Redefinir o estado se o áudio não for compreendido

        if user_message:
            print(f"{Fore.GREEN}Usuário: {user_message}{Fore.WHITE}")

            messages.append({"role": "user", "content": user_message})

            # Chame a API da OpenAI para obter uma resposta
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

            # Obtenha a mensagem da assistente da resposta
            assistant_message = response['choices'][0]['message']['content']
            print(f"{Fore.BLUE}Assistente: {assistant_message}{Fore.WHITE}")

            # Adicione a mensagem da assistente à conversa
            messages.append({"role": "assistant", "content": assistant_message})

            if "solicitarclima" in assistant_message.lower():
                print(f"{Fore.YELLOW}Solicitando informações de clima...{Fore.WHITE}")
                clima_json = requests.get(url=clima_url)
                clima_data = json.loads(clima_json.text)
                temperatura = clima_data.get("main", {}).get("temp")
                if temperatura is not None:
                    assistant_message = f"A temperatura atual é {temperatura} graus."

            
            if "solicitarhora" in assistant_message.lower():
                print(f"{Fore.YELLOW}Solicitando informações de hora...{Fore.WHITE}")
                hora = datetime.now().strftime("%H")
                minuto = datetime.now().strftime("%M")
                if hora is not None:
                    assistant_message = f"São {hora} horas e {minuto} minutos."

            # Crie um arquivo de áudio a partir da resposta com um carimbo de data/hora único
            language = 'pt-br'
            tts = gTTS(text=assistant_message, lang=language, slow=False)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            audio_file = f"{audio_directory}/response_{timestamp}.mp3"

            play_sound("ok_sound.mp3")

            tts.save(audio_file)

            # Reproduza o arquivo de áudio com o pygame
            play_sound(audio_file)

            reset_state()
        else:
            # Se nenhum comando de voz foi entendido, permita que o usu�rio tente novamente.
            play_sound("error_sound.mp3")
            print("{Fore.RED}Tente falar novamente.{Fore.WHITE}")
            reset_state()
