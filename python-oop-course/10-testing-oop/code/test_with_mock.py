"""Mocking a collaborator with unittest.mock.

We have a Notifier that delegates to some send-like collaborator. The test
checks that the collaborator is called with the right arguments — without
needing the real email/SMS/Push back end.

Run:
    pytest 10-testing-oop/code/test_with_mock.py -v
"""

from unittest.mock import Mock


class Notifier:
    def __init__(self, transport):
        self.transport = transport

    def send(self, to: str, message: str) -> None:
        self.transport.send(to, message)


def test_notifier_calls_transport_with_message():
    transport = Mock()
    n = Notifier(transport)
    n.send("ana", "build is green")
    transport.send.assert_called_once_with("ana", "build is green")


def test_notifier_calls_transport_with_kwargs():
    transport = Mock()
    n = Notifier(transport)
    n.send("ana", "build is green")
    assert transport.send.call_count == 1


def test_transport_that_raises_propagates():
    transport = Mock()
    transport.send.side_effect = RuntimeError("network down")
    n = Notifier(transport)
    try:
        n.send("ana", "hi")
    except RuntimeError as e:
        assert "network down" in str(e)
    else:
        raise AssertionError("expected RuntimeError")
