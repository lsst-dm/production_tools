
import os
import pytest
from unittest import mock
from unittest.mock import patch

# from lsst.production.tools.images import bp


class MockType:
    storageClass_name = "Plot"

class MockRef:

    def __init__(self, uuid):
        self.uuid = uuid
        self.datasetType = MockType()

class MockButler:

    def get_dataset(self, uuid):
        return MockRef(uuid)

    def getURI(self, ref):
        return f"test_data/{ref.uuid}.png"

@pytest.fixture()
def app():
    with mock.patch.dict(os.environ, {"BUTLER_REPO_NAMES": "testrepo"}, clear=True):
        from lsst.production.tools import create_app
        app = create_app()

        yield app

@pytest.fixture()
def client(app):
    return app.test_client()


@patch("lsst.production.tools.images.get_butler_map", return_value=MockButler())
def test_image_metadata(mock, client):

    # This image has the 'boxes' metadata
    uuid = "04e7c0fb-40e7-4a07-9e2a-cc9987282923"
    response = client.get(f"/plot-navigator/images/uuid/testrepo/{uuid}")

    assert response.status_code == 200
    assert response.headers['Has-Metadata'] == "true"

    response_head = client.head(f"/plot-navigator/images/uuid/testrepo/{uuid}")
    assert response_head.status_code == 200
    assert response_head.headers['Has-Metadata'] == "true"

    response_md = client.get(f"/plot-navigator/images/uuid_md/testrepo/{uuid}")

    assert response_md.status_code == 200
    assert len(response_md.json['boxes']) > 0

