from flask import Flask, request, redirect, url_for, render_template_string
from collections import Counter

app = Flask(__name__)
orders = []

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
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
    <div class="container">

        <!-- 왼쪽: 입력 및 상세 리스트 -->
        <div class="box">
            <form method="post">
                <input type="text" name="name" placeholder="이름 입력" required>
                <input type="text" name="drink" placeholder="음료 입력" required>
                <div class="temp-buttons">
                    <button name="temperature" value="아이스" class="ice">🧊 아이스</button>
                    <button name="temperature" value="따뜻한" class="hot">🔥 핫</button>
                </div>
            </form>

            {% if orders %}
            <h3>주문 현황</h3>
            <ul>
                {% for idx, order in enumerate(orders) %}
                <li>
                    <div class="drink-info">
                        {{ idx+1 }}. <strong>{{ order['name'] }}</strong> → {{ order['temperature'] }} {{ order['drink'] }}
                    </div>
                    <form method="post" action="/delete" class="delete-form">
                        <input type="hidden" name="index" value="{{ idx }}">
                        <button class="delete-button">삭제</button>
                    </form>
                </li>
                {% endfor %}
            </ul>
            {% endif %}
        </div>

        <!-- 오른쪽: 요약 리스트 -->
        <div class="box">
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
    <div style="text-align: center; margin-top: 40px;">
        <img src="{{ url_for('static', filename='menu.jpg') }}"
             alt="메뉴판"
             style="width: 100%; max-width: 500px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
        <p style="color: #555; margin-top: 10px;">※ 메뉴판을 참고해주세요 ☕</p>
    </div>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        drink = request.form.get('drink', '').strip()
        temperature = request.form.get('temperature', '').strip()
        if name and drink and temperature:
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
