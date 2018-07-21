# Work in progress

import os
import vimeo

# Directories for videos and SCORM template
PATH_VIDEO_FOLDR = os.getcwd() # default to current directory
SCORM_TEMPLATE = '/path/to/SCORM' # default



def connect_to_vimeo():
    v = vimeo.VimeoClient(
        token=YOUR_ACCESS_TOKEN,
        key=YOUR_CLIENT_ID,
        secret=YOUR_CLIENT_SECRET
    )

    # Make the request to the server for the "/me" endpoint.
    about_me = v.get('/me')

    # Make sure we got back a successful response.
    assert about_me.status_code == 200

    # Load the body's JSON data.
    print about_me.json()

    return v

def upload_popup_mode(key_auth):
    pass


def upload_normal_mode(key_auth):
    pass


def generate_scorm(popup_id, completed_id, to_folder):
    pass

def main(out_foldr = "/path/to/output"):
    for filename in os.listdir(PATH_VIDEO_FOLDR):
        print('Processing file {}'.format(filename))

        key_auth = connect_to_vimeo()

        popup_id = upload_popup_mode(key_auth)
        completed_id = upload_normal_mode(key_auth)

        generate_scorm(popup_id, completed_id, out_folder)

if __name__ == '__main__':

    main()