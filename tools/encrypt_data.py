import hashlib


def md5_encrypt(text):
    text = str(text)
    md5 = hashlib.md5()
    md5.update(text.encode('utf-8'))
    return md5.hexdigest()
