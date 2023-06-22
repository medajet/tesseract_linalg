import base64
from io import BytesIO

import pytesseract
import requests
from PIL import Image
from pwn import *
from pyzbar.pyzbar import decode
import qrcode
from sympy import Eq, Symbol, solve
from sympy.parsing.sympy_parser import (
    implicit_multiplication_application,
    parse_expr,
    standard_transformations,
)

__author__ = "Jet"

# Connect to server
r = remote("redacted", 1337)

# Receive data from server
data = r.recvuntil("Ans>")
data = data[:-4]
data = data.decode().split(" ")[-1]

# data is a qrcode encoded in base64.
# decode the base64 into a qrcode and parse the image
img = Image.open(BytesIO(base64.b64decode(data)))
qr = decode(img)[0].data.decode()

# parse the qrcode and get the url
url = qr.split(" ")[-1]
url = url[1:]
url = url.strip()

# save url to file
r = requests.get(url, stream=True)
with open("qr.png", "wb") as f:
    for chunk in r.iter_content():
        f.write(chunk)

# use tesseract to parse the image
img = Image.open("qr.png")
s = pytesseract.image_to_string(img)
s = s.replace("[", "").replace("]", "")

mapping = {f"x{i}": chr(ord("a") + i) for i in range(8)}

eqs = []
for e in s.split("\n"):
    if e != "":
        eqs.append(e)

for i in range(len(eqs)):
    for k, v in mapping.items():
        eqs[i] = eqs[i].replace(k, v)

print(eqs)
transformations = standard_transformations + (implicit_multiplication_application,)
eqs_sympy = [
    Eq(
        parse_expr(e.split("==")[0], transformations=transformations),
        parse_expr(e.split("==")[1], transformations=transformations),
    )
    for e in eqs
]

ans = solve(eqs_sympy, dict=True)[0]
print(ans)
ans = ans[Symbol("c")]
ans = int(ans)

# generate qrcode from ans, then encode in base64
qr = qrcode.QRCode()
qr.add_data(ans)
qr.make(fit=True)
img = qr.make_image(fill_color="black", back_color="white")
buffered = BytesIO()
img.save(buffered, format="PNG")
img_str = base64.b64encode(buffered.getvalue())

r.sendline(img_str)
dat = r.recvall()
print(dat)
print(str(dat))

r.close()
