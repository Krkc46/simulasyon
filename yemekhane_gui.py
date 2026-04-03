import simpy
import simpy.rt
import random
import threading
import tkinter as tk

# ==========================================
# KONFİGÜRASYON VE SİSTEM DEĞİŞKENLERİ
# ==========================================
NUM_SERVERS = 4
NUM_CASHIERS = 1
SEATING_CAPACITY = 15
SIM_TIME = 120

ARRIVAL_MEAN = 1.0
SERVING_MEAN = 3.0
SERVING_STD = 0.5
CASHIER_MEAN = 0.5
EATING_MEAN = 20.0

# GUI için anlık durumu tutan global sözlük
state = {
    's_queue': 0, 's_active': 0,
    'c_queue': 0, 'c_active': 0,
    't_queue': 0, 't_active': 0,
    'total_in': 0, 'total_out': 0,
    'current_time': 0.0,
    'is_finished': False
}

class Cafeteria:
    def __init__(self, env):
        self.env = env
        self.server = simpy.Resource(env, NUM_SERVERS)
        self.cashier = simpy.Resource(env, NUM_CASHIERS)
        self.seating = simpy.Resource(env, SEATING_CAPACITY)

def student(env, cafeteria):
    state['total_in'] += 1
    
    # 1. Yemek Dağıtım Bankosu
    state['s_queue'] += 1
    with cafeteria.server.request() as req:
        yield req
        state['s_queue'] -= 1
        state['s_active'] += 1
        yield env.timeout(max(0.1, random.normalvariate(SERVING_MEAN, SERVING_STD)))
        state['s_active'] -= 1

    # 2. Kasa / Ödeme
    state['c_queue'] += 1
    with cafeteria.cashier.request() as req:
        yield req
        state['c_queue'] -= 1
        state['c_active'] += 1
        yield env.timeout(random.expovariate(1.0 / CASHIER_MEAN))
        state['c_active'] -= 1

    # 3. Masa / Oturma
    state['t_queue'] += 1
    with cafeteria.seating.request() as req:
        yield req
        state['t_queue'] -= 1
        state['t_active'] += 1
        yield env.timeout(random.expovariate(1.0 / EATING_MEAN))
        state['t_active'] -= 1
        
    state['total_out'] += 1

def setup(env, cafeteria):
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_MEAN))
        env.process(student(env, cafeteria))

def monitor_time(env):
    """Zamanı GUI'ye akıcı yansıtmak için bir takip süreci"""
    while True:
        state['current_time'] = env.now
        # Simülasyondaki her 0.1 dakikada bir state'i kaydet
        yield env.timeout(0.1)

def run_simulation():
    """Simülasyon motorunu çalıştıran asıl altyapı"""
    random.seed(42)
    
    # factor = 1.0 (GUI çok daha akıcı oynasın diye hızı 1 yaptık, isterseniz yine 2 yapabilirsiniz)
    env = simpy.rt.RealtimeEnvironment(factor=1.0, strict=False)
    cafeteria = Cafeteria(env)
    
    env.process(setup(env, cafeteria))
    env.process(monitor_time(env))
    
    env.run(until=SIM_TIME)
    state['is_finished'] = True

