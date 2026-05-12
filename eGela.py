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
        metodo = "GET"
        uri = "https://egela.ehu.eus/login/index.php"
        goiburua = { "Host": "egela.ehu.eus",}

        erantzuna = requests.request(metodo, uri, headers=goiburua, allow_redirects=False)

        if erantzuna.status_code == 200:
            if 'Set-Cookie' in erantzuna.headers:
                self._cookie = erantzuna.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna.headers:
                uri = erantzuna.headers['Location']
        else:
            print(f"Errorea 1 eskaeran. Emaitza: {erantzuna.status_code} {erantzuna.reason}")
            print("Espero zena: 200")
            exit(1)

        html_parser = BeautifulSoup(erantzuna.content, "html.parser")
        logintoken = html_parser.find("input", {"name": "logintoken"})["value"]
        ################################################################

        progress = 25
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 2. PETICION #####")
        ################################################################
        metodo = "POST"
        goiburua["Cookie"] = self._cookie
        goiburua["Content-Type"] = "application/x-www-form-urlencoded"

        # username eta password-ean beste balio batzuk agertzen ziren eta metodo hauek erabiliko dira hauen balioak lortzeko
        user_val = username.get()
        password_val = password.get()

        edukia = { 'logintoken': logintoken, 'username': user_val, 'password': password_val}
        edukia_form = urllib.parse.urlencode(edukia)
        goiburua["Content-Length"] = str(len(edukia_form))

        erantzuna2 = requests.request(metodo, uri, headers=goiburua, data=edukia_form, allow_redirects=False)
        if erantzuna2.status_code == 303:
            if 'Set-Cookie' in erantzuna2.headers:
                self._cookie = erantzuna2.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna2.headers:
                uri = erantzuna2.headers['Location']
        else:
            print(f"Errorea 2. eskaeran. Emaitza: {erantzuna2.status_code} {erantzuna2.reason}")
            print("Espero zena: 303")
            exit(1)
        ################################################################

        progress = 50
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)

        print("\n##### 3. PETICION #####")
        ################################################################
        metodo = "GET"
        goiburuak = { "Host": "egela.ehu.eus", "Cookie": self._cookie}

        erantzuna3 = requests.request(metodo, uri, headers=goiburuak, allow_redirects=False)

        if erantzuna3.status_code == 303:
            if 'Set-Cookie' in erantzuna3.headers:
                self._cookie = erantzuna3.headers['Set-Cookie'].split(";")[0]
            if 'Location' in erantzuna3.headers:
                uri = erantzuna3.headers['Location']
        else:
            print(f"Errorea 3. eskaeran. Emaitza: {erantzuna3.status_code} {erantzuna3.reason}")
            print("Espero zena: 303")
            exit(1)

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
        erantzuna4 = requests.request(metodo, uri, headers=goiburuak, allow_redirects=False)
        #profil_url = "https://egela.ehu.eus/user/profile.php"
        #erantzun_profil = requests.request(metodo, profil_url, headers=goiburuak, allow_redirects=False)



        if erantzuna4.status_code == 200:
            COMPROBACION_DE_LOG_IN = True
        else:
            COMPROBACION_DE_LOG_IN = False
            print(f"Errorea 4. eskaeran. Emaitza: {erantzuna4.status_code} {erantzuna4.reason}")
            print("Espero zena: 200")
            exit(1)
        # Esto creo que hay que mover abajo
        html_parser = BeautifulSoup(erantzuna4.text, "html.parser")
        websis = html_parser.find_all('div', {"class": "card dashboard-card"})

        for w in websis:
            # <a> esteka bilatzen dugu
            esteka_probisional = w.find('a')
            if esteka_probisional:
                izena = esteka_probisional.get_text(strip=True)
                # Lortutako estekan Web Sistemak dagoela egiaztatu
                if "Web Sistemak" in izena:
                    self._curso = esteka_probisional['href']
                    print(f"Irakasgaia aurkituta")
                    print(f"Uria: {self._curso}")
                    break

        ################################################################

        progress = 100
        progress_var.set(progress)
        progress_bar.update()
        time.sleep(1)
        popup.destroy()

        if COMPROBACION_DE_LOG_IN:
            self._login = 1
            #############################################
            # ACTUALIZAR VARIABLES
            #############################################
            self._root.destroy()
        else:
            messagebox.showinfo("Alert Message", "Login incorrect!")

    def get_pdf_refs(self):
        popup, progress_var, progress_bar = helper.progress("get_pdf_refs", "Downloading PDF list...")
        progress = 0
        progress_var.set(progress)
        progress_bar.update()

        print("\n##### 5. PETICION (Página principal de la asignatura en eGela) #####")
        #############################################
        # RELLENAR CON CODIGO DE LA PETICION HTTP
        # Y PROCESAMIENTO DE LA RESPUESTA HTTP
        #############################################

        metodo = 'GET'
        goiburuak = { "Host": "egela.ehu.eus", "Cookie": self._cookie}
        print(self._curso + "curso")
        erantzuna5 = requests.request(metodo, self._curso, headers=goiburuak, allow_redirects=False)

        # print(erantzuna5.content)

        # Esto no se si se debe de dejar o no
        #progress_step = float(100.0 / len(NUMERO_DE_PDF_EN_EGELA))

        if erantzuna5.status_code == 200:
            print("\n##### Analisis del HTML... #####")
        #############################################
        # ANALISIS DE LA PAGINA DEL AULA EN EGELA
        # PARA BUSCAR PDFs
        #############################################
            html_parser = BeautifulSoup(erantzuna5.text, "html.parser")
            erlaitz = html_parser.select('ul.nav-tabs .nav-item .nav-link')
            deskargatutakoak = set()

            # =================================================================
            # .pdf fitxategiak bilaketa
            # =================================================================
            total = len(erlaitz) + 1
            progress_step =  100.0 / total
            for er in erlaitz:
                progress += progress_step
                progress_var.set(progress)
                progress_bar.update()

                uri_erlaitz = er.get('href')

                if not uri_erlaitz or not uri_erlaitz.startswith('http'):
                    continue

                # Erlaitzaren izena hartu eta Nabarmenduta zatia kendu
                gai_izena = er.get_text(strip=True)
                gaiak = gai_izena.split("Nabarmenduta")
                gaia = gaiak[0]
                # Orokorrean fitxategirik izango ez dituzten erlaitzak kenduko dira
                if any(kendu in gai_izena for kendu in ["Partaideak", "Kalifikazioak", "Gehiago"]):
                    continue

                uri_erlaitz = er['href']
                print(f"{gaia} prozesatzen")
                metodo = 'GET'

                # Fitxategiaren estekan sartuko gara, barnean fitxategi hori deskargatzeko esteka baitago
                erantzun_fitxategi = requests.request(metodo, uri_erlaitz, headers=goiburuak, allow_redirects=False)
                html_fitxategi = BeautifulSoup(erantzun_fitxategi.text, "html.parser")

                # Erlaitzean dauden fitxategiak bilatuko dira
                fitxategiak = html_fitxategi.find_all('li', {"class": "modtype_resource"})

                baimendu_ikastaro = ["Aurkezpena", "Irakaskuntza gida", "Planifikazioa"]

                # Erlaitzeko fitxategiak lortu
                for fitx in fitxategiak:
                    f = fitx.find('a')
                    if not f:
                        continue
                    # Fitxategia deskargatzeko esteka
                    f = f.get('href')

                    fitx_izen = fitx.get_text(strip=True)
                    # "pdfFitxategia" eta "pyFitxategia" ez ateratzeko egindako garbiketa
                    fitx_garbi = re.sub(r'(?i)pdf\s+fitxategia|fitxategia', '', fitx_izen).strip()

                    # Ikastaroan dauden fitxategiak deskargatzeko bakarrik
                    if "Ikastaroa" in gaia:
                        if not any(baim in fitx_garbi for baim in baimendu_ikastaro):
                            continue

                    if fitx_garbi in deskargatutakoak:  # Fitxategi bera behin baino gehiagotan ez deskargatzeko
                        continue

                    # Erdiko eskaera bat, baldin eta estekak beste orri batera eramaten badu
                    erantzun_dokumentua = requests.request(metodo, f, headers=goiburuak, allow_redirects=False)
                    html_dok = BeautifulSoup(erantzun_dokumentua.text, "html.parser")
                    dok = html_dok.find('div', {"class": "resourceworkaround"})

                    # Lortutako esteka beste orri batera eramaten gaituen konprobaketa
                    dokumentua = ''
                    if dok:
                        dokumentua = dok.find('a')
                        if not dokumentua:
                            continue
                        # Orri horretako esteka hartu
                        dokumentua = dokumentua.get('href')

                    pdf_da = ''
                    # Lortutako fitxategia pdf edo py denentz egiaztatu
                    if "pdf" in (dokumentua.lower() or fitx_izen.lower()):
                        pdf_da = "pdf"

                    if pdf_da:
                        # Beste esteka batera joan behar denentz konprobaketa
                        erantzun_dok = ''
                        if dokumentua:
                            erantzun_dok = requests.request(metodo, dokumentua, headers=goiburuak, allow_redirects=False)
                        # Lortutako fitxategiaren luzapenaren arabera balio bat edo bestea ezarri
                        luzapena = ".pdf"

                        fitxategi_izena = re.sub(r'[\\/*?:"<>|]', "", fitx_garbi)

                        if len(fitxategi_izena) > 100:  # Luzera kontrolatzeko
                            fitxategi_izena = fitxategi_izena[:100]

                        # Luzapena jarri
                        if not fitxategi_izena.lower().endswith(luzapena):
                            fitxategi_izena += luzapena

                        pdf = {'pdf_name': fitx_garbi, 'pdf_link': f}
                        deskargatutakoak.add(fitx_garbi)
                        self._refs.append(pdf)
                        print(f"Fitxategia -> {fitxategi_izena}")

        # INICIALIZA Y ACTUALIZAR BARRA DE PROGRESO
        # POR CADA PDF ANIADIDO EN self._refs

        NUMERO_DE_PDF_EN_EGELA = len(self._refs)
        #progress_step = float(100.0 / len(NUMERO_DE_PDF_EN_EGELA))

        # Esto creo que habria que cambiarlo para que poco a poco vaya cargando
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
        
        ref = self._refs[selection]
        pdf_name = ref['pdf_name']
        pdf_link = ref['pdf_link']
        
        if not pdf_name.lower().endswith('.pdf'):
            pdf_name += '.pdf'
        
        metodo = 'GET'
        goiburuak = {"Host": "egela.ehu.eus", "Cookie": self._cookie}
        
        # 1. Sartu baliabidearen orrialdera (mod/resource/view.php)
        erantzuna = requests.request(metodo, pdf_link, headers=goiburuak, allow_redirects=False)
        html = BeautifulSoup(erantzuna.text, "html.parser")
        
        # 2. Bilatu "resourceworkaround" div-a benetako estekarekin
        dok = html.find('div', {"class": "resourceworkaround"})
        url_zuzena = None
        if dok:
            esteka = dok.find('a')
            if esteka:
                url_zuzena = esteka.get('href')
        
        # 3. Deskargatu PDF-a
        if url_zuzena:
            erantzun_pdf = requests.request(metodo, url_zuzena, headers=goiburuak, allow_redirects=True)
        else:
            erantzun_pdf = requests.request(metodo, pdf_link, headers=goiburuak, allow_redirects=True)
        
        pdf_content = erantzun_pdf.content
        print(f"\tDeskargatuta: {pdf_name} ({len(pdf_content)} bytes)")
        
        return pdf_name, pdf_content