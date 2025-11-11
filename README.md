# Backend API Dự án FitForm 🏋️‍♂️

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://www.python.org/)
[![Django](https://img.shields.io/badge/Django-4.2+-green?logo=django)](https://www.djangoproject.com/)
[![Django REST Framework](https://img.shields.io/badge/DRF-3.14+-red?logo=django)](https://www.django-rest-framework.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-darkblue?logo=postgresql)](https://www.postgresql.org/)
[![Render](https://img.shields.io/badge/Deploy-Render-46E3B7?logo=render)](https://render.com/)

Đây là mã nguồn backend cho ứng dụng web **FitForm**. Dự án này được xây dựng bằng **Django** và **Django REST Framework (DRF)**, cung cấp một bộ API đầy đủ để quản lý người dùng, hồ sơ, kế hoạch tập luyện, gợi ý bài tập thông minh, và theo dõi dinh dưỡng/nước uống.

Dự án này được thiết kế để chạy với **SQL Server** ở môi trường local và **PostgreSQL** ở môi trường Production (triển khai trên Render).

## Các Tính năng Chính (API Endpoints)

* **Xác thực (Auth):** Đăng ký, Đăng nhập (`dj-rest-auth` qua Token).
* **Hồ sơ (Profile):** Tạo và cập nhật thông tin người dùng (chiều cao, cân nặng, mục tiêu, trình độ...).
* **Thư viện Bài tập (Exercise):**
    * Seeding (gieo mầm) CSDL với 25+ bài tập cốt lõi đã được phân loại.
    * `GET /exercises/`: Lọc và tìm kiếm bài tập theo nhóm cơ, dụng cụ, độ khó.
    * `POST /exercises/`: (UC17) User tự tạo bài tập tùy chỉnh.
* **Kế hoạch (Plan):**
    * `GET /plans/generate/`: (UC06) API thông minh, gợi ý kế hoạch tập dựa trên Profile của user.
    * `POST /plans/`: (UC07) Lưu kế hoạch (tùy chỉnh hoặc gợi ý) với các bài tập lồng nhau (nested JSON).
    * `GET /plans/`: Lấy danh sách *cá nhân* các kế hoạch đã lưu.
    * `GET /plans/<id>/`: Lấy chi tiết một kế hoạch (dùng cho UC08 - Bắt đầu buổi tập).
* **Buổi tập (Session):**
    * `POST /sessions/`: (UC11) Lưu lại một buổi tập đã hoàn thành (với JSON lồng chi tiết các set/rep/feedback).
    * `GET /sessions/`: Lấy lịch sử các buổi tập.
    * `GET /sessions/<id>/`: (UC13) Xem chi tiết một buổi tập.
* **Thống kê (Analytics):**
    * `GET /dashboard/`: (UC12) API tổng hợp, trả về BMI, tổng calories, số buổi tập...
* **Dinh dưỡng (Nutrition):**
    * `POST /nutrition-logs/`: (UC19) Ghi lại nhật ký bữa ăn.
    * `POST /hydration-logs/`: (UC20) Ghi lại nhật ký uống nước.
    * `GET /nutrition/suggest/`: (UC18) API thông minh, gợi ý thực đơn (template) dựa trên TDEE và mục tiêu.

## Công nghệ sử dụng

* **Framework:** Django
* **API:** Django REST Framework (DRF)
* **Database (Production):** PostgreSQL
* **Database (Local):** SQL Server
* **Authentication:** `dj-rest-auth` (Token Authentication)
* **Filtering:** `django-filter`
* **CORS:** `django-cors-headers`
* **Deployment:** Render
* **WSGI Server:** Gunicorn

## Thiết lập Môi trường Local (Local Development)

Các bước để chạy dự án này trên máy của bạn.

### 1. Yêu cầu tiên quyết

* [Python (3.11+)](https://www.python.org/downloads/)
* [Git](https://git-scm.com/downloads)
* [SQL Server](https://www.microsoft.com/en-us/sql-server/sql-server-downloads) (và SSMS)
* [Microsoft ODBC Driver for SQL Server](https://learn.microsoft.com/en-us/sql/connect/odbc/download-odbc-driver-for-sql-server)

### 2. Cài đặt

1.  **Clone repository:**
    ```bash
    git clone [https://github.com/Minhpham0203/FitForm.git](https://github.com/Minhpham0203/FitForm.git)
    cd FitForm
    ```

2.  **Tạo và kích hoạt môi trường ảo (venv):**
    ```bash
    # Windows
    python -m venv venv
    .\venv\Scripts\activate
    
    # macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```

3.  **Cài đặt các thư viện:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Cấu hình CSDL (`settings.py`):**
    Dự án đã được cấu hình sẵn để ưu tiên `DATABASE_URL` (cho Render). Khi chạy local, nó sẽ tự động dùng khối `else` (cấu hình SQL Server).
    
    Hãy đảm bảo bạn đã tạo một CSDL rỗng trên SQL Server local và cập nhật khối `else` trong `FitForm/settings.py` cho khớp:

    ```python
    # FitForm/settings.py
    # ...
    else:
        # Cấu hình SQL Server local
        DATABASES = {
            'default': {
                'ENGINE': 'mssql',
                'NAME': 'FitForm_db', # <-- Tên CSDL local của bạn
                'USER': 'sa', # <-- User của bạn
                'PASSWORD': 'Mat_Khau_Cua_Ban', # <-- Mật khẩu của bạn
                'HOST': 'localhost\\MSSQLSERVER01', # <-- Host/Instance của bạn
                'OPTIONS': {
                    'driver': 'ODBC Driver 17 for SQL Server',
                },
            }
        }
    ```

5.  **Chạy Migrations (Tạo bảng CSDL):**
    Lệnh này sẽ tạo các bảng *VÀ* "gieo mầm" (seed) dữ liệu 25 bài tập (từ file migration `seed_exercises`).
    ```bash
    python manage.py migrate
    ```

6.  **Tạo Superuser (Tài khoản Admin):**
    ```bash
    python manage.py createsuperuser
    ```

7.  **Chạy Server:**
    ```bash
    python manage.py runserver
    ```
    API của bạn giờ đã chạy tại `http://127.0.0.1:8000/`.

## Tài liệu API (Hợp đồng API) 📖

Toàn bộ tài liệu API, bao gồm tất cả các endpoint, ví dụ Request/Response, và các header bắt buộc, đều nằm trong file Postman Collection:

**`My Collection.postman_collection.json`** (Đã được update trong repo này)

### Hướng dẫn sử dụng Postman

1.  **Import:** Mở Postman, chọn "Import" và chọn file `.json` trên.
2.  **Cấu hình Biến:**
    * Tạo một Environment trong Postman.
    * Thêm biến `baseUrl`. Đặt giá trị là `http://127.0.0.1:8000` (khi test local) hoặc `https://fitform-repo.onrender.com` (khi test production).
    * Collection này sẽ tự động dùng biến `{{authToken}}` (được lưu ở cấp Collection).
3.  **Lấy Token:** Chạy request **`Auth`** $\rightarrow$ **`Login (Get Token)`**. Script "Tests" sẽ tự động lưu `key` vào biến `authToken`.
4.  **Test:** Chạy bất kỳ request nào khác. Chúng sẽ tự động đính kèm `Authorization: Token {{authToken}}`.

## Triển khai (Deployment)

Dự án này được cấu hình để deploy tự động trên **Render**.

* **Lệnh Khởi động (`Procfile`):**
    ```Procfile
    web: gunicorn FitForm.wsgi --log-file -
    ```
* **Lệnh Build (trên Render):**
    ```bash
    pip install -r requirements.txt && python manage.py migrate
    ```
* **Biến Môi trường (Environment Variables) Bắt buộc trên Render:**
    * `DATABASE_URL`: (Render tự cung cấp khi tạo CSDL PostgreSQL)
    * `SECRET_KEY`: (Lấy từ `settings.py`)
    * `DEBUG`: `False`
    * `DJANGO_ALLOWED_HOSTS`: `fitform-repo.onrender.com`
    * `CORS_ALLOWED_ORIGINS`: `https://fitness-form.netlify.app,http://localhost:3000`
