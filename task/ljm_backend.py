"""실제 LabJack과 no-op MOCK backend를 전환하는 공유 LJM proxy."""

try:
    from labjack import ljm as _real_ljm
    REAL_LJM_AVAILABLE = True
except Exception:
    _real_ljm = None
    REAL_LJM_AVAILABLE = False


class _MockLJM:
    """과제에서 사용하는 LJM 호출만 제공하는 no-op backend."""

    def openS(self, device_type, connection_type, identifier):
        return 0

    def close(self, handle):
        pass

    def eWriteName(self, handle, name, value):
        pass

    def eWriteNames(self, handle, num_frames, names, values):
        pass


class _LJMProxy:
    """모든 caller가 공유하는 교체 가능 LJM 진입점."""

    def __init__(self):
        self._backend = _real_ljm
        self.is_mock = False

    def use_mock(self) -> None:
        self._backend = _MockLJM()
        self.is_mock = True

    def __getattr__(self, name):
        backend = self.__dict__.get("_backend")
        if backend is None:
            raise RuntimeError(
                "labjack-ljm 패키지가 설치되어 있지 않습니다. "
                "setup_venv.py 로 설치하거나 MOCK 모드로 진행하세요."
            )
        return getattr(backend, name)


ljm = _LJMProxy()
