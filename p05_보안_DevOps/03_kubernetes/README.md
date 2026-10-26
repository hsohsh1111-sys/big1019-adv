# 03. Kubernetes — 로컬 클러스터(kind)에 배포하기 (무료)

`02_docker`의 방문자 카운터를 쿠버네티스에 배포하고 **자가 치유·롤링 업데이트·확장**을 체험합니다.

필요: Docker Desktop, [kind](https://kind.sigs.k8s.io/docs/user/quick-start/#installation), [kubectl](https://kubernetes.io/docs/tasks/tools/)
(Docker Desktop의 Settings → Kubernetes 활성화나 minikube를 써도 됩니다. 이때는 NodePort 대신 `kubectl port-forward`를 사용하세요.)

## 1. 클러스터 생성 & 이미지 준비

```bash
kind create cluster --name edu --config kind-config.yaml
kubectl get nodes                                    # control-plane 1 + worker 2

docker build -t visit-counter:v1 ../02_docker
kind load docker-image visit-counter:v1 --name edu   # 로컬 이미지를 클러스터 노드에 복사
```

## 2. 배포

```bash
kubectl apply -f k8s/
kubectl get all -n edu                               # Pod 3개 + redis 1개 Running 확인
curl http://localhost:30080                          # 여러 번 호출 → hostname이 바뀜 (로드밸런싱)
```

## 3. 체험 1: 자가 치유

```bash
kubectl get pods -n edu -l app=visit-counter
kubectl delete pod -n edu <Pod 이름 하나>
kubectl get pods -n edu -w                           # 새 Pod가 자동 생성 → 다시 3개 (Ctrl+C로 종료)
```

## 4. 체험 2: 롤링 업데이트 & 롤백

```bash
# 설정만 바꿔 새 버전 배포 (이미지 v2를 만들어도 됨)
kubectl set env deployment/visit-counter -n edu APP_VERSION=v2
kubectl rollout status deployment/visit-counter -n edu   # Pod가 하나씩 교체 (무중단)
curl http://localhost:30080                              # "version": "v2"

kubectl rollout history deployment/visit-counter -n edu
kubectl rollout undo deployment/visit-counter -n edu     # 문제 생기면 이전 버전으로 롤백
```

## 5. 체험 3: 확장

```bash
kubectl scale deployment/visit-counter -n edu --replicas=5   # 수동 확장
# 자동 확장(HPA)을 보려면 metrics-server 설치 (kind는 TLS 옵션 추가 필요)
kubectl apply -f https://github.com/kubernetes-sigs/metrics-server/releases/latest/download/components.yaml
kubectl patch deployment metrics-server -n kube-system --type=json \
  -p '[{"op":"add","path":"/spec/template/spec/containers/0/args/-","value":"--kubelet-insecure-tls"}]'
kubectl get hpa -n edu
```

## 6. 정리

```bash
kind delete cluster --name edu
```

## 매니페스트 포인트

| 파일 | 포인트 |
|---|---|
| `10-config.yaml` | ConfigMap(설정)·Secret(비밀) 분리, Secret은 base64일 뿐 **암호화 아님** |
| `20-redis.yaml` | Service 이름 `redis` = 클러스터 내부 DNS 이름 |
| `30-app.yaml` | replicas 3, RollingUpdate, readiness/liveness 프로브, requests/limits, **non-root + 읽기 전용 파일시스템** |
| `40-hpa.yaml` | CPU 60% 기준 3~6개 자동 확장 |

> 이 예제의 Redis는 Pod가 재시작되면 데이터가 사라집니다. 실무에서는 PersistentVolume 또는 관리형 서비스(ElastiCache)를 사용합니다.
