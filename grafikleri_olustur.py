import simpy
import random
import statistics
import matplotlib.pyplot as plt
import os

# Simülasyon Değişkenleri
NUM_SERVERS = 4
NUM_CASHIERS = 1
SEATING_CAPACITY = 15
SIM_TIME = 120

ARRIVAL_MEAN = 1.0
SERVING_MEAN = 3.0
SERVING_STD = 0.5
CASHIER_MEAN = 0.5
EATING_MEAN = 20.0

stats = {
    'total_entered': 0,
    'total_finished': 0,
    'waiting_times': {'serving': [], 'cashier': [], 'seating': []},
    'server_busy_time': 0,
    'cashier_busy_time': 0
}

class Cafeteria:
    def __init__(self, env):
        self.env = env
        self.server = simpy.Resource(env, capacity=NUM_SERVERS)
        self.cashier = simpy.Resource(env, capacity=NUM_CASHIERS)
        self.seating = simpy.Resource(env, capacity=SEATING_CAPACITY)

    def serve_food(self):
        service_time = max(0.1, random.normalvariate(SERVING_MEAN, SERVING_STD))
        yield self.env.timeout(service_time)
        stats['server_busy_time'] += service_time

    def process_payment(self):
        payment_time = random.expovariate(1.0 / CASHIER_MEAN)
        yield self.env.timeout(payment_time)
        stats['cashier_busy_time'] += payment_time

    def eat_food(self):
        eating_time = random.expovariate(1.0 / EATING_MEAN)
        yield self.env.timeout(eating_time)

def student(env, name, cafeteria):
    stats['total_entered'] += 1
    arrive_serving_time = env.now
    with cafeteria.server.request() as request:
        yield request
        stats['waiting_times']['serving'].append(env.now - arrive_serving_time)
        yield env.process(cafeteria.serve_food())

    arrive_cashier_time = env.now
    with cafeteria.cashier.request() as request:
        yield request
        stats['waiting_times']['cashier'].append(env.now - arrive_cashier_time)
        yield env.process(cafeteria.process_payment())

    arrive_seating_time = env.now
    with cafeteria.seating.request() as request:
        yield request
        stats['waiting_times']['seating'].append(env.now - arrive_seating_time)
        yield env.process(cafeteria.eat_food())
        stats['total_finished'] += 1

def setup(env):
    cafeteria = Cafeteria(env)
    i = 0
    while True:
        yield env.timeout(random.expovariate(1.0 / ARRIVAL_MEAN))
        i += 1
        env.process(student(env, f"Ogrenci {i}", cafeteria))

# Simülasyonu çalıştır
random.seed(42)
env = simpy.Environment()
env.process(setup(env))
env.run(until=SIM_TIME)

# Klasör yolu
out_dir = r"c:\Users\karak\Desktop\simülasyon"

# 1. Kutu Grafiği (Bekleme Süreleri)
plt.figure(figsize=(10, 6))
data = [stats['waiting_times']['serving'], stats['waiting_times']['cashier'], stats['waiting_times']['seating']]
plt.boxplot(data, tick_labels=['Yemek Dağıtım', 'Kasa', 'Oturma (Tepsiyle Bekleme)'])
plt.title('Aşamalara Göre Bekleme Süreleri Dağılımı', fontsize=14, fontweight='bold')
plt.ylabel('Bekleme Süresi (Dakika)', fontsize=12)
plt.grid(True, axis='y', linestyle='--', alpha=0.7)
plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'bekleme_sureleri_grafigi.png'), dpi=300)
plt.close()

# 2. Çubuk Grafiği (Kullanım Oranları)
server_utilization = (stats['server_busy_time'] / (SIM_TIME * NUM_SERVERS)) * 100
cashier_utilization = (stats['cashier_busy_time'] / (SIM_TIME * NUM_CASHIERS)) * 100

plt.figure(figsize=(8, 6))
bars = plt.bar(['Yemek Dağıtım Görevlileri (4 Kişi)', 'Kasalar (1 Kişi)'], 
               [server_utilization, cashier_utilization], 
               color=['#4CAF50', '#2196F3'])
plt.title('Kaynak Kullanım Oranları (Sistem Meşguliyeti)', fontsize=14, fontweight='bold')
plt.ylabel('Kullanıldığı Süre / Toplam Süre Oranı (%)', fontsize=12)
plt.ylim(0, 100)

for bar in bars:
    yval = bar.get_height()
    plt.text(bar.get_x() + bar.get_width()/2, yval + 1, f"%{yval:.2f}", ha='center', va='bottom', fontweight='bold', fontsize=12)

plt.tight_layout()
plt.savefig(os.path.join(out_dir, 'kaynak_kullanim_oranlari_grafigi.png'), dpi=300)
plt.close()

# 3. Özet Sonuçlar Görseli
plt.figure(figsize=(10, 5))
plt.axis('off')

summary_text = (
    "YEMEKHANE SİMÜLASYONU ÖZET SONUÇLAR (120 Dakika)\n"
    "===========================================================\n"
    f"Sisteme Giren Toplam Öğrenci   : {stats['total_entered']} Kişi\n"
    f"Yemeğini Bitirip Çıkan Öğrenci : {stats['total_finished']} Kişi\n"
    f"Sistemde Kalan Öğrenci Sayısı  : {stats['total_entered'] - stats['total_finished']} Kişi\n"
    "-----------------------------------------------------------\n"
    "ORTALAMA BEKLEME SÜRELERİ (Darboğaz Analizi)\n"
    f"- Yemek Dağıtım Sırası Bekleme : {statistics.mean(stats['waiting_times']['serving']):.2f} dakika\n"
    f"- Kasa (Ödeme) Sırası Bekleme  : {statistics.mean(stats['waiting_times']['cashier']):.2f} dakika\n"
    f"- Boş Masa Bulma Bekleme       : {statistics.mean(stats['waiting_times']['seating']):.2f} dakika\n"
)

plt.text(0.5, 0.5, summary_text, fontsize=12, ha='center', va='center', family='monospace', 
         bbox=dict(facecolor='#f0f8ff', edgecolor='#4682b4', boxstyle='round,pad=1.5', linewidth=2))

plt.savefig(os.path.join(out_dir, 'simulasyon_ozet_sonuclar.png'), bbox_inches='tight', dpi=300)
plt.close()

print("Bütün grafikler başarıyla oluşturuldu ve masaüstüne kaydedildi!")
