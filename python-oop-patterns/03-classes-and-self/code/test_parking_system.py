"""pytest tests for ParkingSystem."""

from parking_system import ParkingSystem


def test_basic():
    ps = ParkingSystem(1, 1, 0)
    assert ps.addCar(1) is True
    assert ps.addCar(2) is True
    assert ps.addCar(3) is False
    assert ps.addCar(1) is False


def test_independent_instances():
    a = ParkingSystem(1, 0, 0)
    b = ParkingSystem(0, 0, 5)
    assert a.addCar(1) is True
    assert a.addCar(1) is False
    assert b.addCar(3) is True
    assert b.addCar(3) is True
