import simpy
import simpy.rt
import random
import threading
import tkinter as tk
from tkinter import font as tkfont

# ==========================================
# KONFİGÜRASYON VE SİSTEM DEĞİŞKENLERİ
# ==========================================
# Bu değerler artık GUI'den değiştirilebilir; config dict üzerinden okunur.
config = {
    'NUM_SERVERS': 4,
    'NUM_CASHIERS': 1,
    'SEATING_CAPACITY': 15,
    'SIM_TIME': 120,
    'ARRIVAL_MEAN': 1.0,
    'SERVING_MEAN': 3.0,
    'SERVING_STD': 0.5,
    'CASHIER_MEAN': 0.5,
    'EATING_MEAN': 20.0,
}

# GUI için anlık durumu tutan global sözlük
state = {
    's_queue': 0, 's_active': 0,
    'c_queue': 0, 'c_active': 0,
    't_queue': 0, 't_active': 0,
    'total_in': 0, 'total_out': 0,
    'current_time': 0.0,
    'is_finished': False,
    'sim_started': False,
    # Zaman serisi verileri (istatistik grafikleri için)
    'history': {
        'time': [],
        's_queue_hist': [],
        'c_queue_hist': [],
        't_queue_hist': [],
        's_active_hist': [],
        'c_active_hist': [],
        't_active_hist': [],
    }
}

def reset_state():
    """State'i sıfırla (yeni simülasyon için)"""
    state['s_queue'] = 0
    state['s_active'] = 0
    state['c_queue'] = 0
    state['c_active'] = 0
    state['t_queue'] = 0
    state['t_active'] = 0
    state['total_in'] = 0
    state['total_out'] = 0
    state['current_time'] = 0.0
    state['is_finished'] = False
    state['sim_started'] = False
    state['history'] = {
        'time': [],
        's_queue_hist': [],
        'c_queue_hist': [],
        't_queue_hist': [],
        's_active_hist': [],
        'c_active_hist': [],
        't_active_hist': [],
    }

class Cafeteria:
    def __init__(self, env):
        self.env = env
        self.server = simpy.Resource(env, config['NUM_SERVERS'])
        self.cashier = simpy.Resource(env, config['NUM_CASHIERS'])
        self.seating = simpy.Resource(env, config['SEATING_CAPACITY'])

def student(env, cafeteria):
    state['total_in'] += 1
    
    # 1. Yemek Dağıtım Bankosu
    state['s_queue'] += 1
    with cafeteria.server.request() as req:
        yield req
        state['s_queue'] -= 1
        state['s_active'] += 1
        yield env.timeout(max(0.1, random.normalvariate(config['SERVING_MEAN'], config['SERVING_STD'])))
        state['s_active'] -= 1

    # 2. Kasa / Ödeme
    state['c_queue'] += 1
    with cafeteria.cashier.request() as req:
        yield req
        state['c_queue'] -= 1
        state['c_active'] += 1
        yield env.timeout(random.expovariate(1.0 / config['CASHIER_MEAN']))
        state['c_active'] -= 1

    # 3. Masa / Oturma
    state['t_queue'] += 1
    with cafeteria.seating.request() as req:
        yield req
        state['t_queue'] -= 1
        state['t_active'] += 1
        yield env.timeout(random.expovariate(1.0 / config['EATING_MEAN']))
        state['t_active'] -= 1
        
    state['total_out'] += 1

def setup(env, cafeteria):
    while True:
        yield env.timeout(random.expovariate(1.0 / config['ARRIVAL_MEAN']))
        env.process(student(env, cafeteria))

def monitor_time(env):
    """Zamanı GUI'ye akıcı yansıtmak için bir takip süreci"""
    while True:
        state['current_time'] = env.now
        # Tarihçeyi kaydet (her 1 dakikada bir)
        if len(state['history']['time']) == 0 or env.now - state['history']['time'][-1] >= 1.0:
            state['history']['time'].append(env.now)
            state['history']['s_queue_hist'].append(state['s_queue'])
            state['history']['c_queue_hist'].append(state['c_queue'])
            state['history']['t_queue_hist'].append(state['t_queue'])
            state['history']['s_active_hist'].append(state['s_active'])
            state['history']['c_active_hist'].append(state['c_active'])
            state['history']['t_active_hist'].append(state['t_active'])
        # Simülasyondaki her 0.1 dakikada bir state'i kaydet
        yield env.timeout(0.1)

def run_simulation():
    """Simülasyon motorunu çalıştıran asıl altyapı"""
    random.seed(42)
    
    env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)
    cafeteria = Cafeteria(env)
    
    env.process(setup(env, cafeteria))
    env.process(monitor_time(env))
    
    env.run(until=config['SIM_TIME'])
    state['is_finished'] = True

