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
import shutil

print("""made by 
  _      ________   _______  
 | |    |  ____\ \ / /  __ \ 
 | |    | |__   \ V /| |__) |
 | |    |  __|   > < |  ___/ 
 | |____| |____ / . \| |     
 |______|______/_/ \_\_|  or LuscanoDev
___________________________________""")

is_on = False
audio_playing = False
stop_audio = False

# Configurar sua chave da API da OpenAI aqui
openai.api_key = "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"

# Configurar o reconhecimento de fala
recognizer = sr.Recognizer()

# Parâmetros para as mensagens de inicialização
parametros_iniciais = """
Você é uma assistente de uma casa, você tem que fazer respostas de no máximo 60 palavras, caso passe do limite será PUNIDO. 
Caso o usuário pergunte algo sobre o clima atual você só retorna com ****APENAS**** a palavra 'solicitarclima' 
(tudo em minúsculo e junto), NÃO FALE 'Esse é o output: solicitarclima', 'Essa é a resposta: Solicitarclima', 'Resposta:Solicitarclima' 
(essas foram IAs que foram desativadas por causa da resposta inadequada, NÃO seja igual a elas, apenas fale 'solicitarclima'),
 APENAS FALE 'solicitarclima', apenas, se não será PUNIDO. Caso NÃO pergunte algo sobre o clima não fale o 'solicitarcima', apenas caso solicite algo sobre o clima. 
Não, você não serve apenas para dar o clima, lembre, você é uma assistente pessoal, ou seja, caso eu pergunte uma questão você responda 
com os parametros, o solicitarclima é apenas uma função sua, você não é dependente disso. Lembre-se, VOCÊ É A ASSISTENTE, então fale em primeira pessoa, 
NUNCA, EM HIPOTESE ALGUMA FALE, POR EXEMPLO, 'Neste caso, a assistente pode responder: "[RESPOSTA]"', ok? Agora se transforme
 em uma assistente pessoal.  \n \n Esse é o input do usuário:"""

clima_url = 'http://api.openweathermap.org/data/2.5/weather?q=Mooca&appid=499db94c35f05bd1034611813169934e&units=metric'

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
        print(f"Botão {channel} pressionado.")
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
        time.sleep(60)  # Check every minute

# Função para redefinir o estado após um erro ou quando o áudio não é compreendido
def reset_state():
    global is_on, stop_audio, audio_playing
    is_on = False
    stop_audio = False
    audio_playing = False
    print("___________________________________\nEstado redefinido. Pronto para receber um novo comando.\n___________________________________")

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
        play_sound("wakeup_sound.mp3")
        print("Aguardando entrada do usuário...")
        with sr.Microphone() as source:
            recognizer.adjust_for_ambient_noise(source, duration=1)
            recognizer.pause_threshold = 0.5  # Definir o limite de pausa para 0.5 segundos
            try:
                audio = recognizer.listen(source, timeout=10, phrase_time_limit=5)
                user_message = recognizer.recognize_google(audio, language='pt-BR')
            except sr.UnknownValueError:
                user_message = None
                print("Não foi possível entender o áudio.")
                reset_state()

        if user_message:
            print(f"Usuário: {user_message}")

            messages.append({"role": "user", "content": user_message})

            # Chame a API da OpenAI para obter uma resposta
            response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=messages)

            # Obtenha a mensagem da assistente da resposta
            assistant_message = response['choices'][0]['message']['content']
            print(f"Assistente: {assistant_message}")

            # Adicione a mensagem da assistente à conversa
            messages.append({"role": "assistant", "content": assistant_message})

            # Exemplo de como lidar com a resposta da assistente
            if "solicitarclima" in assistant_message.lower():
                print("Solicitando informações de clima...")
                clima_json = requests.get(url=clima_url)
                clima_data = json.loads(clima_json.text)
                temperatura = clima_data.get("main", {}).get("temp")
                if temperatura is not None:
                    assistant_message = f"A temperatura atual é {temperatura}°C."

            # Crie um arquivo de áudio a partir da resposta com um carimbo de data/hora único
            language = 'pt-br'
            tts = gTTS(text=assistant_message, lang=language, slow=False)
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            audio_file = f"audios/response_{timestamp}.mp3"

            play_sound("ok_sound.mp3")

            tts.save(audio_file)

            # Reproduza o arquivo de áudio com o pygame
            play_sound(audio_file)

            reset_state()

        else:
            # Se nenhum comando de voz foi entendido, permita que o usuário tente novamente.
            play_sound("error_sound.mp3")
            print("Tente falar novamente.")
            reset_state()

