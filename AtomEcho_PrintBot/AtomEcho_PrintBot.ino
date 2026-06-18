#include <WiFi.h>
#include <WiFiManager.h>
#include <WiFiUdp.h>
#include <HTTPClient.h>
#include <ArduinoJson.h>
#include <driver/i2s.h>
#include <Preferences.h> // Pour sauvegarder l'IP du PC en mémoire

// --- Libraries requises (à installer via le gestionnaire de bibliothèques Arduino) ---
// 1. ESP8266Audio (par Earle F. Philhower, III)
// 2. ArduinoJson (par Benoit Blanchon)
// 3. WiFiManager (par tzapu)
// 4. FastLED (par Daniel Garcia)

#include <FastLED.h>
#define LED_PIN 27
#define NUM_LEDS 1
CRGB leds[NUM_LEDS];

void setLED(CRGB color) {
  leds[0] = color;
  FastLED.show();
}

#include "AudioFileSourceHTTPStream.h"
#include "AudioGeneratorWAV.h"
#include "AudioOutputI2S.h"

// --- Configuration Serveur Python ---
char SERVER_IP[40] = "10.0.0.30"; // Valeur par défaut, sera modifiée par le portail
const int SERVER_UDP_PORT = 5005;
const int SERVER_HTTP_PORT = 5666;
String VOICE_ID = ""; // Laisse vide pour utiliser la voix par défaut

// --- Configuration Hardware M5Stack ATOM Echo ---
#define BTN_PIN 39

// Pins Microphone PDM (SPM1423)
#define CONFIG_I2S_CLK 33
#define CONFIG_I2S_DATA_IN 23

// Pins Haut-Parleur I2S (NS4168)
#define CONFIG_I2S_BCK 19
#define CONFIG_I2S_LRCK 33
#define CONFIG_I2S_DATA_OUT 22

// --- Variables Globales ---
WiFiUDP udp;
AudioGeneratorWAV *wav = NULL;
AudioFileSourceHTTPStream *file = NULL;
AudioOutputI2S *out = NULL;
Preferences preferences;

bool isRecording = false;

IPAddress serverIPAddress;

void setupI2SMic() {
  // Détruire complètement le haut-parleur (I2S_NUM_1) pour libérer les GPIO partagés
  if (wav != NULL) { delete wav; wav = NULL; }
  if (out != NULL) { out->stop(); delete out; out = NULL; }

  // Délai critique : Laisser le temps à l'ESP32 de libérer physiquement la matrice GPIO
  delay(100);

  i2s_config_t i2s_config = {
    .mode = (i2s_mode_t)(I2S_MODE_MASTER | I2S_MODE_RX | I2S_MODE_PDM),
    .sample_rate = 16000,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format = I2S_CHANNEL_FMT_ALL_RIGHT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags = ESP_INTR_FLAG_LEVEL1,
    .dma_buf_count = 8,
    .dma_buf_len = 256,
    .use_apll = false
  };

  i2s_pin_config_t pin_config;
  pin_config.bck_io_num = I2S_PIN_NO_CHANGE;
  pin_config.ws_io_num = CONFIG_I2S_CLK;
  pin_config.data_out_num = I2S_PIN_NO_CHANGE;
  pin_config.data_in_num = CONFIG_I2S_DATA_IN;
  #if (ESP_IDF_VERSION >= ESP_IDF_VERSION_VAL(4, 3, 0))
    pin_config.mck_io_num = I2S_PIN_NO_CHANGE;
  #endif

  i2s_driver_install(I2S_NUM_0, &i2s_config, 0, NULL);
  i2s_set_pin(I2S_NUM_0, &pin_config);

  // Délai critique : Laisser le temps à l'horloge PDM de démarrer et de stabiliser le micro
  delay(100);
}

void setupI2SSpeaker() {
  // Désinstaller le micro (I2S_NUM_0) pour libérer les GPIO partagés
  i2s_driver_uninstall(I2S_NUM_0);
  
  if (wav != NULL) { delete wav; wav = NULL; }
  if (out != NULL) { delete out; out = NULL; }

  // Délai critique : Libération de la matrice GPIO
  delay(100);

  // Initialiser le haut-parleur sur I2S_NUM_1
  out = new AudioOutputI2S(1, AudioOutputI2S::EXTERNAL_I2S);
  out->SetPinout(CONFIG_I2S_BCK, CONFIG_I2S_LRCK, CONFIG_I2S_DATA_OUT);
  out->SetGain(1.5);
  wav = new AudioGeneratorWAV();
}