# ==========================================
# GÖRSEL MASAÜSTÜ ARAYÜZ (GUI) İNŞASI
# ==========================================
def create_dashboard():
    root = tk.Tk()
    root.title("Yemekhane Simülasyon Pano")
    root.geometry("900x700")
    # Koyu modern bir arka plan
    root.configure(bg="#2d3436")

    # Etiket üretici yardımcı fonksiyon
    def make_label(parent, text, font_size, color="#dfe6e9", bold=False, wraplength=850):
        w = "bold" if bold else "normal"
        # Emojilerin Windows/Mac'te düzgün çıkması için Segoe UI Emoji kullanıyoruz
        lbl = tk.Label(parent, text=text, font=("Segoe UI Emoji", font_size, w), bg="#2d3436", fg=color, justify="left", wraplength=wraplength)
        lbl.pack(anchor="w", pady=2, padx=20)
        return lbl

    # Üst Başlık
    tk.Label(root, text="🏢 YEMEKHANE CANLI GÖSTERİM", font=("Segoe UI", 24, "bold"), bg="#2d3436", fg="#00cec9").pack(pady=20)
    
    labels = {}
    labels['time'] = tk.Label(root, text="⏱ Simülasyon Başlıyor...", font=("Segoe UI", 16), bg="#2d3436", fg="#fdcb6e")
    labels['time'].pack(pady=5)

    # --- Banko Pano ---
    tk.Frame(root, height=2, bg="#636e72").pack(fill="x", padx=20, pady=10)
    make_label(root, "🍲 Yemek Dağıtım Bankosu", 16, "#74b9ff", bold=True)
    make_label(root, "Sırada Bekleyenler:", 12)
    labels['s_q'] = make_label(root, "", 20)
    make_label(root, "Hizmet Veren Bankolar:", 12)
    labels['s_a'] = make_label(root, "", 20, color="#ffffff")

    # --- Kasa Pano ---
    tk.Frame(root, height=2, bg="#636e72").pack(fill="x", padx=20, pady=10)
    make_label(root, "💵 Kasa & Ödeme", 16, "#55efc4", bold=True)
    make_label(root, "Kasa Bekleyenler:", 12)
    labels['c_q'] = make_label(root, "", 20)
    make_label(root, "Çalışan Kasalar:", 12)
    labels['c_a'] = make_label(root, "", 20, color="#ffffff")

    # --- Oturma Alanı Pano ---
    tk.Frame(root, height=2, bg="#636e72").pack(fill="x", padx=20, pady=10)
    make_label(root, "🪑 Oturma Alanı (Kapasite: 15)", 16, "#ffeaa7", bold=True)
    make_label(root, "Ayakta Tepsiyle Bekleyenler:", 12)
    labels['t_q'] = make_label(root, "", 20)
    make_label(root, "Masaların Durumu:", 12)
    labels['t_a'] = make_label(root, "", 20, color="#ffffff")

    # --- Alt Özet ---
    tk.Frame(root, height=2, bg="#636e72").pack(fill="x", padx=20, pady=10)
    labels['stats'] = tk.Label(root, text="", font=("Segoe UI", 16, "bold"), bg="#2d3436", fg="#fab1a0")
    labels['stats'].pack(pady=10)

    # 1. Arka planda Simülasyonu başlat (Thread kullanılıyor, bu sayede GUI donmaz)
    sim_thread = threading.Thread(target=run_simulation, daemon=True)
    sim_thread.start()

    # 2. Arayüz Güncelleyici Döngü (Ekrana sürekli Simülasyondan verileri çeker)
    def update_gui():
        labels['time'].config(text=f"⏱ Zaman: {state['current_time']:5.1f} / {SIM_TIME} dk")
        
        # Simgeli Gösterimler
        labels['s_q'].config(text=f"{'🚶 ' * state['s_queue']}")
        labels['s_a'].config(text=f"{'👨‍🍳 ' * state['s_active']}{'➖ ' * (NUM_SERVERS - state['s_active'])}")
        
        labels['c_q'].config(text=f"{'🚶 ' * state['c_queue']}")
        labels['c_a'].config(text=f"{'💳 ' * state['c_active']}{'➖ ' * (NUM_CASHIERS - state['c_active'])}")
        
        labels['t_q'].config(text=f"{'🧍 ' * state['t_queue']}")
        labels['t_a'].config(text=f"{'🍽️ ' * state['t_active']}{'🪑 ' * (SEATING_CAPACITY - state['t_active'])}")
        
        labels['stats'].config(text=f"Sisteme Giren: {state['total_in']}  |  Yemeğini Bitiren: {state['total_out']}  |  İçeride Kalan: {state['total_in'] - state['total_out']}")
        
        # Simülasyon bitti mi diye kontrol et
        if state['is_finished']:
            labels['time'].config(text=f"✅ SİMÜLASYON BAŞARIYLA TAMAMLANDI")
        else:
            # Bitmediyse 100 milisaniye sonra ekrandaki verileri tekrar yenile
            root.after(100, update_gui)

    # Döngüyü ateşle
    update_gui()
    
    # Uygulamayı açık tut
    root.mainloop()

if __name__ == "__main__":
    create_dashboard()
