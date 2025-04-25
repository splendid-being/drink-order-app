from flask import Flask, request, redirect, url_for, render_template_string
from collections import Counter
from datetime import datetime, timezone, timedelta

app = Flask(__name__)
orders = []
last_reset_date = None  # 오후 6시 이후 1일 1회 초기화

KST = timezone(timedelta(hours=9))

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang=\"ko\">
<head>
    <meta charset=\"UTF-8\">
    <title>정보시스템실 음료 선택</title>
    <style>
        body {
            font-family: 'Segoe UI', sans-serif;
            margin: 50px;
            background: #f9f9f9;
        }
        .container {
            display: flex;
            gap: 30px;
            justify-content: center;
        }
        .box {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 10px rgba(0,0,0,0.1);
            flex: 1;
        }
        h2, h3 {
            text-align: center;
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
            gap: 10px;
        }
        input {
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 6px;
            font-size: 16px;
        }
        .error-msg {
            color: red;
            font-size: 14px;
            display: none;
        }
        .temp-buttons {
            display: flex;
            gap: 10px;
        }
        .temp-buttons button {
            flex: 1;
            padding: 10px;
            border: none;
            font-size: 16px;
            border-radius: 6px;
            cursor: pointer;
            color: white;
        }
        .ice { background-color: #5c9cff; }
        .hot { background-color: #ff5c5c; }
        .temp-buttons button:hover { opacity: 0.85; }

        ul { list-style: none; padding: 0; }
        li {
            padding: 8px;
            margin-bottom: 6px;
            background: #fff;
            border-left: 6px solid #5c9cff;
            border-radius: 6px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .drink-info {
            flex: 1;
            padding-left: 8px;
        }
        .delete-form {
            margin: 0;
        }
        .delete-button {
            background: #bbb;
            color: white;
            border: none;
            padding: 6px 12px;
            font-size: 14px;
            border-radius: 4px;
            cursor: pointer;
        }
        .delete-button:hover {
            background: #999;
        }
    </style>
</head>
<body>
    <h2>음료 주문</h2>
    <div class=\"container\">
        <div class=\"box\">
            <form method=\"post\">
                <input type=\"text\" name=\"name\" placeholder=\"이름 입력\" maxlength=\"10\" required>
                <input type=\"text\" name=\"drink\" placeholder=\"음료 입력\" maxlength=\"20\" required>
                <div id=\"error-msg\" class=\"error-msg\">이름과 음료를 모두 입력해주세요.</div>
                <div class=\"temp-buttons\">
                    <button type=\"button\" name=\"temperature\" value=\"아이스\" class=\"ice\">&#x1F9CA; 아이스</button>
                    <button type=\"button\" name=\"temperature\" value=\"따뜻한\" class=\"hot\">&#x1F525; 핫</button>
                </div>
            </form>
            {% if orders %}
            <h3>주문 현황</h3>
            <ul>
                {% for idx, order in enumerate(orders) %}
                <li>
                    <div class=\"drink-info\">
                        {{ idx+1 }}. <strong>{{ order['name'] }}</strong> → {{ order['temperature'] }} {{ order['drink'] }}
                    </div>
                    <form method=\"post\" action=\"/delete\" class=\"delete-form\">
                        <input type=\"hidden\" name=\"index\" value=\"{{ idx }}\">
                        <button class=\"delete-button\">삭제</button>
                    </form>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>
        <div class=\"box\">
            <h3>주문판</h3>
            {% if summary %}
                <ul>
                    {% for item, count in summary.items() %}
                        <li>{{ item }}: {{ count }}잔</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>주문이 아직 없습니다.</p>
            {% endif %}
        </div>
    </div>
    <div style=\"text-align: center; margin-top: 40px;\">
        <img src=\"{{ url_for('static', filename='menu.jpg') }}\"
             alt=\"지하1층 메뉴판\"
             id=\"menu-img\"
             style=\"width: 100%; max-width: 500px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); cursor: pointer;\">
            </div>
    <div style=\"text-align: center; margin-top: 20px;\">
        <img src=\"{{ url_for('static', filename='2F_menu.jpg') }}\"
             alt=\"2층 메뉴판\"
             id=\"menu2f-img\"
             style=\"width: 100%; max-width: 500px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); cursor: pointer;\">
        <p style=\"color: #555; margin-top: 10px;\">※ 메뉴판을 클릭하면 확대됩니다 🧋</p>
    </div>
    <div id=\"img-modal\" style=\"display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background-color: rgba(0,0,0,0.8); z-index: 9999; justify-content: center; align-items: center;\">
        <img id=\"modal-img\" src=\"\" alt=\"확대 메뉴판\" style=\"max-width: 90%; max-height: 90%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);\">
    </div>
    <script>
        const img = document.getElementById('menu-img');
        const img2f = document.getElementById('menu2f-img');
        const modal = document.getElementById('img-modal');
        const modalImg = document.getElementById('modal-img');

        function showModal(targetImg) {
            modalImg.src = targetImg.src;
            modal.style.display = 'flex';
        }

        img.addEventListener('click', () => showModal(img));
        img2f.addEventListener('click', () => showModal(img2f));
        modal.addEventListener('click', () => modal.style.display = 'none');

        function throttle(func, limit) {
            let lastCall = 0;
            return function (e) {
                e.preventDefault();
                const now = Date.now();
                if (now - lastCall >= limit) {
                    lastCall = now;
                    func.call(this, e);
                }
            };
        }

        const buttons = document.querySelectorAll('.temp-buttons button');
        const throttledSubmit = throttle(function (e) {
            const form = e.target.closest('form');
            const name = form.querySelector('input[name="name"]').value.trim();
            const drink = form.querySelector('input[name="drink"]').value.trim();
            const errorMsg = document.getElementById("error-msg");

            if (!name || !drink) {
                errorMsg.style.display = "block";
                return;
            } else {
                errorMsg.style.display = "none";
            }

            const temperature = e.target.value;
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'temperature';
            hidden.value = temperature;
            form.appendChild(hidden);

            form.submit();
        }, 1000);

        buttons.forEach(button => {
            button.addEventListener('click', throttledSubmit);
        });
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    global orders, last_reset_date

    now = datetime.now(KST)
    today_str = now.strftime("%Y-%m-%d")
    print(f"[DEBUG] 현재 시간: {now}, 기준 날짜: {today_str}, last_reset_date: {last_reset_date}")

    if now.hour >= 18:
        if last_reset_date != today_str:
            orders = []
            last_reset_date = today_str
            print(f"[RESET] 주문 내역 초기화됨 at {now}")

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        drink = request.form.get('drink', '').strip()
        temperature = request.form.get('temperature', '').strip()

        if not name or not drink:
            return "이름과 음료는 필수입니다.", 400

        if temperature not in ['아이스', '따뜻한']:
            return "온도 선택이 올바르지 않습니다. (아이스 / 따뜻한)", 422

        orders.append({
            'name': name,
            'drink': drink,
            'temperature': temperature
        })
        return redirect(url_for('index'))

    summary_counter = Counter(f"{order['temperature']} {order['drink']}" for order in orders)
    return render_template_string(
        HTML_TEMPLATE,
        orders=orders,
        enumerate=enumerate,
        summary=summary_counter
    )

@app.route('/delete', methods=['POST'])
def delete():
    idx = int(request.form['index'])
    if 0 <= idx < len(orders):
        orders.pop(idx)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
