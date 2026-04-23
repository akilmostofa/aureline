# Subject-wise Monthly Fee Reminder Scheduler

Use these commands after deployment or on local Windows Task Scheduler.

## Generate monthly subject invoices
```bash
python -m flask --app run.py generate-monthly-subject-invoices
```

## Send reminder SMS exactly 3 days before due date
```bash
python -m flask --app run.py send-payment-reminders
```

## Required environment variables for real SMS
- `SMS_API_URL`
- `SMS_API_KEY`
- `SMS_SENDER_ID`

If SMS is not configured, the command keeps the code path ready but will only log preview messages.
