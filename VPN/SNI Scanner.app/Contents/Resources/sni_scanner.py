#!/usr/bin/env python3
"""SNI Scanner для Reality — macOS приложение"""

import tkinter as tk
from tkinter import ttk
import ssl, socket, time, concurrent.futures, threading, subprocess, json

DEFAULT_DOMAINS = """www.consilium.europa.eu
www.pge.pl
www.bayer.com
www.philips.com
www.siemens.com
www.ecb.europa.eu
www.dw.com
www.pekao.com.pl
www.europarl.europa.eu
www.shell.com
www.volkswagen.de
www.airbus.com
www.bnpparibas.pl
www.santander.pl
www.mbank.pl
www.bmwgroup.com
www.ing.com
www.pkn.pl
www.orlen.pl
www.pkobp.pl
www.commerzbank.de
www.ing.pl
www.aliorbank.pl
www.bnpparibas.com
www.ab-inbev.com"""

# ── Цвета: белая тема ──────────────────────────────────────────────────────
BG      = "#ffffff"
CARD    = "#f2f2f7"
CARD2   = "#e5e5ea"
TEXT    = "#1c1c1e"
MUTED   = "#6c6c70"
ACCENT  = "#007aff"
GREEN   = "#34c759"
RED     = "#ff3b30"
SEP     = "#c6c6c8"
FONT    = "Helvetica Neue"
CUR     = "arrow"


