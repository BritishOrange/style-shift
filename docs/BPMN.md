# BPMN: эксплуатация модели в StyleShift

Бизнес-процесс **эксплуатации** (operation) модели `Qwen2.5-1.5B-Instruct`
в проекте StyleShift: от запуска сервиса до выдачи перефразированного текста.

## Как открыть диаграмму

1. Файл BPMN 2.0: [`bpmn/styleshift-model-operation.bpmn`](bpmn/styleshift-model-operation.bpmn)
2. Откройте на [https://demo.bpmn.io](https://demo.bpmn.io) → *Open file*
   или в [Camunda Modeler](https://camunda.com/download/modeler/) / draw.io (импорт BPMN).

## Участники (pools)

| Pool | Роль |
|------|------|
| **Пользователь (браузер)** | Вводит текст, выбирает стиль, получает результат |
| **StyleShift Service** | Flask API: загрузка модели, валидация, оркестрация инференса |
| **Model Runtime (Qwen2.5)** | Загрузка весов (HF cache) и авторегрессионная генерация на CPU |

## Схема процесса (обзор)

```mermaid
flowchart TB
  subgraph User["Пользователь"]
    U1([Старт]) --> U2[Открыть localhost:3000]
    U2 --> U3[Дождаться «Модель готова»]
    U3 --> U4[Выбрать стиль, ввести текст]
    U4 --> U5[Перефразировать]
    U5 --> U6[Посмотреть результат]
    U6 --> U7{Ещё запрос?}
    U7 -->|да| U4
    U7 -->|нет| U8([Конец])
  end

  subgraph Service["StyleShift Service"]
    S1([poetry run styleshift]) --> S2[Boot Flask + фон. загрузка]
    S2 --> S3[Load tokenizer + weights]
    S3 --> S4{Успех?}
    S4 -->|да| S5[status = ready]
    S4 -->|нет| S6[status = error]
    S5 --> S7[Listen :3000]
    S6 --> S7
    S7 --> S8[Принять POST /api/rewrite]
    S8 --> S9{ready?}
    S9 -->|нет| S12[HTTP 503]
    S9 -->|да| S10{Валидный вход?}
    S10 -->|нет| S13[HTTP 400]
    S10 -->|да| S11[Промпт + generate]
    S11 --> S14[clean_reply]
    S14 --> S15{Непустой?}
    S15 -->|да| S16[HTTP 200 JSON]
    S15 -->|нет| S17[HTTP 500]
  end

  subgraph Model["Model Runtime"]
    M1[from_pretrained / кэш HF]
    M2[model.generate CPU sampling]
  end

  U3 -.->|GET /api/health| S7
  U5 -.->|POST /api/rewrite| S8
  S3 <-->|веса| M1
  S11 <-->|токены| M2
  S12 & S13 & S16 & S17 -.->|ответ| U6
```

## Ключевые развилки

1. **Загрузка модели** — успех → `ready`, иначе `error` (сервис всё равно слушает порт; rewrite даст 503).
2. **Готовность к инференсу** — не `ready` → **503**.
3. **Валидация** — пустой текст / неизвестный стиль / &gt;2000 символов → **400**.
4. **Пустой ответ после очистки** → **500**, иначе **200** с `rewritten`.

## Связь с кодом

| Шаг BPMN | Код |
|----------|-----|
| Boot + фоновая загрузка | `styleshift.__main__.main`, `ModelService.start_background_load` |
| Load weights | `ModelService.load` |
| Health / styles / rewrite | `styleshift.app.create_app` |
| generate + clean | `ModelService.rewrite`, `clean_reply` |
