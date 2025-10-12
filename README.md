# 🍹 Drink Order App

Flask 기반 음료 주문 애플리케이션

## 설명
사무실이나 팀에서 음료를 단체 주문할 때 사용하는 웹 애플리케이션입니다.

## 주요 기능
- 🏢 2개 카페 선택 (지하1층 칸틴, 2층 카페)
- 🔍 음료 자동완성 기능
- ☕ 커피 음료 선택 시 원두 선택 필수
- 🧊 아이스/핫 선택
- 📋 실시간 주문 내역 및 집계 확인
- ⏰ 매일 오후 6시 자동 초기화

## 실행 방법

```bash
# 저장소 클론
git clone https://github.com/splendid-being/drink-order-app.git
cd drink-order-app

# 패키지 설치
pip install -r requirements.txt

# 앱 실행
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 기술 스택
- **Backend**: Flask (Python)
- **Frontend**: HTML, CSS, JavaScript
- **스타일**: Pretendard 폰트, 반응형 디자인

## 프로젝트 구조
```
drink-order-app/
├── app.py                 # Flask 메인 애플리케이션
├── requirements.txt       # Python 의존성
├── templates/
│   └── index.html        # 메인 페이지
└── static/
    ├── css/
    │   └── style.css     # 스타일시트
    └── *.jpg, *.jpeg     # 메뉴판 이미지
```
