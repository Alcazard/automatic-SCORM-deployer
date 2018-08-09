import os
import vimeo
import json
from urllib.parse import urlparse
import shutil

ALLOWED_EXTENSION = ('.mp4', '.avi')


def connect_to_vimeo(config_file):
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

    try:
        uri = key_auth.upload(path_video, data={
            'name': str(video_title),
            'description': "This video was uploaded with Automatic SCORM Deployer"
        })

        video_metadata = key_auth.get(uri + '?fields=link').json()
        print('"{}" has been uploaded to {}'.format(video_name, video_metadata['link']))

        if video_title_suffix is '_completato':
            print('Changing preset for video...')
            key_auth.put(uri + '/presets/120447750')
        return video_metadata

    except vimeo.exceptions.VideoUploadFailure as e:
        print('Error uploading {}, server said: {}'.format(video_name, e.message))


def get_vimeo_id(metadata):
    return urlparse(metadata['link']).path.replace("/", "")


def generate_scorm(popup_id, completed_id, out_foldr, compress_type='zip'):
    config_file = os.path.join(out_foldr, 'config.json')

    with open(config_file, 'r') as scorm_json_file:
        data = json.load(scorm_json_file)

        if 'VIDEO_ID' not in data or 'VIDEO_ID_COMPLETED' not in data:
            raise ValueError('Invalid Scorm Template!. Aborting')

        data["VIDEO_ID"] = popup_id
        data["VIDEO_ID_COMPLETED"] = completed_id

    with open(config_file, 'w') as scorm_json_file:
        scorm_json_file.write(json.dumps(data))

    shutil.make_archive(out_foldr, compress_type, out_foldr)


def main(path_video_folder='/path/to/video/directory',
         path_scorm_template='/path/to/SCORM/template',
         vimeo_config_file=os.path.join(os.path.dirname(os.path.realpath(__file__)), 'config.json')):

    print("Connecting to Vimeo....")
    key_auth = connect_to_vimeo(vimeo_config_file)

    for filename in [f for f in os.listdir(path_video_folder) if f.endswith(ALLOWED_EXTENSION)]:
        print('Processing file {}'.format(filename))
        abs_video_path = os.path.abspath(os.path.join(path_video_folder, filename))

        popup_video_metadata = upload_video(key_auth, str(abs_video_path))
        popup_id = get_vimeo_id(popup_video_metadata)

        completed_video_metadata = upload_video(key_auth, str(abs_video_path), '_completato')
        completed_id = get_vimeo_id(completed_video_metadata)

        print('Upload for {} completed: popup id: {}, completed id: {}'.format(filename, popup_id, completed_id))
        try:
            file_name = os.path.basename(filename)
            file_title = os.path.splitext(file_name)[0]

            shutil.copytree(path_scorm_template, file_title)
            generate_scorm(popup_id, completed_id, shutil.move(file_title, path_video_folder))

        except FileExistsError:
            print("File {} Already Exists!".format(filename))

if __name__ == '__main__':
    main()
