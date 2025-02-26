Instalace potřebných balíčků
============================

sudo apt install libgl1
sudo pip3 install numpy scikit-learn 
sudo pip3 install opencv-python imutils


Nahrání certifikátů
===================

Do složky faceid_server nahrajte soubory:

key.pem - soukromý klíč
cert.pem - TLS certifikát
fullchain.pem - řetězec certifikátů CA


Spuštění serveru
================

Běžné spuštění tornado webserveru:

cd faceid_server
sudo python3 faceid_server.py


Webové rozhraní
===============

https://sulis81.zcu.cz/static/index.html

(upravte hostname dle vaší situace)



Pořízení obrázků
================

Obrázky se pořizují prostřednictvím webové kamery a API WebRTC. Po stisknutí
tlačítka "Take picture" se vykoná funkce takepicture() v souboru capture.js.

takepicture()
-------------

Funkce takepicture() vezme obrázek z kamery, zakóduje jej jako Data URL a
pošle pomocí HTTP POST na server, cesta /receive_image.

ReceiveImageHandler
-------------------

Převezme obrázek zakódovaný jako Data URL, rozkóduje jej a výsledek zapíše do
souboru v adresáři images/ , soubor je pojmenovaný podle časové značky.
Pořiďte dostatečné množství obrázků (ideálně více než deset na detekovanou
osobu).


Příprava dat pro FaceID
=======================

Data pro FaceID jsou uložena v podadresáři faceid/dataset . Zde každý
podadresář reprezentuje jednu identitu a obsahuje různé fotografie její tváře.
Obrázky tváří pořízené v předchozím kroku roztřiďte do této adresářové
struktury.


Natrénování FaceID modelu
=========================

cd faceid
./train.sh


Vysvětlení skriptu train.sh:

0) Skript smaže a vytvoří adresář output obsahující dílčí modely
1) Pomocí extract_embeddings.py získá vektorové reprezentace (embeddings)
   tváří uložených v adresáři dataset, k tomu použije model pro detekci tváře
   v adresáři face_detection_model a model pro vektorové reprezentace
   openface_nn4.small2.v1.t7.
2) Natrénování klasifikačního modelu (přiřazení identit z datasetu jednotlivým
   ektorovým reprezentacím) skriptem train_model.py.
3) Pro každý soubor v adresáři images/ provede detekci tváře a rozpoznání
   identity, výstup je uložen jako *_predict.png (skript predict.sh)


Otestování FaceID modelu
------------------------

Nahrajte nové obrázky známých tváří do adresáře images a znovu spusťte
predikci:

./predict.sh images

Můžete zkontrolovat, zda model detekuje tváře správně a případně doplnit další
trénovací data.


Identita unknown
----------------

Při trénování je vhodné zachovat identitu unknown, která reprezentuje všechny
ostatní tváře. Hraje roli catch-all třídy.


Použití natrénovaného modelu v Tornado Handleru
===============================================

Připravený Tornado Handler uložen v souboru recognize_handler.py jako třída
RecognizeImageHandler. Při importu modulu se vytvoří instance detectoru,
extraktoru příznaků a klasifikátorů identit.

Pro načtení v faceid_server.py odstraňte komentáře
#Uncomment aftert training#. Pak se bude handler importovat a přidá se do cest
exportovaných webovou aplikací.

Samotný handler po obdržení POST requestu a dat zakódovaných jako Data URL 
zavolá celý řetězec a na svůj výstup vypíše detekované tváře
jako JSON data s následující strukturou:

 {
    "faces": [
        {
            "bbox": {
                "x1": 332,
                "x2": 428,
                "y1": 128,
                "y2": 260
            },
            "name": "unknown",
            "prob": 0.37358799362923695
        }
    ]
}

kde faces je pole objektů, každý má atributy:

bbox - obdélník, kde se v obrázku nachází tvář
name - identita, které je tvář přiřazena
prob - pravděpodobnost přiřazení identity k tváři


V souboru capture.js je volání handleru (mapován na cestu /recognize) součástí
funkce recognize() a recognizepicture().  Výsledek z handleru se zpracovává
jako JSON funkcí JSON.parse().


Zdroje:
=======

Adrian Rosebrock: OpenCV Face Recognition
https://www.pyimagesearch.com/2018/09/24/opencv-face-recognition/

Taking still photos with WebRTC
https://developer.mozilla.org/en-US/docs/Web/API/WebRTC_API/Taking_still_photos
https://github.com/mdn/samples-server/tree/master/s/webrtc-capturestill


Face-Recognition-using-OpenFace
https://github.com/vishal0143/Face-Recognition-using-OpenFace