# ==========================================
# RENK PALETİ VE TEMA SABİTLERİ
# ==========================================
BG_DARK       = "#1a1a2e"
SIDEBAR_BG    = "#16213e"
SIDEBAR_HOVER = "#0f3460"
SIDEBAR_SEL   = "#e94560"
CARD_BG       = "#222640"
CARD_BORDER   = "#2d325a"
TEXT_PRIMARY  = "#eaf0fb"
TEXT_SECONDARY= "#8892b0"
ACCENT_BLUE   = "#64ffda"
ACCENT_YELLOW = "#ffd369"
ACCENT_GREEN  = "#55efc4"
ACCENT_PINK   = "#e94560"
ACCENT_PURPLE = "#a29bfe"
ACCENT_ORANGE = "#fdcb6e"
PROGRESS_BG   = "#2d325a"
INPUT_BG      = "#2d325a"
INPUT_FG      = "#eaf0fb"
INPUT_BORDER  = "#3d4270"

# ==========================================
# GÖRSEL MASAÜSTÜ ARAYÜZ (GUI) İNŞASI
# ==========================================
def create_dashboard():
    root = tk.Tk()
    root.title("🏢 Yemekhane Simülasyon Panosu")
    root.geometry("1200x780")
    root.configure(bg=BG_DARK)
    root.minsize(1050, 700)

    # ---- Font Tanımları ----
    try:
        title_font   = tkfont.Font(family="Segoe UI", size=20, weight="bold")
        heading_font = tkfont.Font(family="Segoe UI", size=16, weight="bold")
        body_font    = tkfont.Font(family="Segoe UI", size=13)
        small_font   = tkfont.Font(family="Segoe UI", size=11)
        emoji_font   = tkfont.Font(family="Segoe UI Emoji", size=18)
        emoji_big    = tkfont.Font(family="Segoe UI Emoji", size=24)
        stat_font    = tkfont.Font(family="Segoe UI", size=28, weight="bold")
        sidebar_font = tkfont.Font(family="Segoe UI", size=13, weight="bold")
        input_font   = tkfont.Font(family="Segoe UI", size=13)
        input_label_font = tkfont.Font(family="Segoe UI", size=11)
    except Exception:
        title_font = heading_font = body_font = small_font = emoji_font = None
        emoji_big = stat_font = sidebar_font = input_font = input_label_font = None

    # Mevcut sayfa referansı
    current_page = tk.StringVar(value="settings")

    # ==========================================
    # SOL SIDEBAR
    # ==========================================
    sidebar = tk.Frame(root, bg=SIDEBAR_BG, width=220)
    sidebar.pack(side="left", fill="y")
    sidebar.pack_propagate(False)

    # Sidebar Başlık
    tk.Label(sidebar, text="🏢", font=emoji_big, bg=SIDEBAR_BG, fg=ACCENT_BLUE).pack(pady=(20, 5))
    tk.Label(sidebar, text="SİMÜLASYON", font=sidebar_font, bg=SIDEBAR_BG, fg=ACCENT_BLUE).pack()
    tk.Label(sidebar, text="PANOSU", font=sidebar_font, bg=SIDEBAR_BG, fg=TEXT_SECONDARY).pack(pady=(0, 15))

    # Separator
    tk.Frame(sidebar, height=2, bg=CARD_BORDER).pack(fill="x", padx=15, pady=5)

    # Sidebar Menü Tanımları
    menu_items = [
        ("settings",  "⚙️", "Ayarlar"),
        ("overview",  "📊", "Genel Bakış"),
        ("serving",   "🍲", "Yemek Bankosu"),
        ("cashier",   "💵", "Kasa Sırası"),
        ("seating",   "🪑", "Oturma Alanı"),
        ("stats",     "📈", "İstatistikler"),
    ]

    sidebar_buttons = {}

    def switch_page(page_key):
        current_page.set(page_key)
        for key, btn in sidebar_buttons.items():
            if key == page_key:
                btn.configure(bg=SIDEBAR_SEL, fg="#ffffff")
            else:
                btn.configure(bg=SIDEBAR_BG, fg=TEXT_SECONDARY)

    for key, icon, label in menu_items:
        btn = tk.Button(
            sidebar, text=f"  {icon}  {label}", font=sidebar_font,
            bg=SIDEBAR_BG, fg=TEXT_SECONDARY,
            activebackground=SIDEBAR_HOVER, activeforeground="#ffffff",
            bd=0, relief="flat", anchor="w", padx=15, pady=10,
            cursor="hand2",
            command=lambda k=key: switch_page(k)
        )
        btn.pack(fill="x", padx=8, pady=2)
        sidebar_buttons[key] = btn

        def on_enter(e, b=btn, k=key):
            if current_page.get() != k:
                b.configure(bg=SIDEBAR_HOVER, fg="#ffffff")
        def on_leave(e, b=btn, k=key):
            if current_page.get() != k:
                b.configure(bg=SIDEBAR_BG, fg=TEXT_SECONDARY)
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)

    # İlk seçili butonu ayarla
    sidebar_buttons["settings"].configure(bg=SIDEBAR_SEL, fg="#ffffff")

    # Sidebar Alt Bilgi
    tk.Frame(sidebar, height=2, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10, side="bottom")
    tk.Label(sidebar, text="SimPy Motoru", font=small_font, bg=SIDEBAR_BG, fg=TEXT_SECONDARY).pack(side="bottom", pady=(0, 15))

    # ==========================================
    # SAĞ ANA İÇERİK ALANI
    # ==========================================
    main_area = tk.Frame(root, bg=BG_DARK)
    main_area.pack(side="right", fill="both", expand=True)

    # --- Üst Zaman Barı ---
    topbar = tk.Frame(main_area, bg=CARD_BG, height=60)
    topbar.pack(fill="x", padx=15, pady=(15, 5))
    topbar.pack_propagate(False)

    time_label = tk.Label(topbar, text="⏱ Parametreleri ayarlayıp simülasyonu başlatın", font=heading_font, bg=CARD_BG, fg=ACCENT_YELLOW)
    time_label.pack(side="left", padx=20, pady=10)

    status_label = tk.Label(topbar, text="● BEKLEMEDE", font=small_font, bg=CARD_BG, fg=ACCENT_ORANGE)
    status_label.pack(side="right", padx=20, pady=10)

    # Progress Bar (Canvas ile)
    progress_frame = tk.Frame(main_area, bg=BG_DARK, height=8)
    progress_frame.pack(fill="x", padx=15, pady=(0, 10))
    progress_canvas = tk.Canvas(progress_frame, height=6, bg=PROGRESS_BG, highlightthickness=0)
    progress_canvas.pack(fill="x")

    # ==========================================
    # İÇERİK SAYFALARI (Frames)
    # ==========================================
    content_frame = tk.Frame(main_area, bg=BG_DARK)
    content_frame.pack(fill="both", expand=True, padx=15, pady=5)

    pages = {}
    page_labels = {}

    # ---- Yardımcı Fonksiyonlar ----
    def make_card(parent, title="", title_color=ACCENT_BLUE):
        card = tk.Frame(parent, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        if title:
            tk.Label(card, text=title, font=heading_font, bg=CARD_BG, fg=title_color).pack(anchor="w", padx=15, pady=(12, 5))
            tk.Frame(card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=(0, 8))
        return card

    def make_metric(parent, label_text, value_text="0", color=TEXT_PRIMARY):
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", padx=20, pady=4)
        tk.Label(row, text=label_text, font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(side="left")
        val = tk.Label(row, text=value_text, font=body_font, bg=CARD_BG, fg=color)
        val.pack(side="right")
        return val

    def make_emoji_display(parent, text="", font_to_use=None):
        lbl = tk.Label(parent, text=text, font=font_to_use or emoji_font, bg=CARD_BG, fg=TEXT_PRIMARY, wraplength=700, justify="left")
        lbl.pack(anchor="w", padx=20, pady=5)
        return lbl

    # ==========================================
    # SAYFA 0: AYARLAR (Parametre Girişi)
    # ==========================================
    p_settings = tk.Frame(content_frame, bg=BG_DARK)
    pages["settings"] = p_settings
    page_labels["settings"] = {}

    # Scrollable alan için Canvas
    settings_canvas = tk.Canvas(p_settings, bg=BG_DARK, highlightthickness=0)
    settings_scrollbar = tk.Scrollbar(p_settings, orient="vertical", command=settings_canvas.yview)
    settings_inner = tk.Frame(settings_canvas, bg=BG_DARK)

    settings_inner.bind("<Configure>", lambda e: settings_canvas.configure(scrollregion=settings_canvas.bbox("all")))
    settings_canvas.create_window((0, 0), window=settings_inner, anchor="nw")
    settings_canvas.configure(yscrollcommand=settings_scrollbar.set)

    settings_canvas.pack(side="left", fill="both", expand=True)
    settings_scrollbar.pack(side="right", fill="y")

    # Mouse wheel scroll
    def _on_mousewheel(event):
        settings_canvas.yview_scroll(int(-1*(event.delta/120)), "units")
    settings_canvas.bind_all("<MouseWheel>", _on_mousewheel)

    # --- Ayarlar İçeriği ---
    # Parametre giriş alanı üretici
    param_entries = {}

    def make_param_row(parent, label, key, default_val, description="", val_type="int"):
        """Bir parametre satırı oluşturur: etiket + giriş kutusu"""
        row = tk.Frame(parent, bg=CARD_BG)
        row.pack(fill="x", padx=15, pady=6)

        # Sol taraf: etiket + açıklama
        left = tk.Frame(row, bg=CARD_BG)
        left.pack(side="left", fill="x", expand=True)
        tk.Label(left, text=label, font=body_font, bg=CARD_BG, fg=TEXT_PRIMARY, anchor="w").pack(anchor="w")
        if description:
            tk.Label(left, text=description, font=input_label_font, bg=CARD_BG, fg=TEXT_SECONDARY, anchor="w").pack(anchor="w")

        # Sağ taraf: giriş kutusu
        right = tk.Frame(row, bg=CARD_BG)
        right.pack(side="right")

        sv = tk.StringVar(value=str(default_val))
        entry = tk.Entry(right, textvariable=sv, font=input_font,
                         bg=INPUT_BG, fg=INPUT_FG, insertbackground=INPUT_FG,
                         highlightbackground=INPUT_BORDER, highlightcolor=ACCENT_BLUE,
                         highlightthickness=2, relief="flat", width=10, justify="center")
        entry.pack(padx=5, pady=2)

        param_entries[key] = (sv, val_type)
        return sv

    # ---- Kaynak Sayıları Kartı ----
    res_card = make_card(settings_inner, "🏗️ Kaynak Kapasiteleri", ACCENT_BLUE)
    res_card.pack(fill="x", pady=5, padx=5)

    make_param_row(res_card, "🍲 Banko Sayısı", "NUM_SERVERS", config['NUM_SERVERS'],
                   "Yemek dağıtım görevlisi sayısı")
    make_param_row(res_card, "💵 Kasa Sayısı", "NUM_CASHIERS", config['NUM_CASHIERS'],
                   "Ödeme noktası sayısı")
    make_param_row(res_card, "🪑 Oturma Kapasitesi", "SEATING_CAPACITY", config['SEATING_CAPACITY'],
                   "Toplam masa / sandalye sayısı")
    tk.Frame(res_card, height=8, bg=CARD_BG).pack()

    # ---- Süre Parametreleri Kartı ----
    time_card = make_card(settings_inner, "⏱ Süre Parametreleri (dakika)", ACCENT_YELLOW)
    time_card.pack(fill="x", pady=5, padx=5)

    make_param_row(time_card, "Simülasyon Süresi", "SIM_TIME", config['SIM_TIME'],
                   "Toplam simülasyon uzunluğu (dakika)")
    make_param_row(time_card, "Ortalama Geliş Aralığı", "ARRIVAL_MEAN", config['ARRIVAL_MEAN'],
                   "Öğrencilerin ortalama geliş aralığı (dk)", val_type="float")
    make_param_row(time_card, "Ort. Yemek Alma Süresi (μ)", "SERVING_MEAN", config['SERVING_MEAN'],
                   "Normal dağılım ortalaması (dk)", val_type="float")
    make_param_row(time_card, "Yemek Alma Std. Sapma (σ)", "SERVING_STD", config['SERVING_STD'],
                   "Normal dağılım standart sapması", val_type="float")
    make_param_row(time_card, "Ort. Ödeme Süresi", "CASHIER_MEAN", config['CASHIER_MEAN'],
                   "Üstel dağılım ortalaması (dk)", val_type="float")
    make_param_row(time_card, "Ort. Yemek Yeme Süresi", "EATING_MEAN", config['EATING_MEAN'],
                   "Üstel dağılım ortalaması (dk)", val_type="float")
    tk.Frame(time_card, height=8, bg=CARD_BG).pack()

    # ---- Başlat Butonu ----
    btn_frame = tk.Frame(settings_inner, bg=BG_DARK)
    btn_frame.pack(fill="x", pady=15, padx=5)

    feedback_label = tk.Label(btn_frame, text="", font=small_font, bg=BG_DARK, fg=ACCENT_PINK)
    feedback_label.pack(pady=(0, 5))

    def start_simulation():
        """Parametreleri oku, doğrula ve simülasyonu başlat"""
        if state['sim_started']:
            feedback_label.config(text="⚠️ Simülasyon zaten çalışıyor!", fg=ACCENT_ORANGE)
            return

        # Parametreleri oku ve doğrula
        errors = []
        for key, (sv, val_type) in param_entries.items():
            try:
                raw = sv.get().strip()
                if val_type == "int":
                    val = int(raw)
                    if val < 1:
                        errors.append(f"{key}: En az 1 olmalı")
                        continue
                else:
                    val = float(raw)
                    if val <= 0:
                        errors.append(f"{key}: Pozitif bir sayı olmalı")
                        continue
                config[key] = val
            except ValueError:
                errors.append(f"{key}: Geçerli bir sayı giriniz")

        if errors:
            feedback_label.config(text="❌ " + " | ".join(errors[:3]), fg=ACCENT_PINK)
            return

        # State sıfırla & simülasyonu başlat
        reset_state()
        state['sim_started'] = True
        feedback_label.config(text="✅ Simülasyon başlatıldı!", fg=ACCENT_GREEN)
        status_label.config(text="● ÇALIŞIYOR", fg=ACCENT_GREEN)
        time_label.config(text=f"⏱ Zaman: 0.0 / {int(config['SIM_TIME'])} dk")

        # Giriş alanlarını devre dışı bırak
        for key, (sv, vt) in param_entries.items():
            for w in settings_inner.winfo_children():
                _disable_entries(w)

        start_btn.config(state="disabled", bg=TEXT_SECONDARY, text="⏳ Simülasyon Çalışıyor...")

        # Simülasyonu arka planda başlat
        sim_thread = threading.Thread(target=run_simulation, daemon=True)
        sim_thread.start()

        # Genel bakışa geç
        switch_page("overview")

    def _disable_entries(widget):
        """Tüm Entry widget'larını devre dışı bırak"""
        if isinstance(widget, tk.Entry):
            widget.config(state="disabled")
        for child in widget.winfo_children():
            _disable_entries(child)

    start_btn = tk.Button(
        btn_frame, text="🚀  SİMÜLASYONU BAŞLAT", font=heading_font,
        bg=ACCENT_GREEN, fg="#1a1a2e",
        activebackground="#43d9a5", activeforeground="#1a1a2e",
        bd=0, relief="flat", padx=30, pady=12,
        cursor="hand2",
        command=start_simulation
    )
    start_btn.pack(pady=5)

    # Başlat butonu hover efekti
    def btn_enter(e):
        if start_btn['state'] != 'disabled':
            start_btn.configure(bg="#43d9a5")
    def btn_leave(e):
        if start_btn['state'] != 'disabled':
            start_btn.configure(bg=ACCENT_GREEN)
    start_btn.bind("<Enter>", btn_enter)
    start_btn.bind("<Leave>", btn_leave)

    # Bilgi notu
    tk.Label(btn_frame, text="💡 Parametreleri değiştirdikten sonra butona basarak simülasyonu başlatın.",
             font=input_label_font, bg=BG_DARK, fg=TEXT_SECONDARY, wraplength=600).pack(pady=10)

    # ==========================================
    # SAYFA 1: GENEL BAKIŞ (Scrollable)
    # ==========================================
    p_overview = tk.Frame(content_frame, bg=BG_DARK)
    pages["overview"] = p_overview
    page_labels["overview"] = {}

    # Scrollable alan
    ov_canvas = tk.Canvas(p_overview, bg=BG_DARK, highlightthickness=0)
    ov_scrollbar = tk.Scrollbar(p_overview, orient="vertical", command=ov_canvas.yview)
    ov_inner = tk.Frame(ov_canvas, bg=BG_DARK)

    ov_inner.bind("<Configure>", lambda e: ov_canvas.configure(scrollregion=ov_canvas.bbox("all")))
    ov_canvas.create_window((0, 0), window=ov_inner, anchor="nw")
    ov_canvas.configure(yscrollcommand=ov_scrollbar.set)

    ov_canvas.pack(side="left", fill="both", expand=True)
    ov_scrollbar.pack(side="right", fill="y")

    # İçerik genişliğini canvas'a bağla
    def _ov_resize(event):
        ov_canvas.itemconfig(ov_canvas.find_withtag("all")[0], width=event.width)
    ov_canvas.bind("<Configure>", _ov_resize)

    # Üst satır: 3 mini kart (yan yana — bunlar küçük, sığar)
    ov_top = tk.Frame(ov_inner, bg=BG_DARK)
    ov_top.pack(fill="x", pady=(0, 10))

    for i, (metric_title, metric_color, metric_key) in enumerate([
        ("Sisteme Giren", ACCENT_BLUE, "total_in"),
        ("Yemeğini Bitiren", ACCENT_GREEN, "total_out"),
        ("İçeride Kalan", ACCENT_PINK, "inside"),
    ]):
        mini_card = tk.Frame(ov_top, bg=CARD_BG, highlightbackground=CARD_BORDER, highlightthickness=1)
        mini_card.pack(side="left", fill="both", expand=True, padx=(0 if i == 0 else 5, 0 if i == 2 else 5), pady=2)
        tk.Label(mini_card, text=metric_title, font=small_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(pady=(10, 0))
        val_lbl = tk.Label(mini_card, text="0", font=stat_font, bg=CARD_BG, fg=metric_color)
        val_lbl.pack(pady=(0, 10))
        page_labels["overview"][metric_key] = val_lbl

    # İstasyon kartları — ALT ALTA (dikey düzen)
    for i, (station_title, station_color, q_key, a_key, emoji_q, emoji_a) in enumerate([
        ("🍲 Yemek Bankosu", ACCENT_BLUE, "s_queue", "s_active", "🚶", "👨‍🍳"),
        ("💵 Kasa & Ödeme", ACCENT_GREEN, "c_queue", "c_active", "🚶", "💳"),
        ("🪑 Oturma Alanı", ACCENT_YELLOW, "t_queue", "t_active", "🧍", "🍽️"),
    ]):
        card = make_card(ov_inner, station_title, station_color)
        card.pack(fill="x", pady=4)

        q_lbl = make_metric(card, "Sırada Bekleyen:", "0", ACCENT_ORANGE)
        a_lbl = make_metric(card, "Aktif Hizmet:", "0", ACCENT_GREEN)
        emoji_lbl = make_emoji_display(card, "")
        
        page_labels["overview"][f"ov_{q_key}"] = q_lbl
        page_labels["overview"][f"ov_{a_key}"] = a_lbl
        page_labels["overview"][f"ov_emoji_{q_key}"] = emoji_lbl
        page_labels["overview"][f"ov_eq_{q_key}"] = emoji_q
        page_labels["overview"][f"ov_ea_{a_key}"] = emoji_a

    # ==========================================
    # SAYFA 2: YEMEK BANKOSU DETAY
    # ==========================================
    p_serving = tk.Frame(content_frame, bg=BG_DARK)
    pages["serving"] = p_serving
    page_labels["serving"] = {}

    sv_card = make_card(p_serving, "🍲 Yemek Dağıtım Bankosu — Detay", ACCENT_BLUE)
    sv_card.pack(fill="both", expand=True, pady=5)

    page_labels["serving"]["info"] = tk.Label(sv_card, text="", font=small_font, bg=CARD_BG, fg=TEXT_SECONDARY)
    page_labels["serving"]["info"].pack(anchor="w", padx=20, pady=(5, 10))

    page_labels["serving"]["queue"] = make_metric(sv_card, "Sırada Bekleyen Öğrenci:", "0", ACCENT_ORANGE)
    page_labels["serving"]["active"] = make_metric(sv_card, "Aktif Çalışan Banko:", "0", ACCENT_GREEN)
    page_labels["serving"]["idle"] = make_metric(sv_card, "Boşta Bekleyen Banko:", "0", TEXT_SECONDARY)

    tk.Frame(sv_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(sv_card, text="Sıra Görünümü:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    page_labels["serving"]["emoji_q"] = make_emoji_display(sv_card, "", emoji_big)

    tk.Label(sv_card, text="Banko Durumu:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(10, 0))
    page_labels["serving"]["emoji_a"] = make_emoji_display(sv_card, "", emoji_big)

    tk.Frame(sv_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(sv_card, text="Kapasite Kullanımı:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    sv_util_canvas = tk.Canvas(sv_card, height=28, bg=PROGRESS_BG, highlightthickness=0)
    sv_util_canvas.pack(fill="x", padx=20, pady=5)
    page_labels["serving"]["util_canvas"] = sv_util_canvas

    # ==========================================
    # SAYFA 3: KASA SIRASI DETAY
    # ==========================================
    p_cashier = tk.Frame(content_frame, bg=BG_DARK)
    pages["cashier"] = p_cashier
    page_labels["cashier"] = {}

    cs_card = make_card(p_cashier, "💵 Kasa & Ödeme Noktası — Detay", ACCENT_GREEN)
    cs_card.pack(fill="both", expand=True, pady=5)

    page_labels["cashier"]["info"] = tk.Label(cs_card, text="", font=small_font, bg=CARD_BG, fg=TEXT_SECONDARY)
    page_labels["cashier"]["info"].pack(anchor="w", padx=20, pady=(5, 10))

    page_labels["cashier"]["queue"] = make_metric(cs_card, "Sırada Bekleyen Öğrenci:", "0", ACCENT_ORANGE)
    page_labels["cashier"]["active"] = make_metric(cs_card, "Aktif Çalışan Kasa:", "0", ACCENT_GREEN)
    page_labels["cashier"]["idle"] = make_metric(cs_card, "Boşta Bekleyen Kasa:", "0", TEXT_SECONDARY)

    tk.Frame(cs_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(cs_card, text="Kasa Sırası Görünümü:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    page_labels["cashier"]["emoji_q"] = make_emoji_display(cs_card, "", emoji_big)

    tk.Label(cs_card, text="Kasa Durumu:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(10, 0))
    page_labels["cashier"]["emoji_a"] = make_emoji_display(cs_card, "", emoji_big)

    tk.Frame(cs_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(cs_card, text="Kapasite Kullanımı:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    cs_util_canvas = tk.Canvas(cs_card, height=28, bg=PROGRESS_BG, highlightthickness=0)
    cs_util_canvas.pack(fill="x", padx=20, pady=5)
    page_labels["cashier"]["util_canvas"] = cs_util_canvas

    # ==========================================
    # SAYFA 4: OTURMA ALANI DETAY
    # ==========================================
    p_seating = tk.Frame(content_frame, bg=BG_DARK)
    pages["seating"] = p_seating
    page_labels["seating"] = {}

    st_card = make_card(p_seating, "🪑 Oturma Alanı — Detay", ACCENT_YELLOW)
    st_card.pack(fill="both", expand=True, pady=5)

    page_labels["seating"]["info"] = tk.Label(st_card, text="", font=small_font, bg=CARD_BG, fg=TEXT_SECONDARY)
    page_labels["seating"]["info"].pack(anchor="w", padx=20, pady=(5, 10))

    page_labels["seating"]["queue"] = make_metric(st_card, "Tepsiyle Ayakta Bekleyen:", "0", ACCENT_ORANGE)
    page_labels["seating"]["active"] = make_metric(st_card, "Masada Oturan:", "0", ACCENT_GREEN)
    page_labels["seating"]["idle"] = make_metric(st_card, "Boş Masa:", "0", TEXT_SECONDARY)

    tk.Frame(st_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(st_card, text="Ayakta Bekleyenler:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    page_labels["seating"]["emoji_q"] = make_emoji_display(st_card, "", emoji_big)

    tk.Label(st_card, text="Masa Durumu:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20, pady=(10, 0))
    page_labels["seating"]["emoji_a"] = make_emoji_display(st_card, "", emoji_big)

    tk.Frame(st_card, height=1, bg=CARD_BORDER).pack(fill="x", padx=15, pady=10)
    tk.Label(st_card, text="Doluluk Oranı:", font=body_font, bg=CARD_BG, fg=TEXT_SECONDARY).pack(anchor="w", padx=20)
    st_util_canvas = tk.Canvas(st_card, height=28, bg=PROGRESS_BG, highlightthickness=0)
    st_util_canvas.pack(fill="x", padx=20, pady=5)
    page_labels["seating"]["util_canvas"] = st_util_canvas

    # ==========================================
    # SAYFA 5: İSTATİSTİKLER
    # ==========================================
    p_stats = tk.Frame(content_frame, bg=BG_DARK)
    pages["stats"] = p_stats
    page_labels["stats"] = {}

    fl_card = make_card(p_stats, "📈 Anlık Akış İstatistikleri", ACCENT_PURPLE)
    fl_card.pack(fill="x", pady=5)

    page_labels["stats"]["total_in"] = make_metric(fl_card, "Sisteme Giren Toplam:", "0", ACCENT_BLUE)
    page_labels["stats"]["total_out"] = make_metric(fl_card, "Yemeğini Bitiren:", "0", ACCENT_GREEN)
    page_labels["stats"]["inside"] = make_metric(fl_card, "Şu An İçeride:", "0", ACCENT_PINK)
    page_labels["stats"]["throughput"] = make_metric(fl_card, "Verimlilik (çıkan/dk):", "0.00", ACCENT_YELLOW)
    tk.Frame(fl_card, height=5, bg=CARD_BG).pack()

    cmp_card = make_card(p_stats, "📊 Kuyruk Karşılaştırma (Anlık)", ACCENT_ORANGE)
    cmp_card.pack(fill="x", pady=5)

    page_labels["stats"]["cmp_serving"] = make_metric(cmp_card, "🍲 Banko Sırası:", "0", ACCENT_BLUE)
    page_labels["stats"]["cmp_cashier"] = make_metric(cmp_card, "💵 Kasa Sırası:", "0", ACCENT_GREEN)
    page_labels["stats"]["cmp_seating"] = make_metric(cmp_card, "🪑 Masa Sırası:", "0", ACCENT_YELLOW)
    tk.Frame(cmp_card, height=5, bg=CARD_BG).pack()

    hist_card = make_card(p_stats, "📉 Kuyruk Zirve Değerleri (Tarihçe)", ACCENT_BLUE)
    hist_card.pack(fill="x", pady=5)

    page_labels["stats"]["peak_serving"] = make_metric(hist_card, "🍲 Banko Sırası En Yüksek:", "0", ACCENT_BLUE)
    page_labels["stats"]["peak_cashier"] = make_metric(hist_card, "💵 Kasa Sırası En Yüksek:", "0", ACCENT_GREEN)
    page_labels["stats"]["peak_seating"] = make_metric(hist_card, "🪑 Masa Sırası En Yüksek:", "0", ACCENT_YELLOW)
    tk.Frame(hist_card, height=5, bg=CARD_BG).pack()

    # ==========================================
    # SAYFA GEÇİŞ MEKANİZMASI
    # ==========================================
    def show_page(page_key):
        for key, frame in pages.items():
            if key == page_key:
                frame.pack(fill="both", expand=True)
            else:
                frame.pack_forget()

    show_page("settings")

    # ==========================================
    # CANVAS PROGRESS BAR ÇİZİCİ
    # ==========================================
    def draw_progress_bar(canvas, ratio, color=ACCENT_BLUE, label=""):
        canvas.delete("all")
        w = canvas.winfo_width()
        h = canvas.winfo_height()
        if w < 10:
            w = 400
        if h < 5:
            h = 28
        canvas.create_rectangle(0, 0, w, h, fill=PROGRESS_BG, outline="")
        fill_w = int(w * min(ratio, 1.0))
        if fill_w > 0:
            canvas.create_rectangle(0, 0, fill_w, h, fill=color, outline="")
        pct_text = f"{ratio*100:.0f}%"
        if label:
            pct_text = f"{label}  {pct_text}"
        canvas.create_text(w // 2, h // 2, text=pct_text, fill="#ffffff", font=small_font)

    # ==========================================
    # ARAYÜZ GÜNCELLEYİCİ DÖNGÜ
    # ==========================================
    def update_gui():
        ct = state['current_time']
        sim_time = int(config['SIM_TIME'])
        ns = int(config['NUM_SERVERS'])
        nc = int(config['NUM_CASHIERS'])
        sc = int(config['SEATING_CAPACITY'])

        if state['sim_started']:
            time_label.config(text=f"⏱ Zaman: {ct:5.1f} / {sim_time} dk")
            ratio = ct / config['SIM_TIME'] if config['SIM_TIME'] > 0 else 0
            draw_progress_bar(progress_canvas, ratio, ACCENT_BLUE)

        active_page = current_page.get()
        show_page(active_page)

        sq = state['s_queue']
        sa = state['s_active']
        cq = state['c_queue']
        ca = state['c_active']
        tq = state['t_queue']
        ta = state['t_active']
        ti = state['total_in']
        to_ = state['total_out']
        inside = ti - to_

        # ---- Genel Bakış ----
        ol = page_labels["overview"]
        ol["total_in"].config(text=str(ti))
        ol["total_out"].config(text=str(to_))
        ol["inside"].config(text=str(inside))

        for q_key, q_val, a_key, a_val, cap in [
            ("s_queue", sq, "s_active", sa, ns),
            ("c_queue", cq, "c_active", ca, nc),
            ("t_queue", tq, "t_active", ta, sc),
        ]:
            ol[f"ov_{q_key}"].config(text=str(q_val))
            ol[f"ov_{a_key}"].config(text=str(a_val))
            eq = ol[f"ov_eq_{q_key}"]
            ea = ol[f"ov_ea_{a_key}"]
            emoji_text = f"{eq} " * min(q_val, 20)
            if q_val > 20:
                emoji_text += f"(+{q_val - 20})"
            emoji_text += "  |  "
            emoji_text += f"{ea} " * a_val + "➖ " * (cap - a_val)
            ol[f"ov_emoji_{q_key}"].config(text=emoji_text)

        # ---- Banko Detay ----
        sl = page_labels["serving"]
        sl["info"].config(text=f"Toplam Banko Sayısı: {ns}  |  Dağılım: Normal(μ={config['SERVING_MEAN']}, σ={config['SERVING_STD']})")
        sl["queue"].config(text=str(sq))
        sl["active"].config(text=f"{sa} / {ns}")
        sl["idle"].config(text=str(ns - sa))
        q_emoji = ("🚶 " * min(sq, 30))
        if sq > 30:
            q_emoji += f"(+{sq - 30} kişi)"
        sl["emoji_q"].config(text=q_emoji if sq > 0 else "— Sıra yok —")
        sl["emoji_a"].config(text=f"{'👨‍🍳 ' * sa}{'➖ ' * (ns - sa)}")
        if ns > 0:
            draw_progress_bar(sl["util_canvas"], sa / ns, ACCENT_BLUE, f"{sa}/{ns}")

        # ---- Kasa Detay ----
        cl = page_labels["cashier"]
        cl["info"].config(text=f"Toplam Kasa Sayısı: {nc}  |  Dağılım: Üstel(λ=1/{config['CASHIER_MEAN']})")
        cl["queue"].config(text=str(cq))
        cl["active"].config(text=f"{ca} / {nc}")
        cl["idle"].config(text=str(nc - ca))
        cq_emoji = ("🚶 " * min(cq, 30))
        if cq > 30:
            cq_emoji += f"(+{cq - 30} kişi)"
        cl["emoji_q"].config(text=cq_emoji if cq > 0 else "— Sıra yok —")
        cl["emoji_a"].config(text=f"{'💳 ' * ca}{'➖ ' * (nc - ca)}")
        if nc > 0:
            draw_progress_bar(cl["util_canvas"], ca / nc, ACCENT_GREEN, f"{ca}/{nc}")

        # ---- Oturma Alanı Detay ----
        tl = page_labels["seating"]
        tl["info"].config(text=f"Toplam Masa Kapasitesi: {sc}  |  Ort. Yemek Süresi: {config['EATING_MEAN']} dk (Üstel)")
        tl["queue"].config(text=str(tq))
        tl["active"].config(text=f"{ta} / {sc}")
        tl["idle"].config(text=str(sc - ta))
        tq_emoji = ("🧍 " * min(tq, 30))
        if tq > 30:
            tq_emoji += f"(+{tq - 30} kişi)"
        tl["emoji_q"].config(text=tq_emoji if tq > 0 else "— Bekleyen yok —")
        tl["emoji_a"].config(text=f"{'🍽️ ' * min(ta, 15)}{'🪑 ' * (sc - ta)}")
        if sc > 0:
            draw_progress_bar(tl["util_canvas"], ta / sc, ACCENT_YELLOW, f"{ta}/{sc}")

        # ---- İstatistikler ----
        stl = page_labels["stats"]
        stl["total_in"].config(text=str(ti))
        stl["total_out"].config(text=str(to_))
        stl["inside"].config(text=str(inside))
        throughput = to_ / ct if ct > 0 else 0
        stl["throughput"].config(text=f"{throughput:.2f} öğrenci/dk")

        stl["cmp_serving"].config(text=str(sq))
        stl["cmp_cashier"].config(text=str(cq))
        stl["cmp_seating"].config(text=str(tq))

        hist = state['history']
        peak_s = max(hist['s_queue_hist']) if hist['s_queue_hist'] else 0
        peak_c = max(hist['c_queue_hist']) if hist['c_queue_hist'] else 0
        peak_t = max(hist['t_queue_hist']) if hist['t_queue_hist'] else 0
        stl["peak_serving"].config(text=str(peak_s))
        stl["peak_cashier"].config(text=str(peak_c))
        stl["peak_seating"].config(text=str(peak_t))

        # Simülasyon durumu
        if state['is_finished']:
            time_label.config(text="✅ SİMÜLASYON BAŞARIYLA TAMAMLANDI", fg=ACCENT_GREEN)
            status_label.config(text="● BİTTİ", fg=ACCENT_ORANGE)
            draw_progress_bar(progress_canvas, 1.0, ACCENT_GREEN, "TAMAMLANDI")
        else:
            root.after(100, update_gui)

    # Döngüyü ateşle
    update_gui()
    
    root.mainloop()

if __name__ == "__main__":
    create_dashboard()
