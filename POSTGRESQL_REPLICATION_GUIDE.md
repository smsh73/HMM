# PostgreSQL 복제 설정 가이드

## 개요

HMM GenAI 문서 검색/요약 시스템의 메인 시스템과 선박 시스템 간 데이터 동기화를 위한 PostgreSQL 복제 설정 가이드입니다.

## 복제 방식

### 1. 스트리밍 복제 (Streaming Replication)
- PostgreSQL의 기본 복제 방식
- WAL(Write-Ahead Log) 전송을 통한 실시간 복제
- 비동기 또는 동기 복제 지원

### 2. 논리적 복제 (Logical Replication)
- 테이블 단위 복제
- 더 세밀한 제어 가능
- 버전 10 이상 지원

## 설정 방법

### 메인 시스템 (Primary Server) 설정

#### 1. PostgreSQL 설정 파일 수정 (`postgresql.conf`)

```conf
# 복제 연결 허용
wal_level = replica  # 또는 logical (논리적 복제 사용 시)

# 최대 WAL 전송 연결 수
max_wal_senders = 3

# WAL 보관 설정
wal_keep_segments = 32  # 또는 wal_keep_size = 512MB (PostgreSQL 13+)

# 복제 슬롯 사용 (선택사항, 권장)
max_replication_slots = 3
```

#### 2. 인증 설정 (`pg_hba.conf`)

```conf
# 복제 연결 허용
host    replication     replicator      <선박_시스템_IP>/32    md5
```

#### 3. 복제 사용자 생성

```sql
-- 복제 전용 사용자 생성
CREATE USER replicator WITH REPLICATION PASSWORD 'replication_password';

-- 권한 부여
GRANT CONNECT ON DATABASE hmm_db TO replicator;
```

#### 4. 복제 슬롯 생성 (선택사항)

```sql
-- 복제 슬롯 생성
SELECT pg_create_physical_replication_slot('ship_system_slot');
```

### 선박 시스템 (Standby Server) 설정

#### 1. 초기 데이터 복사

```bash
# 메인 시스템에서 베이스 백업 생성
pg_basebackup -h <메인_시스템_IP> -D /var/lib/postgresql/data -U replicator -P -v -R -S ship_system_slot
```

#### 2. 복구 설정 (`postgresql.conf` 또는 `postgresql.auto.conf`)

```conf
# 스탠바이 모드 활성화
primary_conninfo = 'host=<메인_시스템_IP> port=5432 user=replicator password=replication_password'
primary_slot_name = 'ship_system_slot'
```

#### 3. 복구 모드 설정 (`recovery.conf` 또는 `postgresql.auto.conf`)

```conf
# PostgreSQL 12 이상
restore_command = 'cp /var/lib/postgresql/archive/%f %p'
standby_mode = 'on'
```

## 논리적 복제 설정 (테이블 단위)

### 메인 시스템 설정

#### 1. 논리적 복제 활성화

```conf
# postgresql.conf
wal_level = logical
max_replication_slots = 3
max_worker_processes = 4
```

#### 2. 발행(Publication) 생성

```sql
-- 전체 데이터베이스 발행
CREATE PUBLICATION hmm_publication FOR ALL TABLES;

-- 또는 특정 테이블만 발행
CREATE PUBLICATION hmm_publication FOR TABLE 
    documents, document_chunks, users, llm_providers;
```

### 선박 시스템 설정

#### 1. 구독(Subscription) 생성

```sql
-- 구독 생성
CREATE SUBSCRIPTION hmm_subscription
CONNECTION 'host=<메인_시스템_IP> port=5432 user=replicator password=replication_password dbname=hmm_db'
PUBLICATION hmm_publication;

-- 구독 상태 확인
SELECT * FROM pg_subscription;
```

## 모니터링

### 복제 상태 확인

