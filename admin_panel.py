#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import urllib.request
import urllib.error
import threading
import hashlib

# Cores no estilo Termux
class Colors:
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    BRIGHT_RED = "\033[91m"
    BRIGHT_GREEN = "\033[92m"
    BRIGHT_YELLOW = "\033[93m"
    BRIGHT_BLUE = "\033[94m"
    BRIGHT_MAGENTA = "\033[95m"
    BRIGHT_CYAN = "\033[96m"

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
  \_____|_| .__/|_| |_|\___|_|     |_|\___/_/\_\\\__| 
          | |                                        
          |_|  {Colors.BRIGHT_GREEN}ENTERPRISE ADMIN PANEL{Colors.RESET}
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
            res = response.read().decode('utf-8')
            return response.status, json.loads(res) if res and res != "null" else None
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 500, None

def _send_expo_push(token: str, title: str, body: str):
    """Envia notificação Push Nativa via Servidor Expo."""
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

def gerenciar_usuarios():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}--- GERENCIAMENTO DE USUÁRIOS ---{Colors.RESET}\n")
        print(f"[{Colors.BRIGHT_GREEN}1{Colors.RESET}] Criar / Editar Usuário")
        print(f"[{Colors.BRIGHT_YELLOW}2{Colors.RESET}] Listar Usuários")
        print(f"[{Colors.BRIGHT_RED}3{Colors.RESET}] Bloquear / Desbloquear Usuário")
        print(f"[{Colors.BRIGHT_CYAN}4{Colors.RESET}] Remover Usuário")
        print(f"[{Colors.BRIGHT_MAGENTA}5{Colors.RESET}] Renovar Licença")
        print(f"[{Colors.WHITE}0{Colors.RESET}] Voltar")
        
        opt = input("\nOpção: ")
        
        if opt == "0":
            break
        elif opt == "1":
            user = input("Username: ").strip().lower()
            if not user: continue
            pwd = input("Senha: ").strip()
            pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
            
            dias_validade = input("Validade em dias (Padrão 30): ").strip()
            dias = int(dias_validade) if dias_validade.isdigit() else 30
            exp_ts = time.time() + (dias * 24 * 60 * 60)
            
            st, existing = _firebase_req(f"users/{user}")
            if st == 200 and existing:
                print(f"{Colors.YELLOW}Usuário já existe. Atualizando senha...{Colors.RESET}")
                _firebase_req(f"users/{user}/password", method="PUT", data=pwd_hash)
            else:
                payload = {
                    "username": user,
                    "password": pwd_hash,
                    "active": True,
                    "expiration_timestamp": exp_ts
                }
                _firebase_req(f"users/{user}", method="PUT", data=payload)
                print(f"{Colors.GREEN}Usuário '{user}' criado com {dias} dias de licença!{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "2":
            st, users = _firebase_req("users")
            print(f"\n{Colors.BOLD}{'USUÁRIO':<20} | {'STATUS'}{Colors.RESET}")
            print("-" * 40)
            if st == 200 and users:
                for u, data in users.items():
                    if isinstance(data, dict):
                        status_str = f"{Colors.BRIGHT_GREEN}ATIVO{Colors.RESET}" if data.get("active", True) else f"{Colors.BRIGHT_RED}BLOQUEADO{Colors.RESET}"
                        print(f"{u:<20} | {status_str}")
            else:
                print("Nenhum usuário encontrado.")
            input("\nPressione ENTER...")
            
        elif opt == "3":
            user = input("Username para alternar status: ").strip().lower()
            st, data = _firebase_req(f"users/{user}")
            if st == 200 and data:
                current = data.get("active", True)
                new_st = not current
                _firebase_req(f"users/{user}/active", method="PUT", data=new_st)
                print(f"{Colors.GREEN}Status alterado para {'ATIVO' if new_st else 'BLOQUEADO'}.{Colors.RESET}")
            else:
                print(f"{Colors.RED}Usuário não encontrado.{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "4":
            user = input("Username para excluir: ").strip().lower()
            conf = input(f"Tem certeza que deseja apagar {user}? (s/n): ").strip().lower()
            if conf == 's':
                _firebase_req(f"users/{user}", method="DELETE")
                print(f"{Colors.GREEN}Usuário excluído.{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "5":
            user = input("Username para renovar: ").strip().lower()
            st, existing = _firebase_req(f"users/{user}")
            if st == 200 and existing:
                dias_validade = input("Acrescentar dias de validade (Padrão 30): ").strip()
                dias = int(dias_validade) if dias_validade.isdigit() else 30
                
                current_exp = existing.get("expiration_timestamp", time.time())
                now = time.time()
                
                # Se já expirou, conta a partir de agora. Se ainda tem dias, soma aos dias restantes.
                base_time = now if current_exp < now else current_exp
                new_exp = base_time + (dias * 24 * 60 * 60)
                
                _firebase_req(f"users/{user}/expiration_timestamp", method="PUT", data=new_exp)
                print(f"{Colors.GREEN}Licença de {user} renovada com sucesso!{Colors.RESET}")
            else:
                print(f"{Colors.RED}Usuário não encontrado.{Colors.RESET}")
            input("\nPressione ENTER...")

def enviar_aviso_global():
    clear_screen()
    print_banner()
    print(f"{Colors.BOLD}--- AVISO GLOBAL (MURRAL DO LOBBY) ---{Colors.RESET}\n")
    print("Este aviso aparecerá na tela do Lobby para todos os usuários.")
    
    texto = input("\nDigite a mensagem do aviso: ").strip()
    if not texto: return
    
    st, current = _firebase_req("app_config/announcements")
    if not isinstance(current, list):
        current = []
        
    current.append(texto)
    _firebase_req("app_config/announcements", method="PUT", data=current)
    print(f"{Colors.GREEN}\nAviso publicado com sucesso!{Colors.RESET}")
    input("\nPressione ENTER...")

def limpar_avisos_globais():
    clear_screen()
    print_banner()
    print(f"{Colors.BOLD}--- LIMPAR AVISOS GLOBAIS ---{Colors.RESET}\n")
    conf = input("Tem certeza que deseja apagar todos os avisos do mural? (s/n): ").strip().lower()
    if conf == 's':
        _firebase_req("app_config/announcements", method="DELETE")
        print(f"{Colors.GREEN}\nAvisos apagados com sucesso!{Colors.RESET}")
    input("\nPressione ENTER...")

def enviar_push_nativo():
    clear_screen()
    print_banner()
    print(f"{Colors.BOLD}--- PUSH NOTIFICATION NATIVA (CELULAR) ---{Colors.RESET}\n")
    print(f"[{Colors.BRIGHT_GREEN}1{Colors.RESET}] Enviar para TODOS os Usuários")
    print(f"[{Colors.BRIGHT_CYAN}2{Colors.RESET}] Enviar para Usuário Individual")
    print(f"[{Colors.WHITE}0{Colors.RESET}] Voltar")
    
    opt = input("\nOpção: ")
    if opt == "0": return
    
    title = input("Título da Notificação: ").strip()
    body = input("Corpo da Mensagem: ").strip()
    if not title or not body: return
    
    st, users = _firebase_req("users")
    if st != 200 or not users:
        print(f"{Colors.RED}Nenhum usuário encontrado no banco.{Colors.RESET}")
        input("\nPressione ENTER...")
        return
        
    if opt == "1":
        print(f"\n{Colors.YELLOW}Disparando Push para todos...{Colors.RESET}")
        count = 0
        for u, data in users.items():
            token = data.get("pushToken")
            # Ignora usuários bloqueados
            if token and data.get("active", True):
                success, msg = _send_expo_push(token, title, body)
                if success:
                    count += 1
                else:
                    print(f"{Colors.RED}Falha para {u}: {msg}{Colors.RESET}")
        print(f"{Colors.GREEN}Notificações enviadas com sucesso: {count}{Colors.RESET}")
        
    elif opt == "2":
        target = input("Username do Destinatário: ").strip().lower()
        if target in users and users[target].get("pushToken"):
            success, msg = _send_expo_push(users[target].get("pushToken"), title, body)
            if success:
                print(f"{Colors.GREEN}Push enviado com sucesso para {target}!{Colors.RESET}")
            else:
                print(f"{Colors.RED}Falha ao enviar Push para {target}: {msg}{Colors.RESET}")
        else:
            print(f"{Colors.RED}Usuário não encontrado ou sem Push Token registrado.{Colors.RESET}")
            
    input("\nPressione ENTER...")

def chat_admin():
    clear_screen()
    print_banner()
    print(f"{Colors.BOLD}--- CHAT ADMINISTRATIVO (ANÔNIMO) ---{Colors.RESET}\n")
    target = input("Digite o ID (username) para conectar: ").strip().lower()
    if not target: return
    
    my_user = "admin_master"
    
    # Enviar convite
    print(f"{Colors.YELLOW}Enviando convite para {target}...{Colors.RESET}")
    _firebase_req(f"chat_invites/{target}", method="PUT", data={"from": my_user, "status": "PENDING"})
    
    # Push notification silenciosa pra avisar o cara a olhar o convite
    st, udata = _firebase_req(f"users/{target}")
    if st == 200 and udata and udata.get("pushToken"):
        succ, msg = _send_expo_push(udata["pushToken"], "Sessão Segura Solicitada", "O Administrador está aguardando você no Lobby.")
        if not succ:
            print(f"{Colors.RED}Aviso: Não foi possível notificar o usuário (Push falhou: {msg}){Colors.RESET}")
    
    print(f"{Colors.GREEN}Convite enviado. Aguardando conexão... (Pressione Ctrl+C para sair){Colors.RESET}")
    
    def listen_chat():
        while True:
            try:
                st, msgs = _firebase_req(f"ephemeral_messages/{my_user}")
                if st == 200 and isinstance(msgs, dict):
                    for msg_id, m in msgs.items():
                        if m['sender'] == target:
                            print(f"\n{Colors.BRIGHT_MAGENTA}[{target}]{Colors.RESET} {m['text']}")
                            # Apaga a mensagem
                            _firebase_req(f"ephemeral_messages/{my_user}/{msg_id}", method="DELETE")
            except Exception:
                pass
            time.sleep(2)
            
    t = threading.Thread(target=listen_chat, daemon=True)
    t.start()
    
    try:
        while True:
            text = input(f"{Colors.BRIGHT_CYAN}[{my_user}] > {Colors.RESET}")
            if text.strip().lower() == '/sair':
                break
            if text.strip():
                msg_id = f"msg_{int(time.time()*1000)}"
                _firebase_req(f"ephemeral_messages/{target}/{msg_id}", method="PUT", data={
                    "id": msg_id,
                    "sender": my_user,
                    "text": text.strip(),
                    "timestamp": int(time.time() * 1000)
                })
                # Send Push
                if udata and udata.get("pushToken"):
                    _send_expo_push(udata["pushToken"], "Sessão Segura", "Nova mensagem do Administrador.")
    except KeyboardInterrupt:
        pass
    
    print(f"\n{Colors.YELLOW}Saindo do chat e vaporizando sessão...{Colors.RESET}")
    _firebase_req(f"chat_invites/{target}", method="DELETE")
    _firebase_req(f"ephemeral_messages/{my_user}", method="DELETE")
    _firebase_req(f"ephemeral_messages/{target}", method="DELETE")
    time.sleep(1)

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print(f"  [{Colors.BRIGHT_GREEN}1{Colors.RESET}] Gerenciar Usuários (Criar/Bloquear/Apagar)")
        print(f"  [{Colors.BRIGHT_YELLOW}2{Colors.RESET}] Publicar Aviso Global (Mural)")
        print(f"  [{Colors.BRIGHT_RED}3{Colors.RESET}] Limpar Avisos Globais")
        print(f"  [{Colors.BRIGHT_MAGENTA}4{Colors.RESET}] Enviar Notificação Push Nativa")
        print(f"  [{Colors.BRIGHT_CYAN}5{Colors.RESET}] Iniciar Chat Anônimo (Terminal -> App)")
        print(f"  [{Colors.RED}0{Colors.RESET}] Sair")
        
        opt = input("\nOpção: ")
        
        if opt == "0":
            break
        elif opt == "1":
            gerenciar_usuarios()
        elif opt == "2":
            enviar_aviso_global()
        elif opt == "3":
            limpar_avisos_globais()
        elif opt == "4":
            enviar_push_nativo()
        elif opt == "5":
            chat_admin()
        else:
            print("Opção inválida.")
            time.sleep(1)

if __name__ == "__main__":
    main_menu()
