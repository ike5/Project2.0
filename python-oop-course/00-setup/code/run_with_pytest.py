"""A one-function pytest that exercises the Dog class.

Run:
    pytest 00-setup/code/run_with_pytest.py -q
    pytest 00-setup/code/run_with_pytest.py -v
"""

from hello_oop import Dog


def test_dog_bark() -> None:
    rex = Dog("Rex")
    assert rex.bark() == "Rex says woof!"
