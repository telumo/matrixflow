import sys
from nose.tools import with_setup, raises, eq_, ok_
from pathlib import Path

sys.path.insert(0, '../..')
import filemanager as fm
fm.data_dir = "./tests/data"


def test_get_data_path():
    file_id = "test_id"
    path = fm.get_data_path(file_id)

    ok_(isinstance(path, Path))
    eq_(path.parent, Path(fm.data_dir))
    eq_(path.name, file_id)

def test_put_data_info():
    new_data = {
        "name":"aaaa",
        "description": "aaaa"
    }
    file_id = "test_id"
    res = fm.put_data_info(new_data, file_id)

    data_path = fm.get_data_path(file_id)
    info_path = data_path / "info" / "info.json"

    expected = {
        'id': file_id,
        'nImages': 0,
        'nLabels': 0,
        'nClasses': 0,
        'statistics': {},
        'name': new_data["name"],
        'description': new_data["description"],
        'update_time': fm.get_update_time(info_path),
        'create_time': fm.get_create_time(data_path)
    }

    eq_(expected, res)


def test_get_data_info_1():
    file_id = "test_id"
    path = fm.get_data_path(file_id)
    res = fm.get_data_info(path)


    new_data = {
        "name":"aaaa",
        "description": "aaaa"
    }
    info_path = path / "info" / "info.json"
    expected = {
        'id': file_id,
        'nImages': 0,
        'nLabels': 0,
        'nClasses': 0,
        'statistics': {},
        'name': new_data["name"],
        'description': new_data["description"],
        'update_time': fm.get_update_time(info_path),
        'create_time': fm.get_create_time(path)
    }

    eq_(res, expected)


def test_get_data_info_2():
    file_id = "test001"
    path = fm.get_data_path(file_id)
    res = fm.get_data_info(path)

    expected = {
        'id': 'test001',
        'nImages': 4,
        'nLabels': 4,
        'nClasses': 3,
        'statistics': {'nameA': 2, 'nameB': 1, 'nameC': 1},
        'name': 'fashion MNIST',
        'description': 'fashion MNIST',
        'update_time': '2018-08-10 16:52:25',
        'create_time': '2018-08-10 15:45:32'
    }
    eq_(res, expected)


def test_get_data_info_3():
    file_id = "not_exist_id"
    path = fm.get_data_path(file_id)
    res = fm.get_data_info(path)
    eq_(res, {})


def test_get_data_info_4():
    file_id = "no_info"
    path = fm.get_data_path(file_id)
    res = fm.get_data_info(path)
    expected = {
        'id': 'no_info',
        'nImages': 4,
        'nLabels': 4,
        'nClasses': 0,
        'statistics': {},
        'name': '',
        'description': '',
        'update_time': '2018-08-11 23:32:41',
        'create_time': '2018-08-11 23:32:58'
    }
    eq_(res, expected)


def test_update_data_info():
    file_id = "test_id"
    update_data = {
        "name": "bbbb",
        "description": "bbbb"
    }
    res = fm.update_data_info(update_data, file_id)

    data_path = fm.get_data_path(file_id)
    info_path = data_path / "info" / "info.json"
    expected = {
        'id': file_id,
        'nImages': 0,
        'nLabels': 0,
        'nClasses': 0,
        'statistics': {},
        'name': update_data["name"],
        'description': update_data["description"],
        'update_time': fm.get_update_time(info_path),
        'create_time': fm.get_create_time(data_path)
    }

    eq_(res, expected)

def test_delete_data():
    file_id = "test_id"
    fm.delete_data(file_id)

    path = fm.get_data_path(file_id)
    res = fm.get_data_info(path)
    eq_(res, {})


def test_get_data_statistics():
    file_id = "test_id"
    res = fm.get_data_statistics(file_id)
    eq_(res, {})

def test_get_data_statistics():
    file_id = "test001"
    res = fm.get_data_statistics(file_id)
    expected = {
        'n_classes': 3,
        'statistics': {' nameA': 2, ' nameB': 1, ' nameC': 1}}
    eq_(res, expected)

def test_get_data_statistics():
    file_id = "not_exist_id"
    res = fm.get_data_statistics(file_id)
    eq_(res, {})


