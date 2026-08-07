#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import time
import json
import urllib.request
import urllib.error
import hashlib
from datetime import datetime

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
    if not ts: return "N/A"
    return datetime.fromtimestamp(float(ts)).strftime('%d/%m/%Y %H:%M:%S')

def user_dossier():
    user = input(f"\n{Colors.CYAN}Username para dossiê:{Colors.RESET} ").strip().lower()
    if not user: return
    st, data = _firebase_req(f"users/{user}")
    if st == 200 and data:
        print(f"\n{Colors.BOLD}--- DOSSIÊ DE USUÁRIO: {user.upper()} ---{Colors.RESET}")
        print(f"[{Colors.GREEN}+{Colors.RESET}] Status da Conta: {'Ativa' if data.get('active', True) else 'BLOQUEADA'}")
        print(f"[{Colors.GREEN}+{Colors.RESET}] Licença Expira em: {format_ts(data.get('expiration_timestamp'))}")
        
        device = data.get("last_device")
        if device:
            print(f"\n{Colors.YELLOW}[!] FINGERPRINT DO DISPOSITIVO REGISTRADO{Colors.RESET}")
            print(f"    ├─ Modelo: {device.get('modelName', 'N/A')}")
            print(f"    ├─ Marca: {device.get('brand', 'N/A')}")
            print(f"    ├─ OS: {device.get('osName', 'N/A')} {device.get('osVersion', 'N/A')}")
            print(f"    ├─ Build ID (OS): {device.get('osBuildId', 'N/A')}")
            print(f"    ├─ Impressão Digital (Android ID): {Colors.BRIGHT_RED}{device.get('androidId', 'N/A')}{Colors.RESET}")
            print(f"    ├─ IP Registrado: {device.get('ipAddress', 'N/A')}")
            
            # Formatar detalhes de rede se disponíveis
            net_state = device.get('networkState', {})
            is_connected = net_state.get('isConnected')
            net_type = net_state.get('type', 'N/A')
            print(f"    ├─ Rede Conectada: {'Sim' if is_connected else 'Não'} (Tipo: {net_type})")
            
            print(f"    └─ Último Login Capturado: {format_ts(device.get('timestamp'))}")
        else:
            print(f"\n{Colors.YELLOW}[!] Nenhum fingerprint de dispositivo registrado.{Colors.RESET}")
        
    else:
        print(f"{Colors.RED}Usuário não encontrado.{Colors.RESET}")
    input("\nPressione ENTER...")

