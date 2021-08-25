from rest_framework.exceptions import ValidationError

VALID_DOC_FILES = ('pdf', 'doc', 'docx', 'txt',
                   'rtf', 'xlsx', 'xls')

VALID_AUDIO_FILES = ('mp3', 'ogg', 'wav', 'flac', 'wma')

VALID_VIDEO_FILES = ('mp4', 'mov', 'wmv', 'flv', 'avi', 'mkv', 'webm')


def check_file_extensions(file_field, instance, validator):
    if (file_field not in instance or
            (str(instance[file_field]).split('.')[-1]) in validator):
        return instance
    raise ValidationError('Unsupported file extension.')
