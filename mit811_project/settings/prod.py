from .base import *

DEBUG = False
ALLOWED_HOSTS = ["backend.bookhive.us", "www.backend.bookhive.us"]

# this is the path to the static folder where css, js and images are stored
STATIC_DIR = BASE_DIR / '/home/speebndt/bookhive_backend/static/'
# path to the media folder 
MEDIA_ROOT = BASE_DIR / '/home/speebndt/backend.bookhive.us/media/'

STATIC_URL = 'static/'
STATIC_ROOT = '/home/speebndt/backend.bookhive.us/static/'
MEDIA_URL = 'https://backend.bookhive.us/media/'

STATICFILES_DIRS = [
    STATIC_DIR,
]

MEDIA_BASE_URL = 'https://backend.bookhive.us/'