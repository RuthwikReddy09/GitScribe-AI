from app.services.filters import should_document


def test_should_document_python():
    assert should_document('app/main.py')


def test_should_skip_lockfile():
    assert not should_document('package-lock.json')


def test_should_skip_node_modules():
    assert not should_document('node_modules/pkg/index.js')
