# -*- coding: UTF-8 -*-
from tkinter import messagebox
import requests
import urllib
from urllib.parse import unquote
from bs4 import BeautifulSoup
import time
import helper
import re

class eGela:
    _login = 0
    _cookie = ""
    _curso = ""
    _refs = []
    _root = None

    def __init__(self, root):
        self._root = root

    def erantzuna_inprimatu(self, metodoa, uri, erantzuna):
        print("=" * 60)
        print(f"ESKAERA: {metodoa} {uri}")
        print(f"ERANTZUNA: {erantzuna.status_code} {erantzuna.reason}")
        if 'Set-Cookie' in erantzuna.headers:
            print(f"SET-COOKIE: {erantzuna.headers['Set-Cookie']}")
        if 'Location' in erantzuna.headers:
            print(f"LOCATION: {erantzuna.headers['Location']}")

    # Cookie aldatu den konprobatzeko metodoa
    def cookie_aldaketa(self, erantzuna, aurreko_cookie):
        if 'Set-Cookie' in erantzuna.headers:
            return erantzuna.headers['Set-Cookie'].split(';')[0]
        return aurreko_cookie

    # Helbidea aldatu den konprobatzeko metodoa
    def helbide_aldaketa(self, erantzuna, uria):
        if 'Location' in erantzuna.headers:
            return erantzuna.headers['Location']
        print(uria)
        return uria

    def check_credentials(self, username, password, event=None):
        popup, progress_var, progress_bar = helper.progress("check_credentials", "Logging into eGela...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("##### 1. PETICION #####")
        ################################################################
        # Definicion de los campos necesarios para la peticion HTTP
        metodo = "GET"
        uri = "https://egela.ehu.eus/login/index.php"
        goiburua = { "Host": "egela.ehu.eus",}

        # Se envia la primera petición para obtener el logintoken y la cookie de sesión
        erantzuna = requests.request(metodo, uri, headers=goiburua, allow_redirects=False)

        # Se comprueba la respuesta de la primera petición
        if erantzuna.status_code == 200:
            if 'Set-Cookie' in erantzuna.headers:
                self._cookie = erantzuna.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna.headers:
                uri = erantzuna.headers['Location']
        else:
            print(f"Error 1. petición. Respuesta: {erantzuna.status_code} {erantzuna.reason}")
            print("Valor esperado: 200")
            exit(1)

        # Analizamos el HTML de la respuesta para extraer el logintoken
        html_parser = BeautifulSoup(erantzuna.content, "html.parser")
        logintoken = html_parser.find("input", {"name": "logintoken"})["value"]
        ################################################################

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        ################################################################
        # Definicion de los campos necesarios para la peticion HTTP
        metodo = "POST"
        goiburua["Cookie"] = self._cookie
        goiburua["Content-Type"] = "application/x-www-form-urlencoded"

        # Se obtienen los valores de username y password de los campos de texto
        user_val = username.get()
        password_val = password.get()

        edukia = { 'logintoken': logintoken, 'username': user_val, 'password': password_val}
        edukia_form = urllib.parse.urlencode(edukia)
        goiburua["Content-Length"] = str(len(edukia_form))

        # Se envia la segunda petición con las credenciales para iniciar sesión
        erantzuna2 = requests.request(metodo, uri, headers=goiburua, data=edukia_form, allow_redirects=False)
        # Se comprueba la respuesta de la segunda petición
        if erantzuna2.status_code == 303:
            if 'Set-Cookie' in erantzuna2.headers:
                self._cookie = erantzuna2.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna2.headers:
                uri = erantzuna2.headers['Location']
        else:
            print(f"Error 2. petición. Respuesta: {erantzuna2.status_code} {erantzuna2.reason}")
            print("Valor esperado: 303")
            exit(1)
        ################################################################

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        ################################################################
        # Definicion de los campos necesarios para la peticion HTTP
        metodo = "GET"
        goiburuak = { "Host": "egela.ehu.eus", "Cookie": self._cookie}

        # Se envia la tercera petición para seguir la redirección después de iniciar sesión
        erantzuna3 = requests.request(metodo, uri, headers=goiburuak, allow_redirects=False)

        # Se comprueba la respuesta de la tercera petición
        if erantzuna3.status_code == 303:
            if 'Set-Cookie' in erantzuna3.headers:
                self._cookie = erantzuna3.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna3.headers:
                uri = erantzuna3.headers['Location']
        else:
            print(f"Error 3. petición. Respuesta: {erantzuna3.status_code} {erantzuna3.reason}")
            print("Valor esperado: 303")
            exit(1)

        # Si la cookie ha cambiado, se actualiza en los encabezados para las siguientes peticiones
        if goiburuak["Cookie"] != self._cookie:
            goiburuak["Cookie"] = self._cookie
        ################################################################

        progress = 75
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        print("\n##### 4. PETICION #####")
        ################################################################
        # Se envia directamente la cuarta petición a la página principal de eGela
        # Anteriormente se ha obtenido la nueva uri, y los headers no son necesarios actualizarlos
        erantzuna4 = requests.request(metodo, uri, headers=goiburuak, allow_redirects=False)

        # Se comprueba la respuesta de la cuarta petición para verificar si el inicio de sesión ha sido exitoso
        if erantzuna4.status_code == 200:
            COMPROBACION_DE_LOG_IN = True
        else:
            COMPROBACION_DE_LOG_IN = False
            print(f"Error 4. petición. Respuesta: {erantzuna4.status_code} {erantzuna4.reason}")
            print("Valor esperado: 200")
            exit(1)

        # Analizamos el HTML de la página principal para buscar el enlace a la asignatura "Web Sistemak"
        html_parser = BeautifulSoup(erantzuna4.text, "html.parser")
        websis = html_parser.find_all('div', {"class": "card dashboard-card"})

        for w in websis:
            # Se busca el enlace de la asignatura en la que se van a descargar los PDFs
            esteka_probisional = w.find('a')
            if esteka_probisional:
                izena = esteka_probisional.get_text(strip=True)
                # Si el enlace contiene "Web Sistemak", se guarda la URL de la asignatura para las siguientes peticiones
                if "Web Sistemak" in izena:
                    self._curso = esteka_probisional['href']
                    print(f"Asignatura encontrada: {izena}")
                    print(f"Uri: {self._curso}")
                    break

        ################################################################

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        # Si el login ha sido exitoso, se cierra la ventana de login y se establece el atributo _login a 1 para indicar que se ha iniciado sesión correctamente
        if COMPROBACION_DE_LOG_IN:
            self._login = 1
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 5. PETICION (Página principal de la asignatura en eGela) #####")
        # Definición de los campos necesarios para la petición HTTP
        metodo = 'GET'
        goiburuak = { "Host": "egela.ehu.eus", "Cookie": self._cookie}
        print(self._curso + "curso")
        # Se envia la petición a la página principal de la asignatura para analizar su contenido y buscar los enlaces a los PDFs
        erantzuna5 = requests.request(metodo, self._curso, headers=goiburuak, allow_redirects=False)

        # Se comprueba la respuesta de la petición a la página principal de la asignatura
        if erantzuna5.status_code == 200:
            print("\n##### Analisis del HTML... #####")

            # Se analiza el HTML de la página principal de la asignatura para buscar los enlaces a los diferentes apartados (Erlaitzak) donde pueden estar los PDFs
            html_parser = BeautifulSoup(erantzuna5.text, "html.parser")
            erlaitz = html_parser.select('ul.nav-tabs .nav-item .nav-link')
            deskargatutakoak = set()

            # Se calcula el progreso que se debe incrementar por cada apartado (Erlaitz) analizado para actualizar la barra de progreso
            total = len(erlaitz) + 1
            progress_step =  100.0 / total
            for er in erlaitz:
                progress += progress_step
                progress_var.set(progress)
                progress_bar.update()

                uri_erlaitz = er.get('href')

                if not uri_erlaitz or not uri_erlaitz.startswith('http'):
                    continue

                # Se obtiene el nombre del tema y filtrar la etiqueta "Nabarmendua"
                gai_izena = er.get_text(strip=True)
                gaiak = gai_izena.split("Destacado")
                gaia = gaiak[0]
                
                # Excluir apartados que no contienen archivos para descargar
                if any(kendu in gai_izena for kendu in ["Ikastaroa", "Partaideak", "Kalifikazioak"]):
                    continue

                uri_erlaitz = er['href']
                print(f"Procesando {gaia}")
                metodo = 'GET'

                # Se accede al apartado para obtener sus archivos
                erantzun_fitxategi = requests.request(metodo, uri_erlaitz, headers=goiburuak, allow_redirects=False)
                html_fitxategi = BeautifulSoup(erantzun_fitxategi.text, "html.parser")

                # Se buscan todos los elementos de archivo en la sección (Erlaitz)
                fitxategiak = html_fitxategi.find_all('li', {"class": "modtype_resource"})

                baimendu_ikastaro = ["Aurkezpena", "Irakaskuntza gida", "Planifikazioa"]

                # Procesar cada archivo encontrado
                for fitx in fitxategiak:
                    f = fitx.find('a')
                    if not f:
                        continue
                    # Se obtiene el enlace del archivo
                    f = f.get('href')

                    fitx_izen = fitx.get_text(strip=True)
                    # Se limpia el nombre eliminando textos redundantes como "PDF Fichero" o "Fichero"
                    fitx_garbi = re.sub(r'(?i)pdf\s+fichero|fichero', '', fitx_izen).strip()

                    # Si la sección es "Curso", filtrar solo archivos permitidos
                    if "Ikastaroa" in gaia:
                        if not any(baim in fitx_garbi for baim in baimendu_ikastaro):
                            continue

                    if fitx_garbi in deskargatutakoak:  # No descargar duplicados
                        continue

                    # Se realiza una petición intermedia para obtener el enlace directo al documento
                    erantzun_dokumentua = requests.request(metodo, f, headers=goiburuak, allow_redirects=False)
                    html_dok = BeautifulSoup(erantzun_dokumentua.text, "html.parser")
                    dok = html_dok.find('div', {"class": "resourceworkaround"})

                    # Se verifica si el enlace redirige a otra página
                    dokumentua = ''
                    if dok:
                        dokumentua = dok.find('a')
                        if not dokumentua:
                            continue
                        # Extraer el enlace del contenedor
                        dokumentua = dokumentua.get('href')

                    pdf_da = ''
                    # Se verifica si el archivo es un PDF
                    if "pdf" in (dokumentua.lower() or fitx_izen.lower()):
                        pdf_da = "pdf"

                    if pdf_da:
                        # Realizar petición final al documento
                        erantzun_dok = ''
                        if dokumentua:
                            erantzun_dok = requests.request(metodo, dokumentua, headers=goiburuak, allow_redirects=False)
                        # Establecer la extensión del archivo
                        luzapena = ".pdf"

                        fitxategi_izena = re.sub(r'[\\/*?:"<>|]', "", fitx_garbi)

                        if len(fitxategi_izena) > 100:  # Limitar la longitud del nombre
                            fitxategi_izena = fitxategi_izena[:100]

                        # Añadir la extensión si no la tiene
                        if not fitxategi_izena.lower().endswith(luzapena):
                            fitxategi_izena += luzapena

                        pdf = {'pdf_name': fitx_garbi, 'pdf_link': f}
                        deskargatutakoak.add(fitx_garbi)
                        self._refs.append(pdf)
                        print(f"Fichero -> {fitxategi_izena}")

        NUMERO_DE_PDF_EN_EGELA = len(self._refs)

        if self._refs:
            progress_step = 100 / len(self._refs)
            for _ in self._refs:
                progress += progress_step
                progress_var.set(progress)
                progress_bar.update()
                time.sleep(0.1)

        popup.destroy()
        return self._refs

    def get_pdf(self, selection):
        print("\t##### descargando PDF... #####")
        
        # Se obtiene la referencia del PDF seleccionado por el usuario a través del índice "selection" y se extraen el nombre y el enlace del PDF
        ref = self._refs[selection]
        pdf_name = ref['pdf_name']
        pdf_link = ref['pdf_link']
        
        # Si el nombre del PDF no termina con .pdf, se le añade la extensión .pdf al nombre
        if not pdf_name.lower().endswith('.pdf'):
            pdf_name += '.pdf'
        
        # Definición de los campos necesarios para la petición HTTP
        metodo = 'GET'
        goiburuak = {"Host": "egela.ehu.eus", "Cookie": self._cookie}

        # Se envía la petición para descargar el PDF utilizando el enlace obtenido, y se analiza la respuesta para buscar el enlace directo al PDF en caso de que el enlace inicial redirija a otra página
        erantzuna = requests.request(metodo, pdf_link, headers=goiburuak, allow_redirects=False)
        html = BeautifulSoup(erantzuna.text, "html.parser")
        
        # Se busca en el HTML de la respuesta un div con la clase "resourceworkaround" que contenga un enlace al PDF, y si se encuentra, se obtiene ese enlace para descargar el PDF directamente desde allí
        dok = html.find('div', {"class": "resourceworkaround"})
        url_zuzena = None
        if dok:
            esteka = dok.find('a')
            if esteka:
                url_zuzena = esteka.get('href')
        
        # Si se ha encontrado un enlace directo al PDF, se descarga desde ese enlace, de lo contrario se descarga desde el enlace inicial
        if url_zuzena:
            erantzun_pdf = requests.request(metodo, url_zuzena, headers=goiburuak, allow_redirects=True)
        else:
            erantzun_pdf = requests.request(metodo, pdf_link, headers=goiburuak, allow_redirects=True)
        
        pdf_content = erantzun_pdf.content
        print(f"\Descargado: {pdf_name} ({len(pdf_content)} bytes)")
        
        return pdf_name, pdf_content