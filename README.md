DropBoxLibrarySRC
=================

decrypted python src DropBox

Dropbox turns on logging only when the MD5 checksum of DBDEV starts with "c3da6009e4". James Hall from the #openwall channel was able to crack this partial MD5 hash and he found out that the string "a2y6shya" generates the required partial MD5 collision.

Activating logging in Dropbox now requires cracking a full SHA-256 hash (e27eae61e774b19f4053361e523c771a92e838026da42c60e6b097d9cb2bc825). The plain-text corresponding to this hash needs to be externally supplied to the Dropbox client (in order to activate logging) and this plaintext value is not public.

sha256:e27eae61e774b19f4053361e523c771a92e838026da42c60e6b097d9cb2bc825
