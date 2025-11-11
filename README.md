# FitForm
FitForm - Backend API 🏋️‍♂️Đây là repository chứa mã nguồn backend cho ứng dụng web FitForm. Dự án này được xây dựng bằng Django và Django REST Framework (DRF), cung cấp một bộ API đầy đủ để quản lý người dùng, hồ sơ, kế hoạch tập luyện, gợi ý bài tập, và theo dõi dinh dưỡng.Backend này được thiết kế để giao tiếp với một frontend (ví dụ: Netlify) và được triển khai (deploy) trên Render.Công nghệ sử dụngFramework: DjangoAPI: Django REST Framework (DRF)Authentication (Xác thực): dj-rest-auth (Token Authentication)Database (Production): PostgreSQL (trên Render)Database (Local Dev): SQL Server (hoặc PostgreSQL tùy bạn cấu hình)Filtering (Lọc): django-filterCORS: django-cors-headersWeb Server (Production): GunicornThiết lập Môi trường Local (Local Development)Các bước để chạy dự án này trên máy của bạn.1. Yêu cầu tiên quyếtPython (ví dụ: 3.11+)GitMột CSDL (SQL Server hoặc PostgreSQL) đã được cài đặt và đang chạy trên máy local.2. Cài đặtClone repository:Bashgit clone [URL_REPO_CUA_BAN]
cd [TEN_REPO]
Tạo và kích hoạt môi trường ảo (venv):Bash# Windows
python -m venv venv
.\venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
Cài đặt các thư viện:Bashpip install -r requirements.txt
Cấu hình CSDL (settings.py):Mở file FitForm/settings.py. Tìm đến khối DATABASES. Code đã được thiết lập để ưu tiên DATABASE_URL (cho Render). Khi chạy local, nó sẽ tự động dùng khối else (cấu hình SQL Server của bạn).Hãy đảm bảo khối else khớp với CSDL local của bạn:Python# ...
else:
    # Cấu hình SQL Server local
    DATABASES = {
        'default': {
            'ENGINE': 'mssql',
            'NAME': 'FitForm_db', # Tên CSDL bạn tạo local
            'USER': 'sa',
            'PASSWORD': 'Mat_Khau_Cua_Ban',
            'HOST': 'localhost\\MSSQLSERVER01', 
            'OPTIONS': {
                'driver': 'ODBC Driver 17 for SQL Server',
            },
        }
    }
Chạy Migrations (Tạo bảng CSDL):Lệnh này sẽ tạo các bảng và "gieo mầm" (seed) dữ liệu bài tập (từ file migration seed_exercises).Bashpython manage.py migrate
Tạo Superuser (Tài khoản Admin):Bashpython manage.py createsuperuser
(Nhập username, email, password cho tài khoản admin local của bạn)Chạy Server:Bashpython manage.py runserver
API của bạn giờ đã chạy tại http://127.0.0.1:8000/.Cấu hình Biến Môi trường (Production)Khi triển khai lên Render (hoặc nền tảng khác), bạn phải cung cấp các Biến Môi trường (Environment Variables) sau:DATABASE_URL: Chuỗi kết nối đến CSDL PostgreSQL (Render tự động cung cấp).SECRET_KEY: Khóa bí mật của Django (lấy từ settings.py).DEBUG: Đặt là False.DJANGO_ALLOWED_HOSTS: Tên miền của bạn (ví dụ: fitform-repo.onrender.com).CORS_ALLOWED_ORIGINS: Danh sách các URL frontend (cách nhau bằng dấu phẩy).Ví dụ: https://fitness-form.netlify.app,http://localhost:3000Tài liệu API (Hợp đồng API) 📖Toàn bộ tài liệu API, bao gồm tất cả các endpoint, ví dụ Request/Response, và các header bắt buộc, đều nằm trong file Postman Collection:My Collection.postman_collection.jsonHãy Import (nhập) file này vào Postman để bắt đầu kiểm thử (test) và làm việc.Luồng làm việc với PostmanCấu hình Biến: Cập nhật biến baseUrl trong Postman (ví dụ: http://127.0.0.1:8000 khi test local, hoặc https://fitform-repo.onrender.com khi test production).Lấy Token: Chạy request Auth $\rightarrow$ Login (Get Token). Script "Tests" sẽ tự động lưu authToken.Test API: Các request khác sẽ tự động sử dụng authToken này.Triển khai (Deployment)Dự án này được thiết lập để deploy tự động trên Render thông qua file Procfile:Đoạn mãweb: gunicorn FitForm.wsgi --log-file -
Sau khi deploy, hãy đảm bảo bạn đã chạy migrate trên server production thông qua Shell (hoặc kết nối pgAdmin) và tạo Superuser.
