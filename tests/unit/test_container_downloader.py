from pathlib import Path

from shrinkwrap import ContainerDownloader

import mock
import pytest


@pytest.fixture()
def mock_requests():
    with mock.patch("shrinkwrap.requests.get") as mr:
        yield mr


@pytest.fixture()
def mock_docker_cmd():
    with mock.patch("shrinkwrap.Popen"):
        with mock.patch("shrinkwrap.check_call") as ck:
            yield ck


def test_container_downloader_no_matches(tmp_dir, mock_requests):
    downloader = ContainerDownloader(tmp_dir)
    assert downloader.path == Path(tmp_dir) / "containers"
    mock_requests.return_value.json.return_value = []  # mock github response for empty dir listing
    channel = "latest/stable"
    assert downloader.revisions(channel) == []
    with pytest.raises(AssertionError) as ie:
        assert downloader.download(channel)
    assert str(ie.value) == "No revisions matched the channel latest/stable"


def test_container_downloader(tmp_dir, mock_requests, mock_docker_cmd):
    downloader = ContainerDownloader(tmp_dir)
    assert downloader.path == Path(tmp_dir) / "containers"
    mock_requests.return_value.json.return_value = [
        {
            "name": "README.md",
            "download_url": "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/README.md",  # noqa: 501
        },
        {
            "name": "v1.18.17.txt",
            "download_url": "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/v1.18.17.txt",  # noqa: 501
        },
        {
            "name": "v1.18.18.txt",
            "download_url": "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/v1.18.18.txt",  # noqa: 501
        },
        {
            "name": "v1.19.10.txt",
            "download_url": "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/v1.19.10.txt",  # noqa: 501
        },
    ]
    channel = "1.18/stable"
    assert downloader.revisions(channel) == [
        (
            "1.18.17",
            "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/v1.18.17.txt",
        ),
        (
            "1.18.18",
            "https://raw.githubusercontent.com/charmed-kubernetes/bundle/master/container-images/v1.18.18.txt",
        ),
    ]
    with (Path(__file__).parent / "test_container_listing.txt").open() as fp:
        mock_requests.return_value.text = fp.read()
    downloader.download(channel)
    mock_docker_cmd.assert_has_calls(
        [
            mock.call("docker pull -q rocks.canonical.com/cdk/cdkbot/microbot-amd64:latest".split()),
            mock.call("docker pull -q rocks.canonical.com/cdk/k8s-dns-sidecar:1.14.13".split()),
            mock.call(
                "docker pull -q rocks.canonical.com/cdk/kubernetes-ingress-controller/nginx-ingress-controller-amd64:0.30.0".split()  # noqa: 501
            ),
            mock.call("docker rmi rocks.canonical.com/cdk/cdkbot/microbot-amd64:latest".split()),
            mock.call("docker rmi rocks.canonical.com/cdk/k8s-dns-sidecar:1.14.13".split()),
            mock.call(
                "docker rmi rocks.canonical.com/cdk/kubernetes-ingress-controller/nginx-ingress-controller-amd64:0.30.0".split()  # noqa: 501
            ),
        ]
    )
