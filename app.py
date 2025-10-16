from flask import Flask, request, redirect, url_for, render_template, jsonify
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

# 위치별 전체 메뉴 데이터 정의 (Single Source of Truth)
drink_menu_map = {
    'B1': {
        'drinks': [
            '아메리카노', '카페 라떼', '바닐라빈 라떼', '헤이즐넛 라떼', '돌체 라떼',
            '카라멜 마끼아또', '더블초콜릿 모카', '콜드브루', '콜드 브루 라떼',
            '파파야 블렌딩', '오렌지베리 블렌딩', '레몬그라스 블렌딩', '스윗루이보스 블렌딩',
            '오미자 차', '매실 차', '자몽 차', '레몬 차', '배.도라지.대추 차',
            '패션후르츠 칸티노', '딸기 칸티노', '플레인 요거트 칸티노', '망고 요거트 칸티노',
            '오미자 에이드', '매실 에이드', '자몽 에이드', '핑크레몬 에이드', '망고패션후르츠 에이드', '딸기 에이드',
            '초콜릿', '단팥 라떼', '토피넛 라떼', '칸틴 밀크티', '쑥 라떼', '딸기듬뿍 우유', '제주말차 라떼'
        ],
        'coffee_drinks': [
            '아메리카노', '카페 라떼', '바닐라빈 라떼', '헤이즐넛 라떼',
            '돌체 라떼', '카라멜 마끼아또', '더블초콜릿 모카'
        ],
        'beans': [
            "원두001 (묵직한바디의 강한로스팅)",
            "원두002 (부드러운산미의 미디엄로스팅)",
            "디카페인원두"
        ]
    },
    '2F': {
        'drinks': [
            "에스프레소", "아메리카노", "스테이트 블라썸 스페셜티",
            "카페 라떼", "카푸치노", "아인슈페너", "피스타치오 크림 라떼",
            "바닐라 라떼", "카페 모카", "연유 라떼", "바닐라빈 라떼", "오트 라떼",
            "클래식 루이보스", "글로우 히비스커스", "젠틀 캐모마일", "브리즈 페퍼민트",
            "블루밍 그린", "조선 브렉퍼스트", "루이보스 바닐라", "씨 브리즈", "얼 그레이", "그린 루바브",
            "오미자 히비스커스 티", "진저 레몬 티", "히비스커스 뱅쇼 티",
            "유자 민트 티", "허니 자몽 그린티",
            "복숭아 아이스 티", "유자차", "미숫가루 라떼", "청귤차",
            "밀크티", "녹차 라떼", "초콜릿 라떼", "밤 라떼",
            "초당옥수수 라떼", "흑임자 크림 라떼", "딸기 피스타치오 라떼",
            "유자 에이드", "청귤 에이드", "유자 슬러시", "베리믹스 스무디",
            "자몽 에이드", "오미자 뱅쇼 슬러시", "애플망고 스무디",
            "플레인 요거트 스무디", "복숭아 요거트 스무디"
        ],
        'coffee_drinks': [
            '에스프레소', '아메리카노', '스테이트 블라썸 스페셜티', '카페 라떼', '카푸치노', '아인슈페너',
            '피스타치오 크림 라떼', '바닐라 라떼', '카페 모카', '연유 라떼', '바닐라 빈 라떼', '오트 라떼'
        ],
        'beans': [
            "콜롬비아 유기농",
            "스테이트 블라썸",
            "디카페인원두"
        ]
    },
    'SAND': {
        'drinks': [
            # 커피 (기본 2샷)
            "아메리카노", "카페라떼", "샌드크림라떼",
            "바닐라라떼", "돌체라떼", "카페모카",
            "아샷추",

            # 디카페인 (기본 2샷)
            "디카페인 아메리카노", "디카페인 카페라떼",
            "디카페인 바닐라라떼", "디카페인 돌체라떼",
            "디카페인 아샷추",
            
            # 논-커피
            "딸기라떼", "말차라떼", "초코라떼",
            "흑임자라떼", "복숭아 아이스티", "밀크티",
            
            # 에이드
            "청포도 에이드", "자몽 에이드", "레몬 에이드",
            
            # 스무디 & 쉐이크
            "밀크 쉐이크", "밀크 커피 쉐이크",
            "블루베리 스무디 (딸기맛)",

            # 과일 주스
            "토마토 주스", "수박주스",
            
            # 티
            "레몬티", "캐모마일", "얼그레이",
            "피치우롱", "브렉퍼스트",
            
            # 1L 보틀
            "보틀 아메리카노", "보틀 카페라떼",
            "보틀 바닐라라떼", "보틀 돌체라떼",
            "보틀 디카페인 아메리카노",
            "보틀 청포도 에이드", "보틀 자몽 에이드",
            "보틀 레몬 에이드", "보틀 복숭아 아이스티",
            "보틀 초코라떼", "보틀 말차라떼",
            "보틀 딸기라떼", "보틀 밀크티",
            
            
            # 샌드위치
            "에그마요 샌드위치(딸기잼, 블루베리잼)",
            "에그마요 샌드위치 + 아메리카노",
            "햄치즈 샌드위치",
            "크랜베리 닭가슴살 샌드위치",
            "칠리 닭가슴살 샌드위치",
            "통새우 샌드위치",
            "치킨텐더 샌드위치"
        ],
        'coffee_drinks': [],
        'beans': []
    }
}

# API 엔드포인트: 메뉴 데이터 제공
@app.route('/api/menu/<location>', methods=['GET'])
def get_menu(location):
    """선택한 카페의 메뉴 데이터를 JSON으로 반환"""
    menu_data = drink_menu_map.get(location)
    if not menu_data:
        return jsonify({'error': 'Invalid location'}), 404
    
    return jsonify({
        'location': location,
        'drinks': menu_data['drinks'],
        'coffee_drinks': menu_data['coffee_drinks'],
        'beans': menu_data['beans']
    })

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
