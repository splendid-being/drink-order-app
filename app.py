from flask import Flask, request, redirect, url_for, render_template
from collections import Counter
from datetime import datetime, timezone, timedelta
import re

app = Flask(__name__)
orders = []
last_reset_date = None
KST = timezone(timedelta(hours=9))

def clean_drink_name(drink):
    # 온도 관련 단어 제거
    return re.sub(r"(아이스|핫|뜨거운|따뜻한)\s*", "", drink, flags=re.IGNORECASE).strip()

@app.route('/', methods=['GET', 'POST'])
def index():
    global orders, last_reset_date

    now = datetime.now(KST)
    today_str = now.strftime("%Y-%m-%d")
    if now.hour >= 18 and last_reset_date != today_str:
        orders = []
        last_reset_date = today_str
        print(f"[RESET] 주문 내역 초기화됨 at {now}")

    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        drink = request.form.get('drink', '').strip()
        temperature = request.form.get('temperature', '').strip()
        bean = request.form.get('bean', '').strip()

        if not name or not drink:
            return "이름과 음료는 필수입니다.", 400
        if temperature not in ['아이스', '따뜻한']:
            return "온도 선택이 올바르지 않습니다.", 422

        normalized_drink = re.sub(r"\s+", "", drink.lower())
        if any(x in normalized_drink for x in ['커피', '라떼', '아메리카노', '모카']) and not bean:
            return "원두 선택이 필요합니다.", 400

        cleaned_drink = clean_drink_name(drink)
        order_data = {'name': name, 'drink': cleaned_drink, 'temperature': temperature} 
        if bean:
            order_data['bean'] = bean
        orders.append(order_data)
        return redirect(url_for('index'))

    def normalize(text): return re.sub(r"\s+", "", text.lower())
    summary_counter = Counter(
        f"{order['temperature']} {normalize(order['drink'])}" +
        (f" - {order['bean'].split()[0]}" if 'bean' in order else "")
        for order in orders
    )

    return render_template("index.html", orders=orders, enumerate=enumerate, summary=summary_counter)

@app.route('/delete', methods=['POST'])
def delete():
    idx = int(request.form['index'])
    if 0 <= idx < len(orders):
        orders.pop(idx)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
