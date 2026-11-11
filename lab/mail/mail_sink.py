"""Lab mail sink (lab only; the credentials below are not secrets).

SMTP on :587 with mandatory STARTTLS and AUTH, using a certificate signed by a
lab CA that this program creates in /ca (shared with the appliance, which trusts
it). Messages are kept in memory. HTTP on :8025:

    GET    /messages   JSON list: from, to, subject, body
    DELETE /messages   forget them all
"""
import json
import os
import ssl
import tempfile
import threading
from datetime import datetime, timedelta, timezone
from email import message_from_bytes, policy
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from aiosmtpd.controller import Controller
from aiosmtpd.smtp import AuthResult, LoginPassword
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.x509.oid import NameOID

USERNAME = "lab-smtp-user"
PASSWORD = "lab smtp pass #1"  # spaces and '#' on purpose: the helper must quote them
HOSTNAME = os.environ.get("SINK_HOSTNAME", "mail01")
CA_DIR = "/ca"

messages = []
lock = threading.Lock()


def make_certificates():
    """A lab CA and a server certificate for HOSTNAME. Returns (cert_path, key_path)."""
    now = datetime.now(timezone.utc)
    # A CA left in the volume by an earlier run would not match the new certificate.
    try:
        os.unlink(os.path.join(CA_DIR, "lab-mail-ca.crt"))
    except FileNotFoundError:
        pass

    def name(common_name):
        return x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, common_name)])

    ca_key = ec.generate_private_key(ec.SECP256R1())
    ca_cert = (x509.CertificateBuilder().subject_name(name("Pinpoint lab CA")).issuer_name(name("Pinpoint lab CA"))
               .public_key(ca_key.public_key()).serial_number(x509.random_serial_number())
               .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=30))
               .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
               .add_extension(x509.KeyUsage(digital_signature=False, content_commitment=False, key_encipherment=False,
                                            data_encipherment=False, key_agreement=False, key_cert_sign=True,
                                            crl_sign=True, encipher_only=False, decipher_only=False), critical=True)
               .add_extension(x509.SubjectKeyIdentifier.from_public_key(ca_key.public_key()), critical=False)
               .sign(ca_key, hashes.SHA256()))
    key = ec.generate_private_key(ec.SECP256R1())
    cert = (x509.CertificateBuilder().subject_name(name(HOSTNAME)).issuer_name(ca_cert.subject)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1)).not_valid_after(now + timedelta(days=30))
            .add_extension(x509.SubjectAlternativeName([x509.DNSName(HOSTNAME)]), critical=False)
            .add_extension(x509.SubjectKeyIdentifier.from_public_key(key.public_key()), critical=False)
            .add_extension(x509.AuthorityKeyIdentifier.from_issuer_public_key(ca_key.public_key()), critical=False)
            .sign(ca_key, hashes.SHA256()))

    directory = tempfile.mkdtemp()
    cert_path, key_path = os.path.join(directory, "cert.pem"), os.path.join(directory, "key.pem")
    with open(cert_path, "wb") as handle:
        handle.write(cert.public_bytes(serialization.Encoding.PEM))
    with open(key_path, "wb") as handle:
        handle.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                       serialization.NoEncryption()))
    # Written last: the appliance waits for this file.
    with open(os.path.join(CA_DIR, "lab-mail-ca.crt"), "wb") as handle:
        handle.write(ca_cert.public_bytes(serialization.Encoding.PEM))
    return cert_path, key_path


def authenticate(server, session, envelope, mechanism, auth_data):
    ok = (isinstance(auth_data, LoginPassword)
          and auth_data.login == USERNAME.encode() and auth_data.password == PASSWORD.encode())
    return AuthResult(success=ok, handled=False if not ok else True)


class Store:
    async def handle_DATA(self, server, session, envelope):
        parsed = message_from_bytes(envelope.content, policy=policy.default)
        body = parsed.get_body(preferencelist=("plain", "html"))
        with lock:
            messages.append({
                "from": envelope.mail_from,
                "to": list(envelope.rcpt_tos),
                "subject": str(parsed["Subject"] or ""),
                "body": body.get_content() if body else "",
            })
        return "250 OK"


class Listing(BaseHTTPRequestHandler):
    def _send(self, payload):
        data = json.dumps(payload).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        with lock:
            self._send(list(messages))

    def do_DELETE(self):
        with lock:
            messages.clear()
        self._send([])

    def log_message(self, *args):
        pass


def main():
    cert_path, key_path = make_certificates()
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
    context.load_cert_chain(cert_path, key_path)
    controller = Controller(Store(), hostname="0.0.0.0", port=587, tls_context=context, require_starttls=True,
                            authenticator=authenticate, auth_required=True, auth_require_tls=True)
    controller.start()
    print("mail sink ready: smtp :587 (STARTTLS, login), http :8025", flush=True)
    ThreadingHTTPServer(("0.0.0.0", 8025), Listing).serve_forever()


if __name__ == "__main__":
    main()
