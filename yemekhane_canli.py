import simpy
import simpy.rt  # Gerçek zamanlı (Realtime) simülasyon için
import random
import os

NUM_SERVERS = 4
NUM_CASHIERS = 1
SEATING_CAPACITY = 15
SIM_TIME = 120

ARRIVAL_MEAN = 1.0
SERVING_MEAN = 3.0
SERVING_STD = 0.5
CASHIER_MEAN = 0.5
EATING_MEAN = 20.0

# Anlık Durum Takibi İçin Sözlük (Kuyruklar ve aktif çalışanları tutar)
state = {
    's_queue': 0, 's_active': 0,
    'c_queue': 0, 'c_active': 0,
    't_queue': 0, 't_active': 0,
    'total_in': 0, 'total_out': 0
}

class Cafeteria:
    def __init__(self, env):
        self.env = env
        self.server = simpy.Resource(env, NUM_SERVERS)
        self.cashier = simpy.Resource(env, NUM_CASHIERS)
        self.seating = simpy.Resource(env, SEATING_CAPACITY)

def student(env, cafeteria):
    state['total_in'] += 1
    
    # 1. Banko
    state['s_queue'] += 1
    with cafeteria.server.request() as req:
        yield req
        state['s_queue'] -= 1
        state['s_active'] += 1
        yield env.timeout(max(0.1, random.normalvariate(SERVING_MEAN, SERVING_STD)))
        state['s_active'] -= 1

    # 2. Kasa
    state['c_queue'] += 1
    with cafeteria.cashier.request() as req:
        yield req
        state['c_queue'] -= 1
        state['c_active'] += 1
        yield env.timeout(random.expovariate(1.0 / CASHIER_MEAN))
        state['c_active'] -= 1

    # 3. Masa
    state['t_queue'] += 1
    with cafeteria.seating.request() as req:
        yield req
        state['t_queue'] -= 1
        state['t_active'] += 1
        yield env.timeout(random.expovariate(1.0 / EATING_MEAN))
        state['t_active'] -= 1
        
    state['total_out'] += 1

def setup(env):
    cafeteria = Cafeteria(env)
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_MEAN))
        env.process(student(env, cafeteria))

def live_dashboard(env):
    """Terminali sürekli temizleyerek anlık grafikleri/pano çizen simpy süreci"""
    while True:
        # Terminal Ekranını Temizleme Komutu (Windows için cls, Mac/Linux için clear)
        os.system('cls' if os.name == 'nt' else 'clear')
        
        print("="*60)
        print("          YEMEKHANE CANLI SİMÜLASYON PANOSU")
        print(f"          Simülasyon Zamanı: {env.now:5.2f} dakika / {SIM_TIME}")
        print("="*60)
        
        # Yemek Bankosu Çizimi
        print("\n[YEMEK DAĞITIM BANKOSU]")
        print(f"Sırada Bekleyen : {'O ' * state['s_queue']}")
        print(f"Hizmet Veren    : {'[X] ' * state['s_active']}{'[ ] ' * (NUM_SERVERS - state['s_active'])}")
        
        # Kasa Çizimi
        print("\n[KASA - ÖDEME]")
        print(f"Sırada Bekleyen : {'O ' * state['c_queue']}")
        print(f"Çalışan Kasa    : {'[X] ' * state['c_active']}{'[ ] ' * (NUM_CASHIERS - state['c_active'])}")
        
        # Masa Çizimi
        print("\n[OTURMA ALANI]")
        print(f"Ayakta Bekleyen : {'O ' * state['t_queue']}")
        print(f"Dolu Masalar    : {'[X] ' * state['t_active']}{'[ ] ' * (SEATING_CAPACITY - state['t_active'])}")
        
        # Istatistik Toplam
        print("\n" + "-"*60)
        print(f"Sisteme Giren: {state['total_in']:3} | Çıkan: {state['total_out']:3} | İçerideki: {state['total_in'] - state['total_out']:3}")
        print("-" * 60)
        print("\n(Simülasyonu anlık durdurmak için CTRL+C tuşlarına veya Konsolda STOP butonuna basabilirsiniz.)")
        
        # Bu pano sürecinin akıcılığı için simülasyonda her 0.25 dakikada bir yenileme isteği atıyoruz
        yield env.timeout(0.25)

if __name__ == '__main__':
    # SimPy RealtimeEnvironment (Canlı Simulasyon Modülü) Kullanımı:
    # factor = 3.0 -> Simülasyondaki 1 dakika, gerçek hayatta 3 saniye sürecek (en yavaş hız).
    # strict = False -> Eğer bilgisayar hesaplama yaparken yavaş kalırsa hata vermez, tolere eder.
    random.seed(42)
    env = simpy.rt.RealtimeEnvironment(factor=3.0, strict=False)
    
    env.process(setup(env))
    env.process(live_dashboard(env))
    
    try:
        env.run(until=SIM_TIME)
        print("\nSimülasyon Tamamlandı.")
    except KeyboardInterrupt:
        pass
