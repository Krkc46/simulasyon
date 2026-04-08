<div align="center">

### T.C.<br>MERSİN ÜNİVERSİTESİ<br>ERDEMLİ UYGULAMALI TEKNOLOJİ VE İŞLETMECİLİK YÜKSEKOKULU
*Bilişim Sistemleri ve Teknolojileri / Yönetim Bilişim Sistemleri*

<br><br>

# YEMEKHANE SİMÜLASYONU VE SÜREÇ OPTİMİZASYONU
### Ayrık Olay Simülasyonu (Discrete-Event Simulation) ve Kuyruk Teorisi Analiz Raporu

<br><br>

**Hazırlayan**<br>
**Ad Soyad:** Hüseyin Karakoç<br>
**Öğrenci No:** 22430070027<br>
**Proje GitHub Deposu:** [https://github.com/Krkc46/simulasyon](https://github.com/Krkc46/simulasyon)

<br><br>

**Mersin - 2026**

</div>

---

## 1. Projenin Amacı ve Kapsamı
Bu projenin temel amacı, bir üniversite yemekhanesindeki öğrenci akışının ve hizmet noktalarının yoğunluk durumunu analiz etmektir. Belirli bir zaman dilimi içinde (standart bir öğle arası olan 120 dakika) kuyruk teorisinin pratikte nasıl uygulandığını gözlemlemek ve darboğaz (bottleneck) oluşan noktaları tespit ederek parametrelere dayalı kapasite planlaması yapmaktır.

## 2. Sistem Tanımı ve Model Parametreleri
Yemekhane sistemi üç aşamalı ardışık bir hizmet kuyruğundan oluşmaktadır:
* **Gelişler:** Öğrencilerin yemekhaneye geliş aralıkları rastgele olup eksponansiyel (üstel) dağılıma uymaktadır (ortalama 1 kişi / dakika).
* **1. Aşama - Yemek Dağıtım Bankosu:** `NUM_SERVERS` adlı değişkene bağlı çalışan görevliler mevcuttur. Yemek alma süreleri normal dağılıma uymakta olup, ortalaması 3 dakika ve standart sapması 0.5 dakika olarak varsayılmıştır.
* **2. Aşama - Kasa / Ödeme Süreci:** `NUM_CASHIERS` adlı değişkene sahip kasalarda işlem süreleri eksponansiyel dağılıma uyarak çok hızlı gerçekleşir (ortalama 0.5 dakika).
* **3. Aşama - Oturma ve Yemek Yeme:** Toplam tesis kapasitesi `SEATING_CAPACITY` olarak tanımlanmıştır. Masada geçirilen süre eksponansiyel dağılımla ortalama 20 dakikadır. Eğer boş yer yoksa öğrenciler ellerinde tepsi ile beklemek zorundadır.

## 3. Metodoloji ve Kullanılan Araçlar
Ayrık olay simülasyonu (Discrete-Event Simulation) kurgulamak için **Python** dilinde yazılmış açık kaynaklı **SimPy** kütüphanesi kullanılmıştır. 
Projeyi daha sürdürülebilir hale getirmek için **Nesne Yönelimli Programlama (OOP)** metodolojisi izlenmiştir. Sistemdeki istasyonlar (banko, kasa, masa vb.) `simpy.Resource` ile tanımlanmış sınırlı kaynaklara bağlanmıştır. Öğrencilerin sisteme dahil olması fonksiyonlar üzerinde `yield` (generator) mantığıyla adım adım işletilmiştir. 

## 4. Uygulanan Optimizasyon ve Analiz Sonuçları
İlk kurulan (Varsayılan) modelde 3 banko görevlisi ve 2 kasa bulunuyordu. Termal logların analizi sonucunda sistemde şu tespitler yapıldı:
- **Yemek Bankosu Darboğazı:** 3 görevlinin hızı dakikada 1 öğrenciye ancak yettiği için öğrenci geliş oranlarıyla çakışmış ve burada ciddi bir kuyruk oluşmuştur (Meşguliyet %94 civarı).
- **Atıl Kapasite:** Bankodan tek tek çıkan öğrencileri bekleyen kasalar çok hızlı olduğu için kapasite israfı oluşmuş, meşguliyetleri %25'lerde kalmıştır.

**Uygulanan Optimizasyon (Rebalancing):**
Bu sistem dengesizliğini gidermek için kod güncellendi. Yemek bankosundaki görevli sayısı 4'e çıkarılırken (kuyrukları eritecek çözüm), gereksiz boşta duran kasa sayısı tasarruf amacıyla 1'e düşürüldü. Ayrıca kapasite ve "Little Kanunu (Little's Law)" testleri için masa kapasiteleri düşürülüp ayakta tepsiyle beklemelerin gözlemlenebilmesi sağlandı.

### Simülasyon Veri Grafikleri

Aşağıdaki grafikler sistemin optimize edildikten sonraki halinde, standart bir öğle arasında (120 dakika) nasıl bir performans gösterdiğine dair hesaplanan çıktıları göstermektedir.

**Bekleme Süreleri Dağılımı (Kutu Grafiği):**
![Aşamalara Göre Bekleme Süreleri Dağılımı](bekleme_sureleri_grafigi.png)

**Kaynak Kullanım Oranları (Çubuk Grafiği):**
![Kaynak Kullanım Oranları](kaynak_kullanim_oranlari_grafigi.png)

**Simülasyon Özet Sonuç Panosu:**
![Simülasyon Özet Sonuçlar](simulasyon_ozet_sonuclar.png)

## 5. Grafiksel Arayüz (GUI) Geliştirmesi
Projeyi komut satırındaki sıkıcı yazılardan ibaret olmaktan çıkarmak için iki farklı sunum geliştirildi:
1. SimPy'ın "Realtime" kütüphanesi entegre edilerek zamanın bilgisayar saniyesiyle senkronize aktığı bir animasyonlu komut satırı izleyicisi yapıldı.
2. Projenin son evresi olarak arka planda çoklu işlem (Threading) ile çalışan ve Python'ın kendi kütüphanesi olan **Tkinter** kullanan bir **Masaüstü Kullanıcı Arayüzü (GUI)** tasarlandı. Emojilerle hangi birimde kaç kişinin beklediği arayüz üzerinden eşzamanlı izlenebilir hale getirildi. 

## 6. Sonuç ve Değerlendirme
Bu proje, yazılım destekli simülasyonların maliyet/fayda analizlerindeki gücünü ortaya koymuştur. Sadece bir satır parametre değiştirerek personellerin nasıl konumlandırılması gerektiği tahmin edilmiş ve gereksiz maliyetler teorik ortamda elimine edilmiştir. Oluşturulan genişletilebilir betik sayesinde, ilerde bu senaryoya "öğretmen öncelikli kuyruk" veya "fast-food ayrıcalığı" gibi yeni kurallar kolaylıkla eklenebilecektir.