void setup() {
  Serial.begin(115200);
  pinMode(BTN_PIN, INPUT_PULLUP);
  
  FastLED.addLeds<WS2812B, LED_PIN, GRB>(leds, NUM_LEDS);
  FastLED.setBrightness(20);
  setLED(CRGB::Black);

  Serial.println("\n--- M5Stack PrintBot ---");

  preferences.begin("printbot", false);
  String saved_ip = preferences.getString("server_ip", "10.0.0.30");
  strcpy(SERVER_IP, saved_ip.c_str());

  WiFiManager wm;
  WiFiManagerParameter custom_server_ip("server", "IP de l'ordinateur Serveur", SERVER_IP, 40);
  wm.addParameter(&custom_server_ip);
  
  Serial.println("Recherche de Wi-Fi...");
  bool res = wm.autoConnect("PrintBot-Config");
  if (!res) {
    Serial.println("Echec de connexion WiFi");
    delay(3000);
    ESP.restart();
  } 
  
  // Desactiver la mise en veille du WiFi pour eviter la perte de paquets UDP !
  WiFi.setSleep(false);
  
  if (String(SERVER_IP) != String(custom_server_ip.getValue())) {
     strcpy(SERVER_IP, custom_server_ip.getValue());
     preferences.putString("server_ip", SERVER_IP);
  }
  
  serverIPAddress.fromString(String(SERVER_IP));
  
  Serial.println("WiFi connecte ! IP du jouet :");
  Serial.println(WiFi.localIP());
  Serial.println("IP du Serveur cible :");
  Serial.println(SERVER_IP);

  Serial.println("Pret ! Maintiens le bouton pour parler.");
  setLED(CRGB::Green); // Prêt à recevoir prompt
  
  Serial.println("Lecture du message de bienvenue...");
  playTTS("/api/greeting");
}

void playTTS(String audioUrl) {
  if (audioUrl.length() < 5) return;
  
  String fullUrl = audioUrl;
  if (!fullUrl.startsWith("http")) {
    fullUrl = "http://" + String(SERVER_IP) + ":" + String(SERVER_HTTP_PORT) + audioUrl;
  }
  
  // Re-initialiser le Haut-Parleur avant de jouer
  setupI2SSpeaker();
  
  Serial.println("Lecture WAV : " + fullUrl);
  file = new AudioFileSourceHTTPStream(fullUrl.c_str());
  
  if (wav->begin(file, out)) {
    while(wav->isRunning()) {
      if (!wav->loop()) {
        wav->stop();
      }
    }
  } else {
    Serial.println("Erreur lecture WAV");
  }
  
  delete file;
  file = NULL;
}

void loop() {
  bool btnState = digitalRead(BTN_PIN);
  
  if (btnState == LOW && !isRecording) {
    // BOUTON APPUYE : DEBUT ENREGISTREMENT
    isRecording = true;
    setLED(CRGB::Red); // Indiquer l'enregistrement en cours
    Serial.println(">>> DEBUT ENREGISTREMENT <<<");
    
    // Configurer I2S_NUM_0 en mode Microphone
    setupI2SMic();
    
    // Purger les premiers tampons (pop noise de l'activation PDM)
    size_t dummy_bytes;
    uint8_t dummy_buf[1024];
    for(int i=0; i<4; i++) {
        i2s_read(I2S_NUM_0, (char*)dummy_buf, 1024, &dummy_bytes, portMAX_DELAY);
    }
  } 
  else if (btnState == LOW && isRecording) {
    // MAINTIEN DU BOUTON : STREAMING UDP I2S
    size_t bytes_read;
    uint8_t i2s_read_buff[1024];
    
    i2s_read(I2S_NUM_0, (char*)i2s_read_buff, 1024, &bytes_read, portMAX_DELAY);
    
    if (bytes_read > 0) {
      udp.beginPacket(serverIPAddress, SERVER_UDP_PORT);
      udp.write(i2s_read_buff, bytes_read);
      udp.endPacket();
    }
  } 
  else if (btnState == HIGH && isRecording) {
    // BOUTON RELACHE : FIN ENREGISTREMENT & SYNC HTTP
    isRecording = false;
    setLED(CRGB::Yellow); // Il pense
    Serial.println(">>> FIN ENREGISTREMENT <<<");
    
    for(int i=0; i<3; i++) {
      udp.beginPacket(serverIPAddress, SERVER_UDP_PORT);
      udp.print("END");
      udp.endPacket();
      delay(20);
    }
    
    Serial.println("Demande de traitement au serveur Python...");
    HTTPClient http;
    String syncUrl = "http://" + String(SERVER_IP) + ":" + String(SERVER_HTTP_PORT) + "/api/device/sync";
    if (VOICE_ID.length() > 0) {
      syncUrl += "?voice_id=" + VOICE_ID;
    }
    
    http.begin(syncUrl);
    http.setTimeout(65000); 
    int httpCode = http.GET();
    
    if (httpCode == 200) {
      String payload = http.getString();
      Serial.println("Reponse Serveur : " + payload);
      
      DynamicJsonDocument doc(2048);
      DeserializationError error = deserializeJson(doc, payload);
      
      if (!error) {
        const char* audio_url = doc["audio_url"];
        const char* state_str = doc["state"];
        const char* action_str = doc["action"];
        
        bool didPrint = false;
        
        if (action_str != nullptr && String(action_str) == "PRINT") {
          setLED(CRGB::Purple); // Il imprime
          didPrint = true;
        } else if (state_str != nullptr) {
          if (String(state_str) == "CONFIRMING") {
            setLED(CRGB::Blue); // Oui ou non
          } else if (String(state_str) == "WAITING_PROMPT") {
            setLED(CRGB::Green); // Prêt
          } else if (String(state_str) == "IDLE") {
            setLED(CRGB::Green); // Prêt aussi par defaut
          }
        }
        
        if (audio_url != nullptr) {
          playTTS(String(audio_url));
        }
        
        // Après avoir parlé, si on vient de lancer une impression, on redevient prêt
        if (didPrint) {
          setLED(CRGB::Green); // Prêt pour l'image suivante
        }
      }
    } else {
      Serial.printf("Erreur HTTP: %d\n", httpCode);
    }
    http.end();
  }

  delay(10);
}