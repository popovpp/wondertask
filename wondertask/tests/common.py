from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile


def create_text_file(filename):
    pdf = BytesIO(
        b'%PDF-1.0\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj 2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1'
        b'>>endobj 3 0 obj<</Type/Page/MediaBox[0 0 3 3]>>endobj\nxref\n0 4\n0000000000 65535 f\n000000'
        b'0010 00000 n\n0000000053 00000 n\n0000000102 00000 n\ntrailer<</Size 4/Root 1 0 R>>\nstartxre'
        b'f\n149\n%EOF\n')
    file_name = f'{filename}.pdf'
    uploaded = SimpleUploadedFile(
        file_name,
        pdf.read(),
        content_type='application/pdf')
    return uploaded


def create_image_file(filename):
    small_gif = (b'\x47\x49\x46\x38\x39\x61\x02\x00'
                 b'\x01\x00\x80\x00\x00\x00\x00\x00'
                 b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
                 b'\x00\x00\x00\x2C\x00\x00\x00\x00'
                 b'\x02\x00\x01\x00\x00\x02\x02\x0C'
                 b'\x0A\x00\x3B')
    file_name = f'{filename}.gif'
    uploaded = SimpleUploadedFile(
        name=file_name,
        content=small_gif,
        content_type='image/gif'
    )
    return uploaded


def create_audio_file(filename):
    audio = (
        b'MM\x00*\x00\x00\x00\x08\x00\x03\x01\x00\x00\x03\x00\x00\x00\x01\x00\x01'
        b'\x00\x00\x01\x01\x00\x03\x00\x00\x00\x01\x00\x01\x00\x00\x01\x11\x00\x03'
        b'\x00\x00\x00\x01\x00\x00\x00\x00')
    file_name = f'{filename}.mp3'
    uploaded = SimpleUploadedFile(
        name=file_name,
        content=audio,
        content_type='audio/mpeg'
    )
    return uploaded