```sql
-- 메인 시스템에서 복제 상태 확인
SELECT * FROM pg_stat_replication;

-- 복제 슬롯 상태 확인
SELECT * FROM pg_replication_slots;

-- 논리적 복제 상태 확인
SELECT * FROM pg_stat_subscription;
```

### 지연 확인

```sql
-- 복제 지연 확인
SELECT 
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), sent_lsn) AS send_lag,
    pg_wal_lsn_diff(sent_lsn, write_lsn) AS write_lag,
    pg_wal_lsn_diff(write_lsn, flush_lsn) AS flush_lag,
    pg_wal_lsn_diff(flush_lsn, replay_lsn) AS replay_lag
FROM pg_stat_replication;
```

## 자동 페일오버 설정 (선택사항)

### pg_auto_failover 사용

```bash
# pg_auto_failover 설치
# Ubuntu/Debian
sudo apt-get install postgresql-auto-failover

# 설정
pg_autoctl create monitor --pgdata /var/lib/postgresql/monitor
pg_autoctl create postgres --pgdata /var/lib/postgresql/data --monitor 'postgresql://autoctl_node@monitor:5432/pg_auto_failover'
```

## 네트워크 설정

### 방화벽 설정

```bash
# 메인 시스템
sudo ufw allow from <선박_시스템_IP> to any port 5432

# 선박 시스템
sudo ufw allow from <메인_시스템_IP> to any port 5432
```

### SSL 연결 (권장)

```conf
# postgresql.conf
ssl = on
ssl_cert_file = '/etc/ssl/certs/server.crt'
ssl_key_file = '/etc/ssl/private/server.key'
```

## 문제 해결

### 복제 연결 실패

1. 네트워크 연결 확인
2. `pg_hba.conf` 설정 확인
3. 방화벽 설정 확인
4. 사용자 권한 확인

### 복제 지연

1. 네트워크 대역폭 확인
2. WAL 보관 설정 확인
3. 복제 슬롯 사용 고려
4. 동기 복제 모드 고려 (성능 영향 있음)

### 복제 슬롯 누수

```sql
-- 사용하지 않는 복제 슬롯 삭제
SELECT pg_drop_replication_slot('slot_name');
```

## 성능 최적화

### 비동기 복제 (기본)
- 빠른 성능
- 약간의 데이터 손실 가능성

### 동기 복제
- 데이터 일관성 보장
- 성능 저하 가능

```sql
-- 동기 복제 설정
ALTER SYSTEM SET synchronous_standby_names = 'ship_system';
SELECT pg_reload_conf();
```

## 백업 및 복구

### 베이스 백업

```bash
# 정기적인 베이스 백업
pg_basebackup -h <메인_시스템_IP> -D /backup/base -U replicator -P -v -F tar -z -p
```

### 복구

```bash
# 백업에서 복구
pg_restore -d hmm_db /backup/base/base.tar
```

## 보안 고려사항

1. **암호화**: SSL/TLS 연결 사용
2. **인증**: 강력한 비밀번호 사용
3. **네트워크**: VPN 또는 전용 네트워크 사용
4. **모니터링**: 복제 상태 정기적 확인

## 자동화 스크립트

### 복제 상태 모니터링 스크립트

```bash
#!/bin/bash
# check_replication.sh

PRIMARY_HOST="<메인_시스템_IP>"
DB_NAME="hmm_db"
USER="replicator"

psql -h $PRIMARY_HOST -U $USER -d $DB_NAME -c "
SELECT 
    client_addr,
    state,
    sync_state,
    pg_wal_lsn_diff(pg_current_wal_lsn(), replay_lsn) AS lag_bytes
FROM pg_stat_replication;
"
```

## 참고 자료

- [PostgreSQL 공식 문서 - 복제](https://www.postgresql.org/docs/current/high-availability.html)
- [PostgreSQL 논리적 복제](https://www.postgresql.org/docs/current/logical-replication.html)
- [pg_auto_failover](https://github.com/citusdata/pg_auto_failover)

