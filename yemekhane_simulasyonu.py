import simpy
import random
import statistics

# ==========================================
# GLOABAL KONFİGÜRASYON VE SİSTEM DEĞİŞKENLERİ
# ==========================================
NUM_SERVERS = 4          # Yemek dağıtım bankosu görevli sayısı (Optimizasyon: 3 -> 4)
NUM_CASHIERS = 1         # Kasa sayısı (Optimizasyon: 2 -> 1)
SEATING_CAPACITY = 15    # Yemekhane masa kapasitesi (Darboğazı görmek için 50'den 15'e düşürüldü)
SIM_TIME = 120           # Simülasyon süresi (dakika) - Standart öğle arası

ARRIVAL_MEAN = 1.0       # Ortalama öğrenci geliş süresi (dakika)
SERVING_MEAN = 3.0       # Ortalama yemek alma süresi (dakika)
SERVING_STD = 0.5        # Yemek alma süresi standart sapması (dakika)
CASHIER_MEAN = 0.5       # Ortalama ödeme yapma süresi (dakika)
EATING_MEAN = 20.0       # Ortalama yemek yeme süresi (dakika)

VERBOSE = True           # Süreç loglarını terminale basmak için anahtar (Açık/Kapalı)

# İstatistikleri tutacağımız küresel (global) sözlük
stats = {
    'total_entered': 0,
    'total_finished': 0,
    'waiting_times': {
        'serving': [],
        'cashier': [],
        'seating': []
    },
    'server_busy_time': 0,
    'cashier_busy_time': 0
}

def log(env, message):
    """Eğer VERBOSE True ise simülasyon zamanıyla birlikte olayları terminale basar."""
    if VERBOSE:
        print(f"[{env.now:5.2f} dk] {message}")

class Cafeteria:
    """Yemekhane sistemindeki kaynakları ve onlara ait süreçleri tutan sınıf."""
    def __init__(self, env):
        self.env = env
        
        # SimPy Resource (Kaynak) tanımlamaları
        self.server = simpy.Resource(env, capacity=NUM_SERVERS)
        self.cashier = simpy.Resource(env, capacity=NUM_CASHIERS)
        self.seating = simpy.Resource(env, capacity=SEATING_CAPACITY)

    def serve_food(self):
        """Yemek dağıtım süreci (Normal Dağılım)"""
        # Yemek dağıtımı normal dağılıma uymaktadır
        service_time = random.normalvariate(SERVING_MEAN, SERVING_STD)
        
        # Sürenin negatif çıkmaması için alt sınır koyuyoruz
        service_time = max(0.1, service_time)
        
        # SimPy'da bekleme süresini 'timeout' ile simüle ediyoruz
        yield self.env.timeout(service_time)
        
        # Görevlinin ne kadar süre meşgul kaldığını istatistiklere ekliyoruz
        stats['server_busy_time'] += service_time

    def process_payment(self):
        """Ödeme süreci (Eksponansiyel Dağılım)"""
        # Kasa işlemleri de rastgeledir, eksponansiyel dağılım ile modellenebilir
        payment_time = random.expovariate(1.0 / CASHIER_MEAN)
        
        yield self.env.timeout(payment_time)
        
        # Kasanın meşguliyet süresini ekliyoruz
        stats['cashier_busy_time'] += payment_time

    def eat_food(self):
        """Yemek yeme süresi (Eksponansiyel Dağılım)"""
        # Yemek yeme süresi ortalama 20 dakikadır
        eating_time = random.expovariate(1.0 / EATING_MEAN)
        yield self.env.timeout(eating_time)

def student(env, name, cafeteria):
    """
    Bir öğrencinin yemekhanedeki yaşam döngüsünü (iş süreçlerini) 
    adım adım listeleyen fonksiyon (SimPy Process).
    """
    stats['total_entered'] += 1
    log(env, f"{name} yemekhaneye girdi ve yemek sırasına yöneldi.")
    
    # ---------------------------------------------
    # 1. Aşama: Yemek Dağıtım Bankosu
    # ---------------------------------------------
    arrive_serving_time = env.now
    
    # Bankodan (server) bir görevli talep ediyoruz
    with cafeteria.server.request() as request:
        yield request # Görevli boşa çıkana kadar bekle
        
        # Ne kadar beklediğimizi hesaplıyoruz
        wait_for_serving = env.now - arrive_serving_time
        stats['waiting_times']['serving'].append(wait_for_serving)
        log(env, f"{name} yemeğini almaya başladı. (Banko Bekleme: {wait_for_serving:.2f} dk)")
        
        # Yemek alma sürecini işletiyoruz
        yield env.process(cafeteria.serve_food())
        log(env, f"{name} yemeğini aldı.")

    # ---------------------------------------------
    # 2. Aşama: Kasa / Ödeme Noktası
    # ---------------------------------------------
    arrive_cashier_time = env.now
    
    # Kasadan (cashier) görevli talep ediyoruz
    with cafeteria.cashier.request() as request:
        yield request # Kasa boşalana kadar bekle
        
        wait_for_cashier = env.now - arrive_cashier_time
        stats['waiting_times']['cashier'].append(wait_for_cashier)
        log(env, f"{name} kasada ödeme yapmaya başladı. (Kasa Bekleme: {wait_for_cashier:.2f} dk)")
        
        yield env.process(cafeteria.process_payment())
        log(env, f"{name} ödemesini tamamladı.")

    # ---------------------------------------------
    # 3. Aşama: Oturma Alanı (Tesis Kapasitesi)
    # ---------------------------------------------
    arrive_seating_time = env.now
    log(env, f"{name} boş masa arıyor...")
    
    # Oturma alanından masa (seating) talep ediyoruz
    with cafeteria.seating.request() as request:
        yield request # Masa boşalana kadar elinde tepsiyle bekle
        
        wait_for_seating = env.now - arrive_seating_time
        stats['waiting_times']['seating'].append(wait_for_seating)
        
        if wait_for_seating > 0:
            log(env, f"{name} boş masa buldu ve oturdu. (Tepsiyle Bekleme: {wait_for_seating:.2f} dk)")
        else:
            log(env, f"{name} hemen boş masa buldu ve oturdu.")
            
        # Yemeğini yer
        yield env.process(cafeteria.eat_food())
        log(env, f"{name} yemeğini bitirdi, masayı boşalttı ve ayrılıyor.")
        
        # Döngüyü başarıyla tamamlayan öğrencileri sayıyoruz
        stats['total_finished'] += 1

