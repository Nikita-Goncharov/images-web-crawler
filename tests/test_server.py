import os
import pytest
import shutil

from server import app, PARSED_IMAGES_DIR, ARCHIVE_PATH
from flask.testing import FlaskClient

@pytest.fixture
def client():
    with app.test_client() as client:
        yield client

def test_images_archive_no_dir(client: FlaskClient):
    """If the images directory does not exist or is empty, return 404."""
    if os.path.exists(PARSED_IMAGES_DIR):
        shutil.rmtree(PARSED_IMAGES_DIR)
    response = client.get("/get_images_archive")
    assert response.status_code == 404
    assert b"No images found" in response.data

def test_images_archive_with_files(client: FlaskClient):
    """If there are images in the directory, a file (zip) is returned."""
    os.makedirs(PARSED_IMAGES_DIR, exist_ok=True)
    # Create a test placeholder file
    with open(os.path.join(PARSED_IMAGES_DIR, "test.jpg"), "wb") as f:
        f.write(b"\x00\x00\x00\x00")

    response = client.get("/get_images_archive")
    # Check that the file is returned with status code 200
    assert response.status_code == 200
    # And that it is most likely a ZIP file
    assert response.headers["Content-Type"] == "application/zip"

    # Check that the archive is deleted from the project
    assert not os.path.exists(PARSED_IMAGES_DIR)
    if os.path.exists(ARCHIVE_PATH):
        os.remove(ARCHIVE_PATH)
