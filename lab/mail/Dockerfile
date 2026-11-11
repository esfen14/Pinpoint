# Lab mail sink: an SMTP server that requires STARTTLS and a login, keeps every
# message it receives, and lists them over HTTP. It stands in for the real relay
# (Gmail or a company server) so the SMTP settings can be tested end to end.
FROM python:3.12-slim
RUN pip install --no-cache-dir aiosmtpd==1.4.6 cryptography==43.0.3
COPY lab/mail/mail_sink.py /usr/local/bin/mail_sink.py
EXPOSE 587 8025
ENTRYPOINT ["python3", "-u", "/usr/local/bin/mail_sink.py"]