def setup(env):
    """
    Simülasyon ortamını başlatan ve dışarıdan sürekli 
    öğrenci gelmesini sağlayan (generator) fonksiyon.
    """
    cafeteria = Cafeteria(env)
    
    i = 0
    while True:
        # Öğrencilerin geliş aralığı eksponansiyel dağılıma uyar (Örn. ortalama 1 dk)
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_MEAN))
        i += 1
        
        # Her gelen yeni öğrenci için process başlatıyoruz
        env.process(student(env, f"Öğrenci {i}", cafeteria))

def print_summary_report():
    """
    Performans metriklerini ve KPI'ları (Key Performance Indicators)
    hesaplayarak ekrana sadece sonuçların gösterildiği raporu basar.
    """
    print("\n" + "=" * 60)
    print(" " * 12 + "YEMEKHANE SİMÜLASYONU ÖZET RAPORU")
    print("=" * 60)
    print(f"Toplam Simülasyon Süresi      : {SIM_TIME} dakika")
    print(f"Sisteme Giren Toplam Öğrenci  : {stats['total_entered']}")
    print(f"Yemeğini Bitirip Çıkan Öğrenci: {stats['total_finished']}")
    print(f"İçeride Kalan/Bekleyen Öğrenci: {stats['total_entered'] - stats['total_finished']}")
    print("-" * 60)
    
    # Bekleme Süreleri
    wait_serving = stats['waiting_times']['serving']
    wait_cashier = stats['waiting_times']['cashier']
    wait_seating = stats['waiting_times']['seating']
    
    avg_wait_serving = statistics.mean(wait_serving) if wait_serving else 0
    avg_wait_cashier = statistics.mean(wait_cashier) if wait_cashier else 0
    avg_wait_seating = statistics.mean(wait_seating) if wait_seating else 0
    
    print("ORTALAMA BEKLEME SÜRELERİ (Darboğaz Analizi)")
    print(f"  - Yemek Dağıtım Sırası : {avg_wait_serving:.2f} dakika")
    print(f"  - Kasa Sırası          : {avg_wait_cashier:.2f} dakika")
    print(f"  - Masa Bulma (Tepsiyle): {avg_wait_seating:.2f} dakika")
    print("-" * 60)
    
    # Kaynak Kullanım Oranları (Utilization)
    # Formül: Toplam Meşguliyet Süresi / (Toplam Simülasyon Süresi * Toplam Kaynak Sayısı)
    server_utilization = (stats['server_busy_time'] / (SIM_TIME * NUM_SERVERS)) * 100
    cashier_utilization = (stats['cashier_busy_time'] / (SIM_TIME * NUM_CASHIERS)) * 100
    
    print("KAYNAK KULLANIM ORANLARI (Utilization - Meşguliyet)")
    print(f"  - Yemek Dağıtım Görevlileri : %{server_utilization:.2f}")
    print(f"  - Kasalar                   : %{cashier_utilization:.2f}")
    print("=" * 60)

if __name__ == '__main__':
    # Simülasyon sonuçlarının tekrar üretilebilir olması için rastgelelik tohumu:
    random.seed(42)
    
    if VERBOSE:
        print("SİMÜLASYON LOGLARI BAŞLIYOR...\n" + "-" * 30)
    
    # 1. Çevre (Environment) yaratılır
    env = simpy.Environment()
    
    # 2. Setup processi ortama eklenir
    env.process(setup(env))
    
    # 3. Simülasyon başlatılıp SIM_TIME kadar yürütülür
    env.run(until=SIM_TIME)
    
    # 4. Simülasyon bittiğinde özet rapor bastırılır
    print_summary_report()
