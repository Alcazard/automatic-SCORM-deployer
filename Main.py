# Work in progress

import os
import vimeo
import json
from pathlib import Path
from urllib.parse import urlparse
import shutil

# Directories for videos and SCORM template

PATH_VIDEO_FOLDR = os.getcwd() # default to current directory

SCORM_TEMPLATE = '/path/to/SCORM' # default


def connect_to_vimeo():
    print("Connessione a Vimeo in corso....")

    config_file = os.path.dirname(os.path.realpath(__file__)) + '/config.json'
    config = json.load(open(config_file))

    if 'client_id' not in config or 'client_secret' not in config:
        raise Exception('Non è stato possibile trovare il client_id o il client_secret ' +
                        'nel file `' + config_file + '`. Controllare e riprovare.')
    else:
        print(config)

    # Instantiate the library with your client id, secret and access token
    v = vimeo.VimeoClient(
        token=config['access_token'],
        key=config['client_id'],
        secret=config['client_secret']
    )

    # Make the request to the server for the "/me" endpoint.
    about_me = v.get('/me')

    # Make sure we got back a successful response.
    assert (about_me.status_code == 200)

    # Load the body's JSON data.
    #print (about_me.json())

    return v


def upload_popup_mode(key_auth, path_video):

    # Extracting video name for upload

    video_name = os.path.basename(path_video)

    print ('Uploading: %s' % (video_name))

    # Extracting title

    video_title = os.path.splitext(video_name)[0]


    try:
        # Upload the file and include the video title and description.
        uri = key_auth.upload(path_video, data={
            'name': '%s' % video_title,
            'description': "Questo video è stato caricato con Automatic SCORM Deployer"
        })

        # Get the metadata response from the upload and log out the Vimeo.com url
        video_data = key_auth.get(uri + '?fields=link').json()
        print ('"%s" has been uploaded to %s' % (video_name, video_data['link']))



    except vimeo.exceptions.VideoUploadFailure as e:
        # We may have had an error. We can't resolve it here necessarily, so
        # report it to the user.
        print ('Error uploading %s' % (video_name))
        print ('Server reported: %s' % (e.message))

    print(video_data)
    print(video_data['link'])
    # return the parsed url

    parsed = urlparse(video_data['link'])

    return parsed.path.replace("/", "")


def upload_completed_mode(key_auth, path_video):

    # Extracting video name for upload

    video_name = os.path.basename(path_video)

    print('Uploading: %s' % (video_name))

    # Extracting title and adding ending

    video_title = os.path.splitext(video_name)[0] + "_completato"

    try:
        # Upload the file and include the video title and description.
        uri = key_auth.upload(path_video, data={
            'name': '%s' % video_title,
            'description': "Questo video è stato caricato con Automatic SCORM Deployer"
        })

        # Get the metadata response from the upload and log out the Vimeo.com url
        video_data = key_auth.get(uri + '?fields=link').json()
        print('"%s" has been uploaded to %s' % (video_name, video_data['link']))

        # Change the preset of the video
        #key_auth.patch(uri, data={'name': 'Video title', 'description': '...'})

    except vimeo.exceptions.VideoUploadFailure as e:
        # We may have had an error. We can't resolve it here necessarily, so
        # report it to the user.
        print('Error uploading %s' % (video_name))
        print('Server reported: %s' % (e.message))

    # return the parsed url

    parsed = urlparse(video_data['link'])

    return parsed.path.replace("/", "")



def generate_scorm(popup_id, completed_id, out_foldr):

    # Search for config.json
    json_file = []

    for folder, subs, files in os.walk(out_foldr):
        for filename in files:
            if filename.endswith('.json'):
                json_file.append(os.path.abspath(os.path.join(folder, filename)))

    config_file = ''.join(json_file)
    with open(config_file, 'r') as JSON:
        data = json.load(JSON)

        if 'VIDEO_ID' not in data or 'VIDEO_ID_COMPLETED' not in data:
            raise Exception('Il Template SCORM nno è valido. Controllare e riprovare.')
        else:
            print(data)

        data["VIDEO_ID"]= popup_id
        data["VIDEO_ID_COMPLETED"] = completed_id
        print(data)

    with open(config_file, 'w') as JSON:
        JSON.write(json.dumps(data))

    # Archive the SCORM # Todo

    shutil.make_archive(out_foldr, 'zip', os.path.dirname(os.path.realpath(out_foldr)))

    return(0)

def main():
    out_foldr = PATH_VIDEO_FOLDR # default

    key_auth = connect_to_vimeo()

    file_paths = []

    for folder, subs, files in os.walk(PATH_VIDEO_FOLDR):
        for filename in files:
            file_paths.append(os.path.abspath(os.path.join(folder, filename)))

    for filename in file_paths:
        if filename.endswith(".mp4") or filename.endswith(".avi"):
            print('Processo file {}'.format(filename))

            # We need the absolute path for the video

            video_path = Path(filename).resolve()
            print(video_path)

            popup_id = upload_popup_mode(key_auth, str(video_path))
            completed_id = upload_completed_mode(key_auth, str(video_path))

            try:
                # Extracting file name

                file_name = os.path.basename(filename)
                print(file_name)
                # Extracting file title

                file_title = os.path.splitext(file_name)[0]
                print(file_title)
                # We copy the SCORM template in the video directory

                shutil.copytree(SCORM_TEMPLATE, file_title)

                generate_scorm(popup_id,completed_id,shutil.move(file_title, out_foldr))

            except FileExistsError:
                print("Il File esiste già!")



        else :
             print("Trovato file non processabile {}" .format(filename))



if __name__ == '__main__':

    main()