def check_domain(domain, timeout=4):
    r = {"domain": domain, "tls13": False, "h2": False,
         "redirect": False, "latency_ms": None, "error": None}
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    ctx.set_alpn_protocols(["h2", "http/1.1"])
    try:
        t0 = time.time()
        with socket.create_connection((domain, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=domain) as ssock:
                r["latency_ms"] = round((time.time() - t0) * 1000)
                r["tls13"] = ssock.version() == "TLSv1.3"
                r["h2"] = ssock.selected_alpn_protocol() == "h2"
                try:
                    ssock.sendall(f"HEAD / HTTP/1.1\r\nHost: {domain}\r\nConnection: close\r\n\r\n".encode())
                    resp = ssock.recv(512).decode("utf-8", errors="replace")
                    if any(c in resp.split("\r\n")[0] for c in ["301","302","303","307","308"]):
                        r["redirect"] = True
                except Exception:
                    pass
    except ssl.SSLError:
        r["error"] = "TLS error"
    except (socket.timeout, ConnectionRefusedError, OSError):
        r["error"] = "Timeout"
    except Exception as e:
        r["error"] = str(e)[:35]
    return r


def scan_via_ssh(server_ip, ssh_user, ssh_pass, domains, callback):
    script = f"""
import ssl,socket,time,concurrent.futures,json
domains={repr(domains)}
def check(d,t=4):
    r={{"domain":d,"tls13":False,"h2":False,"redirect":False,"latency_ms":None,"error":None}}
    ctx=ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version=ssl.TLSVersion.TLSv1_3
    ctx.check_hostname=False
    ctx.verify_mode=ssl.CERT_NONE
    ctx.set_alpn_protocols(["h2","http/1.1"])
    try:
        t0=time.time()
        with socket.create_connection((d,443),timeout=t) as s:
            with ctx.wrap_socket(s,server_hostname=d) as ss:
                r["latency_ms"]=round((time.time()-t0)*1000)
                r["tls13"]=ss.version()=="TLSv1.3"
                r["h2"]=ss.selected_alpn_protocol()=="h2"
                try:
                    ss.sendall(f"HEAD / HTTP/1.1\\r\\nHost: {{d}}\\r\\nConnection: close\\r\\n\\r\\n".encode())
                    resp=ss.recv(512).decode("utf-8",errors="replace")
                    if any(c in resp.split("\\r\\n")[0] for c in ["301","302","303","307","308"]):
                        r["redirect"]=True
                except:pass
    except Exception as e:r["error"]=str(e)[:35]
    return r
with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
    results=list(ex.map(check,domains))
print(json.dumps(results))
"""
    try:
        res = subprocess.run(
            ["sshpass", "-p", ssh_pass, "ssh",
             "-o", "StrictHostKeyChecking=no", "-o", "ConnectTimeout=10",
             f"{ssh_user}@{server_ip}",
             f"python3 -c '{script.replace(chr(39), chr(34))}'"],
            capture_output=True, text=True, timeout=60)
        if res.returncode == 0:
            callback(json.loads(res.stdout.strip()), None)
        else:
            callback(None, res.stderr[:200] or "SSH error")
    except FileNotFoundError:
        callback(None, "sshpass не установлен: brew install sshpass")
    except subprocess.TimeoutExpired:
        callback(None, "SSH timeout")
    except Exception as e:
        callback(None, str(e))


def fr(parent, **kw):
    """Frame с явным белым/светлым фоном."""
    bg = kw.pop("bg", BG)
    return tk.Frame(parent, bg=bg, **kw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SNI Scanner")
        self.geometry("480x540")
        self.resizable(False, False)
        self.configure(bg=BG)
        # Принудительно переопределяем системную палитру
        self.option_add("*Background", BG)
        self.option_add("*Foreground", TEXT)
        self.option_add("*Font", f"{FONT} 13")
        self.option_add("*Entry.Background", CARD2)
        self.option_add("*Entry.Foreground", TEXT)
        self.option_add("*Label.Background", BG)
        self.option_add("*Label.Foreground", TEXT)
        self.option_add("*Button.Background", ACCENT)
        self.option_add("*Button.Foreground", "#ffffff")
        self._build_ui()

    # ── helpers ───────────────────────────────────────────────────────────
    def _lbl(self, parent, text, size=13, bold=False, color=None, anchor="w"):
        weight = "bold" if bold else "normal"
        bg = parent.cget("bg")
        return tk.Label(parent, text=text,
                        font=(FONT, size, weight),
                        bg=bg, fg=color or TEXT,
                        anchor=anchor)

    def _entry(self, parent, width=20, show=None, default=""):
        e = tk.Entry(parent,
                     font=(FONT, 14), relief="flat", bd=0,
                     bg=CARD2, fg=TEXT,
                     insertbackground=TEXT,
                     selectbackground=ACCENT,
                     selectforeground="#ffffff",
                     highlightthickness=1,
                     highlightbackground=SEP,
                     highlightcolor=ACCENT,
                     width=width, show=show)
        e.insert(0, default)
        return e

    # ── UI ────────────────────────────────────────────────────────────────
    def _build_ui(self):

        # 1. Заголовок
        hdr = fr(self, bg=BG)
        hdr.pack(fill="x", padx=24, pady=(22, 0))
        self._lbl(hdr, "SNI Scanner", 22, bold=True).pack(anchor="w")
        self._lbl(hdr, "Reality · TLS 1.3 · HTTP/2", 13, color=MUTED).pack(anchor="w", pady=(2, 0))

        # 2. Карточка: сервер + SSH
        card = fr(self, bg=CARD, padx=16, pady=14)
        card.pack(fill="x", padx=24, pady=(18, 0))

        ip_row = fr(card, bg=CARD)
        ip_row.pack(fill="x")

        self._lbl(ip_row, "Сервер", 12, color=MUTED).pack(side="left", padx=(0, 10))
        self.srv_ip = self._entry(ip_row, width=18, default="82.38.66.75")
        self.srv_ip.pack(side="left", ipady=7, padx=(0, 14))

        self.ssh_var = tk.BooleanVar(value=False)
        ssh_cb = tk.Checkbutton(ip_row, text="SSH",
                                variable=self.ssh_var,
                                font=(FONT, 13), bg=CARD, fg=TEXT,
                                activebackground=CARD, activeforeground=TEXT,
                                selectcolor=CARD2,
                                highlightthickness=0,
                                cursor=CUR,
                                command=self._toggle_ssh)
        ssh_cb.pack(side="left")

        # SSH-поля
        self.ssh_frame = fr(card, bg=CARD)

        ssh_row = fr(self.ssh_frame, bg=CARD)
        ssh_row.pack(fill="x", pady=(12, 0))

        def ssh_field(label, default, show=None, w=13):
            col = fr(ssh_row, bg=CARD)
            self._lbl(col, label, 11, color=MUTED).pack(anchor="w")
            e = self._entry(col, width=w, show=show, default=default)
            e.pack(ipady=6, pady=(3, 0))
            col.pack(side="left", padx=(0, 12))
            return e

        self.ssh_user = ssh_field("Пользователь", "root", w=11)
        self.ssh_pass = ssh_field("Пароль", "T-RUeIl9%+", show="*", w=14)

        # 3. Кнопка Сканировать
        self.scan_btn = tk.Button(
            self, text="Сканировать",
            font=(FONT, 16, "bold"),
            bg=ACCENT, fg="#ffffff",
            relief="flat", bd=0,
            pady=15,
            activebackground="#005ecb",
            activeforeground="#ffffff",
            highlightthickness=0,
            cursor=CUR,
            command=self._start_scan)
        self.scan_btn.pack(fill="x", padx=24, pady=(18, 0))

        # 4. Прогресс
        style = ttk.Style()
        style.theme_use("default")
        style.configure("S.Horizontal.TProgressbar",
                        troughcolor=CARD2, background=ACCENT, thickness=4)
        self.progress = ttk.Progressbar(self, style="S.Horizontal.TProgressbar",
                                        mode="indeterminate")

        # 5. Разделитель
        fr(self, bg=SEP, height=1).pack(fill="x", padx=0, pady=(18, 0))

        # 6. Результаты
        self.res_frame = fr(self, bg=BG)
        self.res_frame.pack(fill="both", expand=True, padx=24, pady=(14, 18))

        self.placeholder = self._lbl(self.res_frame,
                                     "Нажми «Сканировать» — найдём лучшие SNI",
                                     13, color=MUTED)
        self.placeholder.pack(anchor="w")

        self.top_frame    = fr(self.res_frame, bg=BG)
        self.others_frame = fr(self.res_frame, bg=BG)

    def _toggle_ssh(self):
        if self.ssh_var.get():
            self.ssh_frame.pack(fill="x")
        else:
            self.ssh_frame.pack_forget()

    def _copy(self, domain, btn):
        self.clipboard_clear()
        self.clipboard_append(domain)
        btn.config(text="Скопировано", bg=GREEN, fg="#ffffff")
        self.after(1800, lambda: btn.config(text="Copy", bg=CARD2, fg=ACCENT))

    def _start_scan(self):
        self.scan_btn.config(state="disabled", text="Сканирование...")
        self.progress.pack(fill="x", padx=24, pady=(10, 0))
        self.progress.start(12)
        self.placeholder.pack_forget()
        for w in self.top_frame.winfo_children():    w.destroy()
        for w in self.others_frame.winfo_children(): w.destroy()
        self.top_frame.pack_forget()
        self.others_frame.pack_forget()

        domains = [d.strip() for d in DEFAULT_DOMAINS.strip().split("\n") if d.strip()]

        if self.ssh_var.get():
            threading.Thread(
                target=scan_via_ssh,
                args=(self.srv_ip.get().strip(),
                      self.ssh_user.get().strip(),
                      self.ssh_pass.get().strip(),
                      domains, self._ssh_done),
                daemon=True).start()
        else:
            threading.Thread(target=self._local_scan,
                             args=(domains,), daemon=True).start()

    def _local_scan(self, domains):
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
            for r in ex.map(check_domain, domains):
                results.append(r)
        self.after(0, self._show, results)

    def _ssh_done(self, results, error):
        if error:
            self.after(0, self._show_err, error)
        else:
            self.after(0, self._show, results)

    def _show_err(self, msg):
        self._finish()
        self._lbl(self.top_frame, f"Ошибка: {msg}", 12, color=RED).pack(anchor="w")
        self.top_frame.pack(fill="x")

    def _show(self, results):
        self._finish()
        good = sorted(
            [r for r in results if r["tls13"] and r["h2"] and not r["redirect"] and not r["error"]],
            key=lambda x: x["latency_ms"] or 9999)

        if not good:
            self._lbl(self.top_frame, "Подходящих доменов не найдено", 13, color=MUTED).pack(anchor="w")
            self.top_frame.pack(fill="x")
            return

        # Топ-3
        self.top_frame.pack(fill="x")
        for i, r in enumerate(good[:3]):
            row = fr(self.top_frame, bg=CARD, padx=14, pady=10)
            row.pack(fill="x", pady=(0, 6))

            left = fr(row, bg=CARD)
            left.pack(side="left", fill="x", expand=True)

            marker = "●" if i == 0 else "○"
            mc = GREEN if i == 0 else MUTED
            self._lbl(left, f"{marker}  {r['domain']}", 13, bold=(i==0), color=mc).pack(anchor="w")
            self._lbl(left, f"{r['latency_ms']} ms", 11, color=MUTED).pack(anchor="w")

            btn = tk.Button(row, text="Copy",
                            font=(FONT, 12), bg=CARD2, fg=ACCENT,
                            relief="flat", bd=0, padx=10, pady=4,
                            activebackground=SEP, activeforeground=ACCENT,
                            highlightthickness=0, cursor=CUR)
            btn.config(command=lambda d=r["domain"], b=btn: self._copy(d, b))
            btn.pack(side="right", padx=(8, 0))

        # Остальные
        others = good[3:]
        if others:
            fr(self.res_frame, bg=SEP, height=1).pack(fill="x", pady=(4, 8))
            self.others_frame.pack(fill="x")
            grid = fr(self.others_frame, bg=BG)
            grid.pack(fill="x")
            grid.columnconfigure(0, weight=1)
            grid.columnconfigure(1, weight=1)
            for idx, r in enumerate(others):
                self._lbl(grid, r["domain"], 11, color=MUTED).grid(
                    row=idx//2, column=idx%2, sticky="w", padx=(0, 10), pady=1)

    def _finish(self):
        self.progress.stop()
        self.progress.pack_forget()
        self.scan_btn.config(state="normal", text="Сканировать")


if __name__ == "__main__":
    app = App()
    app.mainloop()
