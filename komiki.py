import os
import sys
import argparse
import rarfile
import threading
import time
import zipfile
from PIL import Image

KOBO_CLARA = (1072, 1448)

#   [Some notes]
# 
#   rarfile lib doesn't recognice .cbr files as .rar files
#   We do a rename from cbr to rar and back on the fly
#   to make it easier for us to work with this files.

def mod_image(file,     options):
    """Kobo clara resolution, black/white and file size"""
    image = Image.open(file)
    final_image = image.resize(KOBO_CLARA)
    if options.bw:
        final_image = final_image.convert('L')
    final_image.save(file, quality=85, optimize=True)


def extract_images(file):
    if file.endswith('.cbz'):
        with zipfile.ZipFile(file, 'r') as zf:
            zf.extractall('tmp_cbz')
        return 'tmp_cbz'
    
    elif file.endswith('.cbr'):
        rar_file = rename_to(file, 'rar')
        os.rename(file, rar_file)
        with rarfile.RarFile(rar_file, 'r') as rf:
            rf.extractall('tmp_cbr')
        return 'tmp_cbr'


def rename_to(file, ext):
    '''Rename extension - Mainly for easy cbr file management'''
    base_name, _ = os.path.splitext(file)
    return base_name + '.' + f'{ext}'


def process_extracted_images(tmp_dir, options):
    for root, dirs, files in os.walk(tmp_dir):
        for file in files:
            if file.lower().endswith(('jpg', 'jpeg', 'png')):
                img_route = os.path.join(root, file)
                mod_image(img_route, options)


def ready_to_compress(file_to_compress, tmp_dir):
    for root, dirs, files in os.walk(tmp_dir):
        for file in files:
            file_to_compress.write(os.path.join(root, file), os.path.relpath(os.path.join(root, file), tmp_dir))


def pack_cbz(file, tmp_dir):
    with zipfile.ZipFile(file, 'w') as new_cbz:
        ready_to_compress(new_cbz, tmp_dir)



def remove_tmp(tmp_dir):
    for root, dirs, files in os.walk(tmp_dir, topdown=False):
        for file in files:
            os.remove(os.path.join(root, file))
        for dir in dirs:
            os.rmdir(os.path.join(root, dir))
        os.rmdir(tmp_dir)     


def loading_bar(stop_event):
 
    chars = ['|', '/', '-', '\\']  # Loading animation characters

    while not stop_event.is_set():
        for char in chars:
            sys.stdout.write(f'\r[] Processing {char}')  # Overwrites line with animation
            sys.stdout.flush()
            time.sleep(0.1)
    print("\n")

def set_args():
    parser = argparse.ArgumentParser(description="Optimize comics for ebook readers (only supports Kobo Clara)")
    parser.add_argument("file_name", type=str, help="Comic file")
    parser.add_argument('-b', '--bw',
                    action='store_true', help="Apply black and white filter")  
    args = parser.parse_args()
    return args


def transform_the_donkey_into_unicorn(komiki, args):
    tmp_dir = extract_images(komiki)
    process_extracted_images(tmp_dir, options=args)
    pack_cbz(komiki, tmp_dir)
    remove_tmp(tmp_dir)
    

def main():

    args = set_args()
    komiki = args.file_name
    
    continue_ = input("This program won't keep a save copy of the file you are about to process. Are you sure you want to continue? (yes/no) ")
    if continue_ != 'yes':
        sys.exit(0)

    stop_event = threading.Event()
    thread_loading = threading.Thread(target=loading_bar, args=(stop_event,))
    thread_loading.start()

    try:
        transform_the_donkey_into_unicorn(komiki, args)
    except Exception as e:
        print(f"\nShit happend!:\n {e}")
    finally:
        stop_event.set()
        thread_loading.join()


if __name__ == '__main__':
    main()
