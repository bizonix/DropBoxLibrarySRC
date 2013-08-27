#Embedded file name: dropbox/client/panda.py
import zlib
from dropbox.trace import TRACE, unhandled_exc_handler

def panda():
    try:
        data = '\neJyllr1qAzEMx3c/hbnlKJiOxXmEW4qnQpY733EZCmkLhUIfv/62JMuXtNWQIbF+kv6xJAshD21R\n677rbVWH59Sus22HJ+u5cPYoqg+6HLAwSuuHf2U2EZqWSzYAw9k3uOKy2DOmmaHatq6usoXQtMbp\nOQWg0wmi5ib9eRhIRK0nAWAaOQVVzOA/WhakAqgZM8/RkFfUeDwAAeSZ4lbsGmHmPpoMf5wZZpFd\nod+uf4eScoh3hAfdWWEyG1Ad0vQbUmbt2C9fH5QVuq4HMKXZvDTA76lpsPdCIgTajjxLZjXb0oQI\nF0Ogr+wmFM6jdGahgcYHepRugkPF9dREcPQYHCNjewzxXEv5408MLoeoDYPuHeijUq5yE4RGmEjU\nMkdwm4LxAmVR4kyAtpaR4lo/TZqmt7UtgS6TsFQDoBa9GgywTpcos8hCZCCZqG4uVgQZvxaknae6\nKILFZOhIhcx6B0mqftckLQURrNkKMFicjiZn5XN9rKzEw4JZ3bGk5TBE1kqXW7QR89xNPLHnAjHs\n0FC+4mlePtn5hcvQhovTYzXV3gS6NdiHxWKbnfZnM6L7b/Y8ZrCtiPnc6Ir3Ln1abKuZ+yns6ZYm\nu5clzxrml7RVG5rs0xTTiJDVwLY+LA4jRufydiDPlD6rhxrrqwaxjOyhNtz+DCg0c7KZrTmaYlQ3\nI/OqfP74fFvf95Akl5EHoQhmZigvl9fr9fL13Utog9/nR9CRtW9EE6sNhd909wfPSHOudtaKvKMQ\nP3D9VuY='
        TRACE('%s', zlib.decompress(data.decode('base64')))
    except Exception:
        unhandled_exc_handler()
