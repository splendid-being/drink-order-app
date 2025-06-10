from flask import Flask, request, redirect, url_for, render_template
from collections import Counter
from datetime import datetime, timezone, timedelta
import re

app = Flask(__name__)
orders = []
last_reset_date = None
KST = timezone(timedelta(hours=9))

# 커피 이름에 온도 관련 단어 제거
def clean_drink_name(drink):
    return re.sub(r"(아이스|핫|뜨거운|따뜻한)\s*", "", drink, flags=re.IGNORECASE).strip()

# 소문자 + 공백 제거 정규화
def normalize(text):
    return re.sub(r"\s+", "", text.lower())

# 위치별 커피 음료 정의
drink_menu_map = {
    'B1': {
        'coffee_drinks': [
            '아메리카노', '카페 라떼', '바닐라빈 라떼', '헤이즐넛 라떼',
            '돌체 라떼', '카라멜 마끼아또', '더블초콜릿 모카'
        ]
    },
    '2F': {
        'coffee_drinks': [
            '에스프레소','아메리카노','스테이트 블라썸 스페셜티','카페 라떼','카푸치노','아인슈페너',
             '피스타치오 크림 라떼','바닐라 라떼', '카페 모카', '연유 라떼','바닐라 빈 라떼', '오트 라떼'
        ]
    }
}

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
        location = request.form.get('location', 'B1').strip()

        if not name or not drink:
            return "이름과 음료는 필수입니다.", 400
        if temperature not in ['아이스', '따뜻한']:
            return "온도 선택이 올바르지 않습니다.", 422

        cleaned_drink = clean_drink_name(drink)
        normalized_drink = normalize(cleaned_drink)

        coffee_drinks = drink_menu_map.get(location, {}).get('coffee_drinks', [])
        coffee_normalized = [normalize(c) for c in coffee_drinks]

        print(f"[DEBUG] 위치: {location}")
        print(f"[DEBUG] 정제 후 음료: {cleaned_drink} → {normalized_drink}")
        print(f"[DEBUG] 커피 음료 목록: {coffee_drinks}")

        if normalized_drink in coffee_normalized and not bean:
            return "원두 선택이 필요합니다.", 400

        order_data = {
            'name': name,
            'drink': cleaned_drink,
            'temperature': temperature,
            'location': location
        }
        if bean:
            order_data['bean'] = bean

        orders.append(order_data)
        return redirect(url_for('index'))

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