def manage_users():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}[ GERENCIAMENTO DE CONTAS E INVESTIGAÇÃO ]{Colors.RESET}\n")
        print(f" {Colors.CYAN}1.{Colors.RESET} Criar / Editar Usuário")
        print(f" {Colors.CYAN}2.{Colors.RESET} Listar Todos os Usuários")
        print(f" {Colors.CYAN}3.{Colors.RESET} Bloquear / Desbloquear Conta")
        print(f" {Colors.CYAN}4.{Colors.RESET} Remover Usuário Permanentemente")
        print(f" {Colors.CYAN}5.{Colors.RESET} Renovar Licença")
        print(f" {Colors.CYAN}6.{Colors.RESET} Gerar Dossiê (Dados + Aparelho) {Colors.BRIGHT_RED}[NOVO]{Colors.RESET}")
        print(f" {Colors.WHITE}0.{Colors.RESET} Voltar")
        
        opt = input("\n> ")
        
        if opt == "0": break
        elif opt == "1":
            user = input("Username: ").strip().lower()
            if not user: continue
            pwd = input("Senha: ").strip()
            pwd_hash = hashlib.sha256(pwd.encode('utf-8')).hexdigest()
            dias = input("Validade em dias (Padrão 30): ").strip()
            dias = int(dias) if dias.isdigit() else 30
            exp_ts = time.time() + (dias * 24 * 60 * 60)
            
            st, existing = _firebase_req(f"users/{user}")
            if st == 200 and existing:
                _firebase_req(f"users/{user}/password", method="PUT", data=pwd_hash)
                print(f"{Colors.GREEN}Senha atualizada!{Colors.RESET}")
            else:
                payload = {"username": user, "password": pwd_hash, "active": True, "expiration_timestamp": exp_ts}
                _firebase_req(f"users/{user}", method="PUT", data=payload)
                print(f"{Colors.GREEN}Usuário '{user}' criado!{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "2":
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
            
        elif opt == "3":
            user = input("Username: ").strip().lower()
            st, data = _firebase_req(f"users/{user}")
            if data:
                new_status = not data.get("active", True)
                _firebase_req(f"users/{user}/active", method="PUT", data=new_status)
                print(f"{Colors.GREEN}Status de '{user}' alterado para {'ATIVO' if new_status else 'BLOQUEADO'}.{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "4":
            user = input("Username para remover (PERMANENTE): ").strip().lower()
            st, data = _firebase_req(f"users/{user}")
            if data:
                _firebase_req(f"users/{user}", method="DELETE")
                print(f"{Colors.GREEN}Usuário apagado!{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt == "5":
            user = input("Username: ").strip().lower()
            dias = input("Adicionar quantos dias? ").strip()
            if dias.isdigit():
                st, data = _firebase_req(f"users/{user}")
                if data:
                    cur = data.get("expiration_timestamp", time.time())
                    cur = max(cur, time.time())
                    _firebase_req(f"users/{user}/expiration_timestamp", method="PUT", data=cur + int(dias)*86400)
                    print(f"{Colors.GREEN}Licença estendida!{Colors.RESET}")
            input("\nPressione ENTER...")
        elif opt == "6":
            user_dossier()

def system_announcements():
    while True:
        clear_screen()
        print_banner()
        print(f"{Colors.BOLD}[ COMUNICADOS GLOBAIS E PUSH NOTIFICATIONS ]{Colors.RESET}\n")
        print(f" {Colors.CYAN}1.{Colors.RESET} Alterar Mensagem Global do App (Lobby)")
        print(f" {Colors.CYAN}2.{Colors.RESET} Disparar Push Notification para Todos")
        print(f" {Colors.CYAN}3.{Colors.RESET} Disparar Push Notification Individual")
        print(f" {Colors.WHITE}0.{Colors.RESET} Voltar")
        
        opt = input("\n> ")
        if opt == "0": break
        elif opt == "1":
            msg = input(f"Novo aviso (deixe vazio para remover): ").strip()
            _firebase_req("app_config/global_warning", method="PUT", data=msg if msg else None)
            print(f"{Colors.GREEN}Aviso Global atualizado.{Colors.RESET}")
            input("\nPressione ENTER...")
            
        elif opt in ["2", "3"]:
            title = input("Título da Notificação: ").strip()
            body = input("Mensagem: ").strip()
            
            if opt == "2":
                st, users = _firebase_req("users")
                count = 0
                if users:
                    for u, data in users.items():
                        tok = data.get("pushToken")
                        if tok and data.get("active", True):
                            succ, emsg = _send_expo_push(tok, title, body)
                            if succ: count += 1
                            else: print(f"{Colors.RED}Erro ({u}): {emsg}{Colors.RESET}")
                print(f"{Colors.GREEN}{count} notificações enviadas.{Colors.RESET}")
            else:
                tgt = input("Username destino: ").strip().lower()
                st, data = _firebase_req(f"users/{tgt}")
                if data and data.get("pushToken"):
                    succ, emsg = _send_expo_push(data["pushToken"], title, body)
                    if succ: print(f"{Colors.GREEN}Enviado!{Colors.RESET}")
                    else: print(f"{Colors.RED}Erro: {emsg}{Colors.RESET}")
                else: print(f"{Colors.RED}Usuário sem Push Token.{Colors.RESET}")
            input("\nPressione ENTER...")

def main_menu():
    while True:
        clear_screen()
        print_banner()
        print(f" {Colors.CYAN}1.{Colors.RESET} Gerenciar Usuários e Dispositivos")
        print(f" {Colors.CYAN}2.{Colors.RESET} Comunicados e Push Notifications")
        print(f" {Colors.WHITE}0.{Colors.RESET} Sair")
        
        opt = input("\nSelecione uma operação: ")
        
        if opt == "1": manage_users()
        elif opt == "2": system_announcements()
        elif opt == "0": break

if __name__ == "__main__":
    try:
        main_menu()
    except KeyboardInterrupt:
        print(f"\n{Colors.RED}Painel encerrado pelo usuário.{Colors.RESET}")
        sys.exit(0)
