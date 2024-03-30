import os
import unicodedata

dir_path = 'src'

files = os.listdir(dir_path)

for file in files:
    nfc_file_name = unicodedata.normalize("NFC", file).encode("utf-8")
    os.rename(os.path.join(dir_path, file),
              os.path.join(dir_path.encode(encoding='utf-8'), nfc_file_name))
