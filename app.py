from flask import Flask, request, redirect, url_for, render_template_string
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


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <title>&#x1F964; 음료 주문</title>
    <style>
        body { font-family: 'Segoe UI', sans-serif; margin: 50px; background: #f9f9f9; }
        .container { display: flex; gap: 30px; justify-content: center; }
        .box { background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); flex: 1; }
        h1, h2, h3 { text-align: center; color: #333; }
        form { display: flex; flex-direction: column; gap: 10px; }
        input, select { padding: 10px; border: 1px solid #ccc; border-radius: 6px; font-size: 16px; }
        .error-msg { color: red; font-size: 14px; display: none; }
        .temp-buttons { display: flex; gap: 10px; }
        .temp-buttons button {
            flex: 1; padding: 10px; border: none; font-size: 16px; border-radius: 6px;
            cursor: pointer; color: white;
        }
        .ice { background-color: #5c9cff; }
        .hot { background-color: #ff5c5c; }
        .temp-buttons button:hover { opacity: 0.85; }
        ul { list-style: none; padding: 0; }
        li {
            padding: 8px; margin-bottom: 6px; background: #fff;
            border-left: 6px solid #5c9cff; border-radius: 6px;
            display: flex; justify-content: space-between; align-items: center;
        }
        .drink-info { flex: 1; padding-left: 8px; }
        .delete-form { margin: 0; }
        .delete-button {
            background: #bbb; color: white; border: none;
            padding: 6px 12px; font-size: 14px; border-radius: 4px; cursor: pointer;
        }
        .delete-button:hover { background: #999; }
        .ice-border { border-left: 6px solid #5c9cff; }
        .hot-border { border-left: 6px solid #ff5c5c; }
      
       

        #suggestions {
            width: 100%;
            left: 0;
            background: #fff;
            border-radius: 6px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            z-index: 1000;
            max-height: 160px;
            overflow-y: auto;
        }

        #suggestions div {
            padding: 10px 12px;
            cursor: pointer;
        }

        #suggestions div:last-child {
            border-bottom: none;
        }

        #suggestions div:hover {
            background-color: #f1f1f1;
        }

        .autocomplete-item.active {
            background-color: #e0f4ff;
        }

    </style>
</head>
<body>
    <h1>&#x1F964; 음료 주문</h1>
    <div class="container">
        <div class="box">
            <form method="post" style="position: relative;">
                <input type="text" name="name" placeholder="이름 입력" maxlength="10" required>
                <input type="text" name="drink" id="drink-input" placeholder="음료 입력" maxlength="20" required>
                <small style="color: #777; font-size: 13px; margin-top: -5px;">
                    &#x2328; 이제 방향키와 Enter로 자동완성 항목을 선택할 수 있어요!
                </small>
                <div id="suggestions"></div>
                <div id="bean-section" style="display: none;">
                    <label for="bean">&#x1F331; 원두 선택</label>
                    <select name="bean" id="bean">
                        <option value="">-- 원두를 선택해주세요 --</option>
                        <option value="원두001 (묵직한바디의 강한로스팅)">원두001 (묵직한바디의 강한로스팅)</option>
                        <option value="원두002 (부드러운산미의 미디엄로스팅)">원두002 (부드러운산미의 미디엄로스팅)</option>
                        <option value="디카페인원두">디카페인원두</option>
                    </select>
                </div>
                <div id="error-msg" class="error-msg">이름과 음료를 모두 입력해주세요.</div>
                <div id="bean-error" class="error-msg">원두를 선택해주세요.</div>
                <div class="temp-buttons">
                    <button type="button" name="temperature" value="아이스" class="ice">&#x1F9CA; 아이스</button>
                    <button type="button" name="temperature" value="따뜻한" class="hot">&#x1F525; 핫</button>
                </div>
            </form>
            {% if orders %}
            <h3>주문 현황</h3>
            <ul>
                {% for idx, order in enumerate(orders) %}
                <li class="{{ 'ice-border' if order['temperature'] == '아이스' else 'hot-border' }}"> 
                    <div class="drink-info">
                        {{ idx+1 }}. <strong>{{ order['name'] }}</strong> → {{ order['temperature'] }} {{ order['drink'].replace(' ', '') }}
                        {% if order.get('bean') %}
                            - {{ order['bean'] }}
                        {% endif %}
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
        <div class="box">
            <h3>&#x1F4DD; 주문판</h3>
            {% if summary %}
                <ul>
                    {% for item, count in summary.items() %}
                        <li class="{{ 'ice-border' if '아이스' in item else 'hot-border' }}"> {{ item }}: {{ count }}잔</li>
                    {% endfor %}
                </ul>
            {% else %}
                <p>주문이 아직 없습니다.</p>
            {% endif %}
        </div>
    </div>

    <!-- 메뉴판 이미지 -->
    <div style="text-align: center; margin-top: 40px;">
        <div style="display: flex; justify-content: center; gap: 20px; flex-wrap: wrap;">
            <div>
            <p style="margin-bottom: 8px; color: #333;">지하 1층 메뉴판</p>
            <img src="{{ url_for('static', filename='menu.jpg') }}"
                alt="지하1층 메뉴판"
                class="menu-img"
                style="width: 300px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); cursor: pointer;">
        </div>
        <div>
            <p style="margin-bottom: 8px; color: #333;">2층 메뉴판</p>
            <img src="{{ url_for('static', filename='2F_menu.jpeg') }}"
                alt="2층 메뉴판"
                class="menu-img"
                style="width: 300px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); cursor: pointer;">
        </div>
        </div>
        <p style="color: #555; margin-top: 10px;">※ 메뉴판을 클릭하면 확대됩니다</p>
    </div>

    <!-- 모달 이미지 확대 -->
    <div id="img-modal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%;
         background-color: rgba(0,0,0,0.8); z-index: 9999; justify-content: center; align-items: center;">
        <img id="modal-img" src="" alt="확대 메뉴판"
             style="max-width: 90%; max-height: 90%; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.4);">
    </div>

    <script>
        const drinkInput = document.getElementById('drink-input');
        const suggestions = document.getElementById('suggestions');
        const beanSection = document.getElementById('bean-section');
        const beanError = document.getElementById('bean-error');
        const beanSelect = document.getElementById('bean');
        const drinkList = [
    '아메리카노', '카페 라떼', '바닐라빈 라떼','헤이즐넛 라떼','돌체 라떼',
    '카라멜 마끼아또','더블초콜릿 모카', '콜드브루', '콜드 브루 라떼',
    '파파야 블렌딩', '오렌지베리 블렌딩', '레몬그라스 블렌딩', '스윗루이보스 블렌딩',
    '오미자 차', '매실 차','자몽 차','레몬 차','배.도라지.대추 차',
    '패션후르츠 칸티노', '딸기 칸티노', '플레인 요거트 칸티노','망고 요거트 칸티노',
    '오미자 에이드', '매실 에이드', '자몽 에이드', '핑크레몬 에이드','망고패션후르츠 에이드','딸기 에이드',
    '초콜릿', '단팥 라떼','토피넛 라떼','칸틴 밀크티','쑥 라떼', '딸기듬뿍 우유','제주말차 라떼'
];

let currentFocus = -1;

drinkInput.addEventListener('input', () => {
    const raw = drinkInput.value;
    const normalized = raw.toLowerCase().replace(/\s+/g, '');
    suggestions.innerHTML = "";
    currentFocus = -1;

    // 자동완성 추천 표시
    if (normalized.length > 0) {
        const matched = drinkList.filter(item => item.toLowerCase().includes(normalized));
        matched.slice(0, 5).forEach(match => {
            const div = document.createElement('div');
            div.textContent = match;



            div.tabIndex = -1;
            div.classList.add('autocomplete-item');
            div.addEventListener('mousedown', (e) => {
                e.preventDefault();
                drinkInput.value = match;
                suggestions.innerHTML = "";
                drinkInput.dispatchEvent(new Event('input'));
            });

            suggestions.appendChild(div);
        });
    }

        // 원두 선택 조건 확인
        const coffeeDrinks = [
            '아메리카노', '카페 라떼', '바닐라빈 라떼', '헤이즐넛 라떼',
            '돌체 라떼', '카라멜 마끼아또', '더블초콜릿 모카'
        ];

        const isCoffee = coffeeDrinks.some(name => normalized.includes(name.replace(/\s+/g, '').toLowerCase()));

        if (isCoffee) {
            beanSection.style.display = 'block';
        } else {
            beanSection.style.display = 'none';
            beanError.style.display = 'none';
            beanSelect.value = '';
        }
    });

    drinkInput.addEventListener('keydown', (e) => {
    const items = suggestions.querySelectorAll('div');
    if (e.key === 'ArrowDown') {
        currentFocus++;
        if (currentFocus >= items.length) currentFocus = 0;
        setActive(items);
        e.preventDefault();
    } else if (e.key === 'ArrowUp') {
        currentFocus--;
        if (currentFocus < 0) currentFocus = items.length - 1;
        setActive(items);
        e.preventDefault();
    } else if (e.key === 'Enter') {
        if (currentFocus > -1 && items[currentFocus]) {
            items[currentFocus].dispatchEvent(new Event('mousedown'));
            e.preventDefault();
        }
    } else if (e.key === 'Escape') {
        suggestions.innerHTML = "";
    }
    });

    function setActive(items) {
    if (!items || items.length === 0) return;
    items.forEach(item => item.classList.remove('active'));
    if (currentFocus >= 0 && currentFocus < items.length) {
        items[currentFocus].classList.add('active');
        items[currentFocus].scrollIntoView({ block: 'nearest' });
    }
}

    
        document.addEventListener('click', (e) => {
            if (!suggestions.contains(e.target) && e.target !== drinkInput) {
                suggestions.innerHTML = "";
            }
        });



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
            const bean = form.querySelector('select[name="bean"]').value.trim();
            const errorMsg = document.getElementById("error-msg");

            if (!name || !drink) {
                errorMsg.style.display = "block";
                return;
            } else {
                errorMsg.style.display = "none";
            }

            const isCoffee = drink.toLowerCase().replace(/\\s+/g, '').match(/커피|라떼|아메리카노|모카/);
            if (isCoffee && !bean) {
                beanError.style.display = "block";
                return;
            } else {
                beanError.style.display = "none";
            }

            const temperature = e.target.value;
            const hidden = document.createElement('input');
            hidden.type = 'hidden';
            hidden.name = 'temperature';
            hidden.value = temperature;
            form.appendChild(hidden);

            form.submit();
        }, 1000);
        buttons.forEach(button => button.addEventListener('click', throttledSubmit));

        // 메뉴판 확대
        document.querySelectorAll('.menu-img').forEach(img => {
            img.addEventListener('click', () => {
                document.getElementById('modal-img').src = img.src;
                document.getElementById('img-modal').style.display = 'flex';
            });
        });
        document.getElementById('img-modal').addEventListener('click', () => {
            document.getElementById('img-modal').style.display = 'none';
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

    return render_template_string(HTML_TEMPLATE, orders=orders, enumerate=enumerate, summary=summary_counter)

@app.route('/delete', methods=['POST'])
def delete():
    idx = int(request.form['index'])
    if 0 <= idx < len(orders):
        orders.pop(idx)
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
