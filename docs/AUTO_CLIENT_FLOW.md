# Auto Client Flow

## Conversation-first

Client talks to **AI Менеджер**. Forms exist only when an operation truly needs structured data (e.g. creating a warehouse car).

## Happy path

```
USER: Найди BMW X5 в Одессе до 15000$ и пришли сюда.
AI:   Ищу BMW X5, Одесса, до $15 000.
      Нашёл N вариантов. + cards
USER: Только дизель.
AI:   (same slots + fuel=diesel) updated results
```

## Forbidden

- Re-ask brand / budget / city already known
- Ask phone / VIN / year unless needed for sell/valuation
- Show Score / Priority / Dept / Intent / tenant IDs
- English technical errors (`No active tenant context`, `Dealer rates not configured…`)