def test_get_data_1():
    file_id = "test001"
    offset = 0
    limit = 4
    res = fm.get_data(file_id, offset, limit)
    expected = {
        'status': 'success',
        'data_type': 'list',
        'total': 4,
        'list': [
            {
                'name': 'A2.jpg',
                'body': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAAcABwBAREA/8QAHwAAAQUBAQEB\nAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh\nByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ\nWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG\nx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APn+iiituw8LandzH7Rb\nT2VqiebLczwPtRMgA4AyxJKgAdSR0HNdBbeDvD+qyLa6fq99bXbDCLqFoUEjemRwOfcn0zXO654U\n1vw7qL2OpadPFKOVbyyVkH95TjkVmNa3CEboJRnnlDV+DxPrtqEEGsX0YT7m2dht+nNXP+E78V7S\nreIdRYHqHnLZ6+v1pU8eeKkTYuuXYXqV3cH8Pwqpc+KNcvJFe41S5dlXaDvxx17fWsiiiiv/2Q==\n',
                'label': ' nameA\n'
            },
            {
                'name': 'B.jpg',
                'body': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAAcABwBAREA/8QAHwAAAQUBAQEB\nAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh\nByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ\nWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG\nx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APBrOyudQuVtrSF5pm6K\no/M+w96208E6yxx5UYP+/u/UZFRXPg/W7ZGf7GZVUZPlMGIH+71/SsLFeyaVounaTp1jLp9uxTUL\nRJvtcjczABQwx/ABJv474WtHHHtT4mIkHqpyD3U+o965HxXoegS6qjM7afIYyzpDENshaR239f8A\na244xtwOBTPAWtafBpd3Hq1zax4ZRFkv5zYBHGMjGCByOcDpiuse+0cqGj1OEKSATKyoFz6knGKz\nrrxNoenn97qdvIw5222ZSfoQNv5mvM/Eetvr2sy3uwxx4CRpnlVHTPv1P41k0UUV/9k=\n',
                'label': ' nameB\n'
            },
            {'name':
                'C.jpg',
                'body': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAAcABwBAREA/8QAHwAAAQUBAQEB\nAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh\nByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ\nWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG\nx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APEtF09L+eTzT8iKMLnG\n5icAfzrqtG0o+cSJvDdrGrMvl6xKAkrADOAMsMbhgkrnkDOCBjeJbe7g1eQalHZs84DwS2QXyGiH\nyqYinGwbcevHPOa5up7a8ubNibeZo8srEA8EqcjI74Neq6ZB4cvtSA1rUbO1lS3cNb3alEuFcsRI\nJAcBhnG0gcAEZ7cV4v1KCbUre2srq3urWztEto3hhZEHHO3eSx5/i79RXMUV1niNN94x9LO2Y49x\nn+tc/qMBhmTPeKJvzQVTorsdUfzprxmVRjT7bAGeyrWV4kAFxbYGP9Eg/wDQKw6//9k=\n',
                'label': ' nameC\n'
            },
            {
                'name': 'A.jpg',
                'body': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0a\nHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/wAALCAAcABwBAREA/8QAHwAAAQUBAQEB\nAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1Fh\nByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZ\nWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXG\nx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/9oACAEBAAA/APn+iiituw8LandzH7Rb\nT2VqiebLczwPtRMgA4AyxJKgAdSR0HNdBbeDvD+qyLa6fq99bXbDCLqFoUEjemRwOfcn0zXO654U\n1vw7qL2OpadPFKOVbyyVkH95TjkVmNa3CEboJRnnlDV+DxPrtqEEGsX0YT7m2dht+nNXP+E78V7S\nreIdRYHqHnLZ6+v1pU8eeKkTYuuXYXqV3cH8Pwqpc+KNcvJFe41S5dlXaDvxx17fWsiiiiv/2Q==\n',
                'label': ' nameA\n'
            }
        ]
    }
    eq_(res, expected)

def test_get_data_2():
    """
        error
        set not-exist id
    """
    file_id = "not_exist_id"
    offset = 0
    limit = 4
    res = fm.get_data(file_id, offset, limit)
    expected = {
        "status": "error"
    }
    eq_(res, expected)


def test_get_data_3():
    """
        error
        limit - offset > # of images
    """
    file_id = "test001"
    offset = 0
    limit = 100000
    res = fm.get_data(file_id, offset, limit)
    expected = {
        "status": "error"
    }
    eq_(res, expected)


def test_get_data_4():
    """
       error
        offset > # of images
    """
    file_id = "test001"
    offset = 100000
    limit = 100000
    res = fm.get_data(file_id, offset, limit)
    expected = {
        "status": "error"
    }
    eq_(res, expected)


def test_get_data_list():
    res = fm.get_data_list()
    expected = {
        'status': 'success',
        'data_type': 'list',
        'total': 2,
        'list': [
            {
                'id': 'test001',
                'nImages': 4,
                'nLabels': 4,
                'nClasses': 3,
                'statistics': {'nameA': 2, 'nameB': 1, 'nameC': 1},
                'name': 'fashion MNIST',
                'description': 'fashion MNIST',
                'update_time': '2018-08-10 16:52:25',
                'create_time': '2018-08-10 15:45:32'
            },
            {
                'id': 'no_info',
                'nImages': 4,
                'nLabels': 4,
                'nClasses': 0,
                'statistics': {},
                'name': '',
                'description': '',
                'update_time': '2018-08-11 23:32:41',
                'create_time': '2018-08-11 23:32:58'
            }
        ]
    }
    eq_(res, expected)

def test_get_images():
    file_id = "test001"
    path = fm.get_data_path(file_id)
    images_path = path / "images"
    res = fm.get_images(images_path)
    eq_(len(res), 4)
