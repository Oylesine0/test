# Temel olarak hafif bir Python 3.9 imajı kullanıyoruz.
FROM python:3.9-slim

# Konteyner içinde çalışacağımız dizini ayarlıyoruz.
WORKDIR /app

# Önce sadece requirements.txt dosyasını kopyalayıp kütüphaneleri kuruyoruz.
# Bu, Docker'ın katman önbellekleme özelliğinden faydalanarak, kodunuz değişse bile
# kütüphanelerin tekrar tekrar indirilmesini engeller ve süreci hızlandırır.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Geriye kalan uygulama kodunu kopyalıyoruz.
COPY app.py .

# Uygulamanın çalışacağı portu dışarıya açıyoruz (Hugging Face bunu otomatik yönlendirir).
EXPOSE 7860

# Konteyner başladığında uygulamayı çalıştıracak komutu belirtiyoruz.
CMD ["python", "app.py"]