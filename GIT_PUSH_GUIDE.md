# GitHub Push 가이드

## 현재 상태

- **Git 저장소**: 초기화됨
- **변경사항**: 커밋 완료
- **Remote**: https://github.com/smsh73/hmm.git

## Push 방법

### 방법 1: 직접 Push

```bash
cd "/Users/seungminlee/Downloads/HMM 2"
git push origin main
```

### 방법 2: 저장소 확인 후 Push

저장소가 존재하지 않는 경우 GitHub에서 먼저 생성해야 합니다:

1. https://github.com/smsh73 에서 새 저장소 생성
2. 저장소 이름: `hmm`
3. Public 또는 Private 선택
4. README, .gitignore, license는 추가하지 않음 (이미 있음)

그 다음:
```bash
cd "/Users/seungminlee/Downloads/HMM 2"
git push -u origin main
```

### 방법 3: Force Push (주의)

기존 저장소와 충돌이 있는 경우:
```bash
git push -u origin main --force
```

⚠️ **주의**: Force push는 기존 히스토리를 덮어씁니다.

## 저장소 확인

### Remote 확인
```bash
git remote -v
```

### 저장소 URL 변경
```bash
git remote set-url origin https://github.com/smsh73/hmm.git
```

## 인증 문제

### Personal Access Token 사용

GitHub에서 Personal Access Token이 필요한 경우:

1. GitHub Settings > Developer settings > Personal access tokens > Tokens (classic)
2. 새 토큰 생성 (repo 권한)
3. Push 시 토큰 사용:
   ```bash
   git push https://<token>@github.com/smsh73/hmm.git main
   ```

### SSH 사용

SSH 키가 설정된 경우:
```bash
git remote set-url origin git@github.com:smsh73/hmm.git
git push origin main
```

## 커밋된 변경사항

다음 기능들이 커밋되었습니다:
- 다국어 문서 전처리 기능
- 모델 서빙 인프라 개선 (단일 모델 제한, load/unload/replace)
- 검색 피드백 루프 기능
- 데이터베이스 마이그레이션 (Alembic)
- Sample Docs 처리 스크립트
- 배포 가이드 문서

## 문제 해결

### 500 Internal Server Error
- GitHub 서버 일시적 문제일 수 있음
- 잠시 후 다시 시도
- 또는 GitHub에서 저장소가 존재하는지 확인

### 저장소가 존재하지 않음
- GitHub에서 새 저장소 생성 필요
- 또는 저장소 이름 확인 (대소문자 구분)

### 인증 오류
- Personal Access Token 필요
- 또는 SSH 키 설정 필요

## 다음 단계

1. GitHub에서 저장소 확인: https://github.com/smsh73/hmm
2. Push 성공 확인
3. README.md 업데이트 (선택사항)

