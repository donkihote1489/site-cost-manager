# 🏗️ 전문건설 현장비용 관리 시스템

이 프로젝트는 전문건설업체 본사의 공사관리팀에서 사용하는 **현장별 월간 비용 관리 시스템**입니다.

## 주요 기능
- 로그인 (현장 / 본사 공무팀 / 경영지원부 권한 구분)
- 비용유형별 절차 흐름 자동 초기화 및 상태관리
- 금액 입력 기능 (기성금, 노무비, 투입비)
- 절차 단계 진행 상황 트래킹
- 현장별 손수익 및 노무비 비중 요약 대시보드
- Streamlit 기반 시각화 및 웹UI
- SQLite 데이터베이스 사용 (자동 생성 및 저장)

## 실행 방법
```bash
pip install -r requirements.txt
streamlit run main.py
```

## 디렉토리 구조
.
├── main.py
├── auth.py
├── db.py
├── procedure.py
├── dashboard.py
├── requirements.txt
├── README.md
└── .streamlit
    └── config.toml
