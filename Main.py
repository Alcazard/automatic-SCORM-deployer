import os
import vimeo
import json
from pathlib import Path
from urllib.parse import urlparse
import shutil

ALLOWED_EXTENSION = ['.mp4', '.avi']


def connect_to_vimeo():
    print("Connecting to Vimeo....")

    config_file = os.path.dirname(os.path.realpath(__file__)) + '/config.json'
    config = json.load(open(config_file))

    if 'client_id' not in config or 'client_secret' not in config:
        raise ConnectionError('No client_id or client_secret found in {}'.format(config_file))

    vimeo_client = vimeo.VimeoClient(
        token=config['access_token'],
        key=config['client_id'],
        secret=config['client_secret']
    )

    about_me = vimeo_client.get('/me')  # Make the request to the server for the "/me" endpoint.

    if about_me.status_code != 200:
        raise ValueError('Cannot get /me, status is {}'.format(about_me.status_code))

    return vimeo_client


def upload_video(key_auth, path_video, video_title_suffix=''):
    video_name = os.path.basename(path_video)
    video_title = os.path.splitext(video_name)[0] + video_title_suffix
    print('Uploading video "{}", title is {}'.format(video_name, video_title))

    # Change the preset of the video (take it as a parameter!
    # key_auth.patch(uri, data={'name': 'Video title', 'description': '...'})

    try:
        uri = key_auth.upload(path_video, data={
            'name': str(video_title),
            'description': "Questo video è stato caricato con Automatic SCORM Deployer"
        })

        video_metadata = key_auth.get(uri + '?fields=link').json()
        print('"{}" has been uploaded to {}'.format(video_name, video_metadata['link']))

        return video_metadata

    except vimeo.exceptions.VideoUploadFailure as e:
        print('Error uploading {}, server said: {}'.format(video_name, e.message))


def get_vimeo_id(metadata):
    return urlparse(metadata['link']).path.replace("/", "")


def generate_scorm(popup_id, completed_id, out_foldr):
    json_file = []      #FIXME: Umh...

    for folder, subs, files in os.walk(out_foldr):
        for filename in files:
            if filename.endswith('.json'):
                json_file.append(os.path.abspath(os.path.join(folder, filename)))

    config_file = ''.join(json_file)

    with open(config_file, 'r') as scorm_json_file:
        data = json.load(scorm_json_file)

        if 'VIDEO_ID' not in data or 'VIDEO_ID_COMPLETED' not in data:
            raise Exception('Invalid Scorm Template!. Aborting')

        data["VIDEO_ID"] = popup_id
        data["VIDEO_ID_COMPLETED"] = completed_id

        print('Generating SCORM with following data: {}'.format(data))

    # FIXME: I think you could open and write the file at the same time!
    with open(config_file, 'w') as scorm_json_file:
        scorm_json_file.write(json.dumps(data))

    shutil.make_archive(out_foldr, 'zip', os.path.dirname(os.path.realpath(out_foldr)))


def main(path_video_folder=os.getcwd(), path_scorm_template='/path/to/SCORM'):
    out_folder = path_video_folder
    key_auth = connect_to_vimeo()
    files_path = []

    # FIXME: This should be a list comprehension :) # files = [x for x in os.walk(PATH_VIDEO_FOLDR) if x.endswith( ...]
    for folder, subs, files in os.walk(path_video_folder):
        for filename in files:
            file_extension = os.path.splitext(filename)[1]
            if file_extension in ALLOWED_EXTENSION:
                files_path.append(os.path.abspath(os.path.join(folder, filename)))

    # FIXME: Merge this for with the previous: Do a single for loop! :)
    for filename in files_path:
        print('Processing file {}'.format(filename))
        abs_video_path = Path(filename).resolve()

        popup_video_metadata = upload_video(key_auth, str(abs_video_path))
        popup_id = get_vimeo_id(popup_video_metadata)

        completed_video_metadata = upload_video(key_auth, str(abs_video_path), '_completato')
        completed_id = get_vimeo_id(completed_video_metadata)

        print('Upload process completed: popup id is {} and completed id is {}'.format(popup_id, completed_id))
        try:
            file_name = os.path.basename(filename)
            file_title = os.path.splitext(file_name)[0]

            shutil.copytree(path_scorm_template, file_title)
            generate_scorm(popup_id, completed_id, shutil.move(file_title, out_folder))

        except FileExistsError:
            print("File {} Already Exists!".format(filename))

if __name__ == '__main__':
    main()
    print('Process completed.')
