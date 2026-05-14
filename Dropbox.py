import requests
import urllib
import webbrowser
from socket import AF_INET, socket, SOCK_STREAM
import json
import helper

app_key = '8tj9infsdwcxsbb'
app_secret = 'tgnzcye443b6lbc'
server_addr = "localhost"
server_port = 8070
redirect_uri = "http://" + server_addr + ":" + str(server_port)

class Dropbox:
    _access_token = ""
    _path = "" # / parece que da problemas
    _files = []
    _root = None
    _msg_listbox = None

    def __init__(self, root):
        self._root = root

    def local_server(self):
        # por el puerto 8090 esta escuchando el servidor que generamos
        server_socket = socket(AF_INET, SOCK_STREAM)
        server_socket.bind((server_addr, server_port))
        server_socket.listen(1)
        print("\tLocal server listening on port " + str(server_port))

        # recibe la redireccio 302 del navegador
        client_connection, client_address = server_socket.accept()
        peticion = client_connection.recv(1024)
        print("\tRequest from the browser received at local server:")
        print (peticion)

        # buscar en solicitud el "auth_code"
        primera_linea =peticion.decode('UTF8').split('\n')[0]
        aux_auth_code = primera_linea.split(' ')[1]
        auth_code = aux_auth_code[7:].split('&')[0]
        print ("\tauth_code: " + auth_code)

        # devolver una respuesta al usuario
        http_response = "HTTP/1.1 200 OK\r\n\r\n" \
                        "<html>" \
                        "<head><title>Proba</title></head>" \
                        "<body>The authentication flow has completed. Close this window.</body>" \
                        "</html>"
        client_connection.sendall(http_response.encode('utf-8'))
        client_connection.close()
        server_socket.close()

        return auth_code

    def do_oauth(self):
        if len(app_key) == 0 or len(app_secret) == 0:
            # Si no se han añadido las claves necesarias para hacer la autenticación el programa terminará
            print(f"falta el app_key o el app_secret en el archivo Dropbox.py\n app_secret:'{app_secret}'\n app_key'{app_key}'")
            exit(1)

        # Definición de los campos necesarios    
        servidor = 'www.dropbox.com'
        params = {'response_type': 'code',
            'client_id': app_key,
            'redirect_uri': redirect_uri }
        params_encoded = urllib.parse.urlencode(params)
        recurso = '/oauth2/authorize?' + params_encoded
        uri = 'https://' + servidor + recurso
        webbrowser.open_new(uri)

        # Conseguir el código
        auth_code = self.local_server()

        # Definición de los campos necesarios    
        params = {'code': auth_code,
        'grant_type': 'authorization_code',
        'client_id': app_key,
        'client_secret': app_secret,
        'redirect_uri': redirect_uri}
        cabeceras={'User-Agent':'Python Client',
        'Content-Type': 'application/x-www-form-urlencoded'}
        uri='https://api.dropboxapi.com/oauth2/token'

        # Enviar petición
        respuesta = requests.post( uri, headers=cabeceras,data=params)
        print (respuesta.status_code)
        # Procesar la respuesta como JSON
        json_respuesta = json.loads(respuesta.content)
        print (json_respuesta)
        # Guardar access token en la variable
        self._access_token = json_respuesta['access_token']
        print ("\n\nAccess_Token:"+ self._access_token)

        self._root.destroy()

    def list_folder(self, msg_listbox):
        print("/list_folder")
        # Definición de los campos necesarios para la petición HTTP
        uri = 'https://api.dropboxapi.com/2/files/list_folder'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-list_folder

        datos = {'path': self._path,
                 'recursive': False}
        datos_encoded = json.dumps(datos)
        print("Datos: " + datos_encoded)
        cabeceras = {'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json',
            'scope': 'files.metadata.read'}
        
        # Enviar petición
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded,allow_redirects=False)
        status = respuesta.status_code
        print ("\tStatus: " + str(status))
        contenido = respuesta.text
        print("\tContenido:")
        # Procesar la respuesta como JSON
        contenido_json = json.loads(contenido)
        if respuesta.status_code != 200:
            print("Error Dropbox")
            return
        try:
            contenido_json = respuesta.json()
        except Exception as e:
            print("JSON inválido:", e)
            return

        # Imprimir los nombres de los archivos obtenidos
        print("Ficheros en "+ self._path)
        for entrie in contenido_json.get("entries", []):
            print(entrie['name'])

        # Comprobar si hay archivos en la respuesta
        if 'entries' not in contenido_json:
            print("\tNo se han encontrado archivos en:", contenido_json)
            return
        self._files = helper.update_listbox2(msg_listbox, self._path, contenido_json)

    def transfer_file(self, file_path, file_data):
        print("/upload")
        # Definición de los campos necesarios para la petición HTTP
        uri = 'https://content.dropboxapi.com/2/files/upload'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-upload

        uri = 'https://content.dropboxapi.com/2/files/upload'
        api_arg = "{\"autorename\":false,\"mode\":\"add\",\"mute\":false,\"path\":\"" + file_path +"\",\"strict_conflict\":false}"
        cabeceras = {'Host': 'content.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/octet-stream',
            'scope': 'files.content.write',
            "Dropbox-API-Arg":  api_arg}
        
        # Enviar petición
        respuesta = requests.post(uri, headers=cabeceras, data=file_data)
        print("\tStatus: " + str(respuesta.status_code))
        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultado = json.loads(respuesta.content)
            print("Archivo subido exitosamente:")
            print(resultado)
        else:
            print("Error al subir el archivo:")
            print(respuesta.text)


    def delete_file(self, file_path):
        print("/delete_file")

        # Definición de los campos necesarios
        uri = 'https://api.dropboxapi.com/2/files/delete_v2'
        # https://www.dropbox.com/developers/documentation/http/documentation#files-delete
        cabeceras = {'Host': 'api.dropboxapi.com',
                     'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}

        # Se comprueba si el file_path es un set, list o tuple y se extrae el primer elemento
        if isinstance(file_path, (set, list, tuple)):
            file_path = list(file_path)[0]

        # Se limpian los espacios en blanco del file_path
        file_path = str(file_path).strip()
        # Se asegura que el file_path empiece con "/"
        if not file_path.startswith("/"):
            file_path = "/" + file_path

        datos = {'path': file_path}
        datos_json = json.dumps(datos)

        # Enviar petición
        respuesta = requests.post(uri, headers=cabeceras, data=datos_json)
        print("\tStatus: " + str(respuesta.status_code))
        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultado = json.loads(respuesta.content)
            print("Archivo eliminado exitosamente:")
            print(resultado)
        else:
            print("Error al eliminar el archivo:")
            print(respuesta.text)

    def create_folder(self, path):
        print("/create_folder")
        # Definición de los campos necesarios para la petición HTTP
        uri = 'https://api.dropboxapi.com/2/files/create_folder_v2'
       # https://www.dropbox.com/developers/documentation/http/documentation#files-create_folder
        datos = {'path': path,
                 'autorename': False}
        datos_encoded = json.dumps(datos)
        print("Datuak: " + datos_encoded)

        cabeceras = {'Host': 'api.dropboxapi.com',
            'Authorization': 'Bearer ' + self._access_token,
            'Content-Type': 'application/json'}

        # Enviar petición
        respuesta = requests.post(uri, headers=cabeceras, data=datos_encoded)
        print("\tStatus: " + str(respuesta.status_code))
        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultado = json.loads(respuesta.content)
            print("Carpeta creada exitosamente:")
            print(resultado)
        else:
            print("Error al crear la carpeta:")
            print(respuesta.text)

    ######################
    # Funciones añadidas #
    ######################
    def rename_file(self, old_path, new_name):
        print("/rename_file")
       
        # Definición de los campos necesarios para la petición HTTP
        uri = 'https://api.dropboxapi.com/2/files/move_v2'
        # Se define un nuevo path con el mismo directorio pero con el nuevo nombre
        path_zatitu = old_path.split('/')
        path_zatitu[-1] = new_name
        new_path = '/'.join(path_zatitu)

        cabeceras = {'Host': 'api.dropboxapi.com',
                     'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'}

        data = {
            'from_path': old_path,
            'to_path': new_path,
            'autorename': True
        }
        data_encoded = json.dumps(data)

        # Enviar petición
        respuesta = requests.post(uri, headers=cabeceras, data=data_encoded)
        print("\tStatus: " + str(respuesta.status_code))
        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultado = json.loads(respuesta.content)
            print("Archivo renombrado exitosamente:")
            print(resultado)
            return True
        else:
            print("Error al renombrar el archivo:")
            print(respuesta.text)
            return False


    def move_file(self, old_path, target_folder):
        print("/move_v2 (Mover)")
        # Definición de los campos necesarios para la petición HTTP
        uri = 'https://api.dropboxapi.com/2/files/move_v2'

        # Extraemos el nombre del archivo del path original
        file_name = old_path.split('/')[-1]

        # Se construye el nuevo path
        target_folder = target_folder.strip('/')
        if target_folder == "":
            new_path = "/" + file_name
        else:
            new_path = "/" + target_folder + "/" + file_name

        headers = {'Host': 'api.dropboxapi.com',
                     'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'
                   }
        data = {
            "from_path": old_path,
            "to_path": new_path,
            "autorename": True
        }

        # Enviar petición
        respuesta = requests.post(uri, headers=headers, data=json.dumps(data))
        print("\tStatus: " + str(respuesta.status_code))
        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultado = json.loads(respuesta.content)
            print("Archivo movido exitosamente:")
            print(resultado)
        else:
            print("Error al mover el archivo:")
            print(respuesta.text)
        return respuesta.status_code == 200

    def search(self, query, msg_listbox):
        print("/search")
        # Definicion de los campos necesarios para la peticion HTTP   
        uri = 'https://api.dropboxapi.com/2/files/search_v2'

        headers = {'Host': 'api.dropboxapi.com',
                     'Authorization': 'Bearer ' + self._access_token,
                     'Content-Type': 'application/json'
        }
        data = {'query': query,
                'options': {
                    'path': ""
                }
            }

        data_encoded = json.dumps(data)
        # Enviar petición
        respuesta = requests.post(uri, headers=headers, data=data_encoded)

        # Comprobacion del status_code de la respuesta
        if respuesta.status_code == 200:
            resultados = respuesta.json()

            # Como la API search devuelve una estructura distinta a list_folder, procesamos los resultados para adaptarlos al formato que espera helper.update_listbox2
            matches = resultados.get('matches', [])
            processed_files = []

            # Recorremos los resultados de búsqueda y extraemos la metadata de cada archivo encontrado
            for m in matches:
                metadata = m.get('metadata', {}).get('metadata', {})
                processed_files.append(metadata)

            # Se crea un diccionario falso para engañar al helper y que pinte los resultados
            fake_json = {'entries': processed_files}

            # Se limpia la ruta actual para indicar que estamos en modo búsqueda
            self._path = "Resultados de búsqueda"
            self._files = helper.update_listbox2(msg_listbox, self._path, fake_json)
        # Si la respuesta no es 200, se muestra un mensaje de error con el contenido de la respuesta
        else:
            print("Error en la búsqueda:", respuesta.text)

