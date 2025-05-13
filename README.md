# phd_workshop: kubernetes resource dumper

Скрипт и инфраструктура для периодического сбора информации обо всех Kubernetes-ресурсах в кластере и сохранения их в архив `k8s-dump.zip`.

## Что делает

- Получает список всех ресурсов из `kubectl api-resources`
- Делает `kubectl get -o json` и `kubectl describe` по каждому ресурсу
- Собирает события `kubectl get events -A`
- Упаковывает всё в `k8s-dump.zip`
- Запускается как Kubernetes CronJob

## Структура
```text
k8s-dumper/
├── Dockerfile                  # Контейнер со скриптом + kubectl
├── dump_k8s_resources.py       # Основной скрипт
├── rbac.yaml                   # Права доступа к кластеру
├── k8s-dumper-cronjob.yaml     # CronJob на каждый день
└── README.md                   # Документация
```

## Установка

1. Собери и запушь образ:

`docker build -t my-k8s-dumper .`

`docker tag my-k8s-dumper registry.example.com/tools/my-k8s-dumper`

`docker push registry.example.com/tools/my-k8s-dumper`

2. Примени манифесты:

`kubectl apply -f rbac.yaml`

`kubectl apply -f k8s-dumper-cronjob.yaml`

3. Дождиcь выполнения и скачай архив:

`POD=$(kubectl get pod -l job-name=k8s-dumper -o name)`

`kubectl cp $POD:/app/k8s-dump.zip ./k8s-dump.zip`

Права доступа
RBAC разрешает get, list, describe для всех ресурсных API-групп:
```text
- core
- apps
- batch
- rbac.authorization.k8s.io
- autoscaling
- networking.k8s.io
- policy
```

По расписанию
CronJob запускается ежедневно в 01:00.
