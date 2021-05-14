from django.core.files.uploadedfile import SimpleUploadedFile


def create_text_file():
    test_file = "testfile.txt"
    with open(test_file, "w") as f:
        f.write("Hello World")
    f = open(test_file, 'r')
    return f


def create_image_file():
    SMALL_GIF = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B'
                 )
    UPLOADED = SimpleUploadedFile(
        name='small.gif',
        content=SMALL_GIF,
        content_type='image/gif'
    )
    return UPLOADED


def create_audio_file():
    testfile_audio = (
        b'MM\x00*\x00\x00\x00\x08\x00\x03\x01\x00\x00\x03\x00\x00\x00\x01\x00\x01'
        b'\x00\x00\x01\x01\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01\x11\x00\x03'
        b'\x00\x00\x00\x01\x00\x00\x00\x00')
    audio_file = SimpleUploadedFile(name='music.mp3',
                                    content=testfile_audio,
                                    content_type='audio/mpeg')
    return audio_file